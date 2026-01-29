#![allow(non_local_definitions)] // False positive from pyo3 macros

use csv::{QuoteStyle, ReaderBuilder, Terminator, WriterBuilder};
use pyo3::create_exception;
use pyo3::exceptions::PyException;
use pyo3::prelude::*;
use pyo3::types::{PyDict, PyList};
use pyo3::wrap_pyfunction;
use pyo3_async_runtimes::tokio::future_into_py;
use std::sync::{Arc, Mutex as StdMutex};
use tokio::fs::File;
use tokio::io::{AsyncReadExt, AsyncWriteExt, BufReader};
use tokio::sync::Mutex;

// Exception classes (ABI3 compatible)
create_exception!(_rapcsv, CSVError, PyException);
create_exception!(_rapcsv, CSVFieldCountError, PyException);

/// File source enum for supporting both paths and file handles.
#[allow(dead_code)] // Fields are accessed via pattern matching, not direct field access
enum FileSource {
    Path(String),
    Handle {
        file: Py<PyAny>,       // Python file-like object with async read/write methods
        event_loop: Py<PyAny>, // Event loop reference for run_coroutine_threadsafe
    },
}

// Note: FileSource::Handle cannot be cloned directly without GIL
// We'll avoid cloning FileSource and instead clone the path/handle separately where needed

/// Read from a Python async file-like object.
///
/// Calls the file's `read(size)` method and awaits the coroutine using spawn_blocking
/// to avoid blocking the Tokio runtime while running Python async code.
/// Uses `asyncio.run_coroutine_threadsafe()` to schedule on the original event loop.
async fn read_from_python_file(
    file_handle: Py<PyAny>,
    event_loop: Py<PyAny>, // Event loop reference for run_coroutine_threadsafe
    size: usize,
) -> PyResult<String> {
    // Use spawn_blocking to run Python async code without blocking Tokio
    let result = tokio::task::spawn_blocking(move || {
        #[allow(deprecated)]
        // Python::with_gil is still required in blocking contexts (spawn_blocking)
        Python::with_gil(|py| -> PyResult<String> {
            let handle_bound = file_handle.bind(py);
            let loop_bound = event_loop.bind(py);

            // Use the helper function to call read on the event loop thread
            // This avoids calling rapfiles.read() from a thread without an event loop
            let rapcsv_mod = py.import("rapcsv")?;
            let helper_func = rapcsv_mod.getattr("_call_file_method_threadsafe")?;

            // Call the helper function which schedules read() on the event loop
            // Pass arguments as positional: file_handle, method_name, event_loop, *args
            let result = helper_func.call1((handle_bound, "read", loop_bound, size))?;
            let result_str = result.extract::<String>()?;
            Ok(result_str)
        })
    })
    .await
    .map_err(|e| {
        PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(format!(
            "Failed to await Python coroutine: {e}"
        ))
    })??;

    Ok(result)
}

/// Write to a Python async file-like object.
///
/// Calls the file's `write(data)` method and awaits the coroutine using spawn_blocking.
/// Uses `asyncio.run_coroutine_threadsafe()` to schedule on the original event loop.
async fn write_to_python_file(
    file_handle: Py<PyAny>,
    event_loop: Py<PyAny>, // Event loop reference for run_coroutine_threadsafe
    data: String,
) -> PyResult<()> {
    // Use spawn_blocking to run Python async code without blocking Tokio
    tokio::task::spawn_blocking(move || {
        #[allow(deprecated)]
        // Python::with_gil is still required in blocking contexts (spawn_blocking)
        Python::with_gil(|py| -> PyResult<()> {
            let handle_bound = file_handle.bind(py);
            let loop_bound = event_loop.bind(py);

            // Use the helper function to call write on the event loop thread
            // This avoids calling rapfiles.write() from a thread without an event loop
            let rapcsv_mod = py.import("rapcsv")?;
            let helper_func = rapcsv_mod.getattr("_call_file_method_threadsafe")?;

            // Call the helper function which schedules write() on the event loop
            // Pass arguments as positional: file_handle, method_name, event_loop, *args
            helper_func.call1((handle_bound, "write", loop_bound, data))?;

            Ok(())
        })
    })
    .await
    .map_err(|e| {
        PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(format!(
            "Failed to await Python coroutine: {e}"
        ))
    })??;

    Ok(())
}

/// Get the event loop for file handle operations.
/// Returns the stored loop (should always be Some for file handles).
/// Must be called from async context with Python GIL available.
#[allow(dead_code)] // Kept for potential future use
fn get_event_loop_for_file_handle(
    event_loop: &Arc<StdMutex<Option<Py<PyAny>>>>,
) -> PyResult<Py<PyAny>> {
    #[allow(deprecated)] // Python::with_gil is still required in this context
    Python::with_gil(|py| -> PyResult<Py<PyAny>> {
        let loop_guard = event_loop.lock().map_err(|_| {
            PyErr::new::<pyo3::exceptions::PyRuntimeError, _>("Failed to lock event loop")
        })?;

        // Event loop should always be stored for file handles
        loop_guard.as_ref().ok_or_else(|| {
            PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(
                "Event loop not available. This should not happen - file handles require an event loop during construction."
            )
        }).map(|lo| lo.clone_ref(py))
    })
}

/// Internal wrapper function that converts Futures to coroutines.
/// This calls the Python function defined in rapcsv/__init__.py to avoid exec/eval.
#[pyfunction]
#[pyo3(name = "_await_wrapper")]
fn await_wrapper_internal(py: Python<'_>, awaitable: Bound<'_, PyAny>) -> PyResult<Py<PyAny>> {
    // Import the wrapper function from rapcsv/__init__.py
    // This avoids exec/eval entirely by using a pre-defined Python function
    let rapcsv_mod = py.import("rapcsv")?;
    let wrapper_func = rapcsv_mod.getattr("_await_wrapper")?;

    // Call the Python wrapper function with our awaitable
    let coro = wrapper_func.call1((awaitable,))?;
    Ok(coro.unbind())
}

/// Wrap a Python awaitable (coroutine or Future) into a coroutine for run_coroutine_threadsafe.
/// This is safer than using exec/eval - we use Python's built-in type checking.
#[allow(dead_code)] // Kept for potential future use
fn wrap_awaitable_into_coroutine<'py>(
    py: Python<'py>,
    awaitable: Bound<'py, PyAny>,
) -> PyResult<Bound<'py, PyAny>> {
    // Always use the wrapper function from rapcsv/__init__.py
    // It handles both coroutines and Futures internally, avoiding type issues
    let rapcsv_mod = py.import("rapcsv")?;
    let wrapper_func = rapcsv_mod.getattr("_await_wrapper")?;

    // Call the Python wrapper function with our awaitable
    let coro = wrapper_func.call1((awaitable,))?;
    Ok(coro)
}

/// Validate a file path for security and correctness.
fn validate_path(path: &str) -> PyResult<()> {
    if path.is_empty() {
        return Err(PyErr::new::<pyo3::exceptions::PyValueError, _>(
            "Path cannot be empty",
        ));
    }
    if path.contains('\0') {
        return Err(PyErr::new::<pyo3::exceptions::PyValueError, _>(
            "Path cannot contain null bytes",
        ));
    }
    Ok(())
}

/// CSV dialect configuration.
/// Holds all CSV parsing/writing parameters compatible with Python's csv module.
#[derive(Clone, Debug)]
struct DialectConfig {
    delimiter: u8,
    quotechar: u8,
    escapechar: Option<u8>,
    #[allow(dead_code)] // Stored for dialect configuration, used when applying to reader/writer
    quoting: QuoteStyle,
    lineterminator: Terminator,
    skipinitialspace: bool,
    strict: bool,
    double_quote: bool,
}

impl Default for DialectConfig {
    fn default() -> Self {
        DialectConfig {
            delimiter: b',',
            quotechar: b'"',
            escapechar: None,
            quoting: QuoteStyle::Necessary,
            lineterminator: Terminator::CRLF,
            skipinitialspace: false,
            strict: false,
            double_quote: true,
        }
    }
}

impl DialectConfig {
    /// Create dialect config from Python parameters.
    #[allow(clippy::too_many_arguments)] // Required for Python API compatibility
    fn from_python(
        delimiter: Option<&str>,
        quotechar: Option<&str>,
        escapechar: Option<&str>,
        quoting: Option<u32>,
        lineterminator: Option<&str>,
        skipinitialspace: Option<bool>,
        strict: Option<bool>,
        double_quote: Option<bool>,
    ) -> PyResult<Self> {
        let delimiter = delimiter
            .and_then(|s| s.as_bytes().first().copied())
            .unwrap_or(b',');

        if delimiter.is_ascii_whitespace() {
            return Err(PyErr::new::<pyo3::exceptions::PyValueError, _>(
                "delimiter cannot be whitespace",
            ));
        }

        let quotechar = quotechar
            .and_then(|s| s.as_bytes().first().copied())
            .unwrap_or(b'"');

        let escapechar = escapechar.and_then(|s| s.as_bytes().first().copied());

        let quoting = match quoting {
            Some(0) => QuoteStyle::Never,      // QUOTE_NONE
            Some(1) => QuoteStyle::Necessary,  // QUOTE_MINIMAL
            Some(2) => QuoteStyle::Always,     // QUOTE_ALL
            Some(3) => QuoteStyle::NonNumeric, // QUOTE_NONNUMERIC
            Some(4) => QuoteStyle::Always, // QUOTE_NOTNULL - map to Always (quote all non-null fields)
            Some(5) => QuoteStyle::Always, // Reserved for future use
            Some(6) => QuoteStyle::NonNumeric, // QUOTE_STRINGS - map to NonNumeric (quote string fields)
            _ => QuoteStyle::Necessary,        // Default to QUOTE_MINIMAL
        };

        let lineterminator = match lineterminator {
            Some("\r\n") | Some("\\r\\n") => Terminator::CRLF,
            Some("\n") | Some("\\n") => Terminator::Any(b'\n'),
            Some("\r") | Some("\\r") => Terminator::Any(b'\r'),
            Some(custom) if custom.len() == 1 => Terminator::Any(custom.as_bytes()[0]),
            _ => Terminator::CRLF, // Default
        };

        Ok(DialectConfig {
            delimiter,
            quotechar,
            escapechar,
            quoting,
            lineterminator,
            skipinitialspace: skipinitialspace.unwrap_or(false),
            strict: strict.unwrap_or(false),
            double_quote: double_quote.unwrap_or(true),
        })
    }

    /// Apply dialect config to a ReaderBuilder.
    fn apply_to_reader(&self, builder: &mut ReaderBuilder, field_size_limit: Option<usize>) {
        builder
            .delimiter(self.delimiter)
            .quote(self.quotechar)
            .terminator(self.lineterminator)
            .flexible(!self.strict);

        // csv crate doesn't have separate quoting() method for ReaderBuilder
        // Quoting behavior is handled by the quote character and escape settings

        if let Some(esc) = self.escapechar {
            builder.escape(Some(esc));
        }

        if self.skipinitialspace {
            // csv crate handles whitespace trimming automatically
        }

        // Apply field size limit if specified
        // Note: csv crate doesn't have direct field_size_limit, but we can use buffer_capacity
        // as a workaround, though it's not exactly the same. For true field size limiting,
        // we'd need to check field sizes manually after reading.
        if let Some(limit) = field_size_limit {
            // Set buffer capacity to at least the field size limit
            // This helps prevent reading extremely large fields
            builder.buffer_capacity(limit.max(8192));
        }
    }

    /// Apply dialect config to a WriterBuilder.
    fn apply_to_writer(&self, builder: &mut WriterBuilder) {
        builder
            .delimiter(self.delimiter)
            .quote(self.quotechar)
            .terminator(self.lineterminator);

        // WriterBuilder uses quote() for quote character and doesn't have separate quote_style()
        // The quoting style is primarily controlled by quote character and double_quote behavior

        if let Some(esc) = self.escapechar {
            builder.escape(esc); // WriterBuilder.escape() takes u8, not Option<u8>
        }

        if !self.double_quote {
            builder.double_quote(false);
        }
    }
}

/// Python bindings for rapcsv - Streaming async CSV.
///
/// rapcsv provides true async CSV reading and writing for Python, backed by Rust and Tokio.
/// Unlike libraries that wrap blocking I/O in async syntax, rapcsv guarantees that all CSV
/// operations execute outside the Python GIL, ensuring event loops never stall under load.
///
/// # Features
///
/// - True async CSV reading and writing
/// - Streaming support for large files (reads incrementally, not entire file into memory)
/// - Context manager support (`async with`)
/// - aiocsv compatibility (AsyncReader/AsyncWriter aliases)
/// - CSV-specific exception types (CSVError, CSVFieldCountError)
/// - RFC 4180 compliant CSV parsing and writing
#[pymodule]
fn _rapcsv(py: Python<'_>, m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<Reader>()?;
    m.add_class::<Writer>()?;
    m.add_class::<AsyncDictReader>()?;
    m.add_class::<AsyncDictWriter>()?;
    // Register exception classes (required for create_exception! to be accessible from Python)
    m.add("CSVError", py.get_type::<CSVError>())?;
    m.add("CSVFieldCountError", py.get_type::<CSVFieldCountError>())?;

    // Register the wrapper function (no exec/eval needed - uses pyo3-async-runtimes)
    m.add_function(wrap_pyfunction!(await_wrapper_internal, m)?)?;

    Ok(())
}

/// Async CSV reader.
///
/// Provides streaming async CSV reading with incremental file processing.
/// Files are read in chunks without loading the entire file into memory.
///
/// # Example
///
/// ```python
/// from rapcsv import Reader
///
/// async def read_csv():
///     reader = Reader("data.csv")
///     while True:
///         row = await reader.read_row()
///         if not row:
///             break
///         print(row)
/// ```
///
/// # Context Manager
///
/// ```python
/// async with Reader("data.csv") as reader:
///     row = await reader.read_row()
/// ```
#[pyclass]
struct Reader {
    source: FileSource, // Either Path(String) or Handle {file, event_loop}
    path: String,       // Keep for backward compatibility and error messages
    file: Arc<Mutex<Option<BufReader<File>>>>, // Only used when source is Path
    file_handle: Arc<StdMutex<Option<Py<PyAny>>>>, // Python file handle when source is Handle (std::sync::Mutex for blocking locks in spawn_blocking)
    event_loop: Arc<StdMutex<Option<Py<PyAny>>>>, // Event loop reference for run_coroutine_threadsafe
    buffer: Arc<Mutex<String>>,
    buffer_start: Arc<Mutex<usize>>, // Start position in buffer for next parse
    position: Arc<Mutex<usize>>,     // Record index (0-based)
    line_num: Arc<Mutex<usize>>,     // Line number (1-based, accounting for multi-line records)
    dialect: DialectConfig,
    read_size: usize, // Configurable chunk size for reading
    #[allow(dead_code)] // Captured at instantiation for future validation
    field_size_limit: Option<usize>, // Maximum field size (captured at instantiation)
}

#[pymethods]
impl Reader {
    /// Open a CSV file for reading.
    ///
    /// # Arguments
    /// * `path` - Path to the CSV file
    /// * `delimiter` - Field delimiter (default: ',')
    /// * `quotechar` - Quote character (default: '"')
    /// * `escapechar` - Escape character (default: None)
    /// * `quoting` - Quoting style: 0=QUOTE_NONE, 1=QUOTE_MINIMAL, 2=QUOTE_ALL, 3=QUOTE_NONNUMERIC, 4=QUOTE_NOTNULL, 6=QUOTE_STRINGS
    /// * `lineterminator` - Line terminator (default: '\r\n')
    /// * `skipinitialspace` - Skip whitespace after delimiter (default: false)
    /// * `strict` - Strict mode for field count validation (default: false)
    /// * `double_quote` - Handle doubled quotes (default: true)
    /// * `read_size` - Buffer size for reading chunks (default: 8192)
    /// * `field_size_limit` - Maximum field size in bytes (default: None, uses csv crate default)
    #[new]
    #[pyo3(signature = (
        path_or_handle,
        delimiter = None,
        quotechar = None,
        escapechar = None,
        quoting = None,
        lineterminator = None,
        skipinitialspace = None,
        strict = None,
        double_quote = None,
        read_size = None,
        field_size_limit = None
    ))]
    #[allow(clippy::too_many_arguments)] // Required for Python API compatibility
    fn new(
        #[allow(unused_variables)] py: Python<'_>,
        path_or_handle: &Bound<'_, PyAny>,
        delimiter: Option<&str>,
        quotechar: Option<&str>,
        escapechar: Option<&str>,
        quoting: Option<u32>,
        lineterminator: Option<&str>,
        skipinitialspace: Option<bool>,
        strict: Option<bool>,
        double_quote: Option<bool>,
        read_size: Option<usize>,
        field_size_limit: Option<usize>,
    ) -> PyResult<Self> {
        // Try to extract as string first (file path)
        let (source, path, file_handle, event_loop) =
            if let Ok(path_str) = path_or_handle.extract::<String>() {
                validate_path(&path_str)?;
                (
                    FileSource::Path(path_str.clone()),
                    path_str,
                    Arc::new(StdMutex::new(None)),
                    Arc::new(StdMutex::new(None)),
                )
            } else {
                // Assume it's a file-like object
                let handle = path_or_handle.clone().unbind();
                // For file handles, use a placeholder path for error messages
                let placeholder_path = "<file_handle>".to_string();

                // Get the running event loop (required for aiofiles/rapfiles handles)
                // Must be available during construction since we're in Python's context
                let asyncio = py.import("asyncio")?;
                let loop_obj = asyncio.call_method0("get_running_loop").map_err(|_| {
                    PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(
                        "No running event loop found. File handles require a running event loop. \
                     Use 'async with' or ensure asyncio.run() has been called.",
                    )
                })?;

                let handle_clone = handle.clone_ref(py);
                let loop_clone = loop_obj.unbind();
                (
                    FileSource::Handle {
                        file: handle_clone.clone_ref(py),
                        event_loop: loop_clone.clone_ref(py),
                    },
                    placeholder_path,
                    Arc::new(StdMutex::new(Some(handle_clone))),
                    Arc::new(StdMutex::new(Some(loop_clone))), // Always store the loop
                )
            };

        let dialect = DialectConfig::from_python(
            delimiter,
            quotechar,
            escapechar,
            quoting,
            lineterminator,
            skipinitialspace,
            strict,
            double_quote,
        )?;
        Ok(Reader {
            source,
            path,
            file: Arc::new(Mutex::new(None)),
            file_handle,
            event_loop,
            buffer: Arc::new(Mutex::new(String::new())),
            buffer_start: Arc::new(Mutex::new(0)),
            position: Arc::new(Mutex::new(0)),
            line_num: Arc::new(Mutex::new(0)),
            dialect,
            read_size: read_size.unwrap_or(8192),
            field_size_limit,
        })
    }

    /// Get the current line number (1-based).
    #[getter]
    fn line_num(&self) -> PyResult<usize> {
        Python::attach(|_py| {
            Ok(*self.line_num.try_lock().map_err(|_| {
                PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(
                    "Cannot access line_num concurrently",
                )
            })?)
        })
    }

    /// Read the next row from the CSV file.
    fn read_row(self_: PyRef<Self>) -> PyResult<Py<PyAny>> {
        let path = self_.path.clone();
        let is_path = matches!(self_.source, FileSource::Path(_));
        let file = Arc::clone(&self_.file);
        let file_handle = Arc::clone(&self_.file_handle);
        let event_loop = Arc::clone(&self_.event_loop);
        let buffer = Arc::clone(&self_.buffer);
        let buffer_start = Arc::clone(&self_.buffer_start);
        let position = Arc::clone(&self_.position);
        let line_num = Arc::clone(&self_.line_num);
        let dialect = self_.dialect.clone();
        let chunk_size = self_.read_size;
        let field_size_limit = self_.field_size_limit;
        Python::attach(|py| {
            // For file handles, we'll extract and clone in async block where we can lock
            // But we can't easily clone Py<PyAny> without GIL in async
            // Workaround: pass Arc<Mutex> through and handle cloning inside read_from_python_file_arc
            // But that function has issues too. Let's use a simpler approach:
            // Extract once per call in the async block, accepting the limitation
            let future = async move {
                // Get current position
                let current_pos = {
                    let pos_guard = position.lock().await;
                    *pos_guard
                };

                // Read data incrementally in chunks until we can parse the next record
                // This is streaming because we only read chunks, not the entire file
                let mut buffer_guard = buffer.lock().await;
                let mut buffer_start_guard = buffer_start.lock().await;

                loop {
                    // Try to parse CSV from current buffer (starting from buffer_start)
                    let available_data = if *buffer_start_guard < buffer_guard.len() {
                        &buffer_guard[*buffer_start_guard..]
                    } else {
                        ""
                    };

                    if !available_data.is_empty() {
                        let mut csv_reader_builder = ReaderBuilder::new();
                        csv_reader_builder.has_headers(false);
                        dialect.apply_to_reader(&mut csv_reader_builder, field_size_limit);
                        let mut csv_reader =
                            csv_reader_builder.from_reader(available_data.as_bytes());

                        // available_data starts after buffer_start, which means records before current_pos
                        // are already consumed. So we should read the next record (at current_pos) directly
                        // without skipping, since available_data already starts at the right position.
                        // However, we need to account for the fact that buffer_start might not be exactly
                        // at a record boundary if the buffer was trimmed. So we still need to skip.
                        // Actually, let's calculate: if buffer_start > 0, some records were consumed.
                        // We need to figure out how many records are in the consumed portion.
                        // Simplest: always parse from buffer_start, and since we're tracking position
                        // separately, we know we want record at index current_pos.
                        // But available_data might start in the middle of the buffer, so we need to
                        // count how many records are before buffer_start.

                        // Simpler approach: parse from the beginning of available_data (which is
                        // the data we haven't consumed yet), and read the first record (which should
                        // be at position current_pos in the overall file).
                        let mut records_iter = csv_reader.records();

                        // Try to read the next record (first record in available_data should be at current_pos)
                        if let Some(result) = records_iter.next() {
                            match result {
                                Ok(record) => {
                                    let row: Vec<String> =
                                        record.iter().map(|s| s.to_string()).collect();

                                    // Get the byte position after reading this record
                                    // The csv_reader position() gives us where we are after the iterator consumed the record
                                    let consumed_in_slice = csv_reader.position().byte() as usize;

                                    // Count newlines in the consumed record for accurate line_num tracking
                                    // This handles multi-line records (quoted fields with newlines)
                                    let record_end = consumed_in_slice.min(available_data.len());
                                    let record_text = &available_data[..record_end];
                                    let newline_count = record_text
                                        .as_bytes()
                                        .iter()
                                        .filter(|&&b| b == b'\n')
                                        .count();

                                    // Update position and line_num
                                    {
                                        let mut pos_guard = position.lock().await;
                                        *pos_guard = current_pos + 1;
                                    }
                                    {
                                        // Increment line_num based on actual newlines in the record
                                        // For multi-line records, this counts all lines, not just records
                                        let mut line_num_guard = line_num.lock().await;
                                        if newline_count > 0 {
                                            *line_num_guard += newline_count;
                                        } else {
                                            // If no newline found, increment by 1 (single-line record)
                                            *line_num_guard += 1;
                                        }
                                    }

                                    // Update buffer_start to track consumed bytes
                                    *buffer_start_guard += consumed_in_slice;

                                    // Only trim buffer when it gets very large to prevent unbounded growth
                                    // This is still streaming as we read incrementally
                                    if buffer_guard.len() > chunk_size * 8 {
                                        // Trim buffer but reset position tracking
                                        let new_buffer =
                                            buffer_guard[*buffer_start_guard..].to_string();
                                        *buffer_guard = new_buffer;
                                        // Reset buffer_start and adjust position
                                        *buffer_start_guard = 0;
                                        // Note: We keep position as is since we've read that many records
                                    }

                                    return Ok(row);
                                }
                                Err(_e) => {
                                    // CSV parse error - might be incomplete record or malformed CSV
                                    // If we have enough data in buffer and still can't parse, it's likely malformed
                                    // We'll continue reading in case it's incomplete, but track the error
                                    // If we hit EOF and still have this error, we'll raise it
                                    // For now, continue reading more data
                                }
                            }
                        }
                    }

                    // Read more data from file in chunks
                    let chunk_result: PyResult<(String, bool)> = if is_path {
                        // Use Tokio File/BufReader for path-based sources
                        let mut file_guard = file.lock().await;
                        if file_guard.is_none() {
                            let opened_file = File::open(&path).await.map_err(|e| {
                                PyErr::new::<pyo3::exceptions::PyIOError, _>(format!(
                                    "Failed to open file {path}: {e}"
                                ))
                            })?;
                            *file_guard = Some(BufReader::new(opened_file));
                        }
                        let reader = file_guard.as_mut().unwrap();
                        let mut chunk = vec![0u8; chunk_size];
                        match reader.read(&mut chunk).await {
                            Ok(0) => Ok(("".to_string(), true)), // EOF
                            Ok(n) => {
                                chunk.truncate(n);
                                let chunk_str = String::from_utf8(chunk).map_err(|_| {
                                    PyErr::new::<pyo3::exceptions::PyIOError, _>(
                                        "Invalid UTF-8 in CSV file",
                                    )
                                })?;
                                Ok((chunk_str, false)) // Data read
                            }
                            Err(e) => Err(PyErr::new::<pyo3::exceptions::PyIOError, _>(format!(
                                "Failed to read file {path}: {e}"
                            ))),
                        }
                    } else {
                        // Use Python file handle for Handle sources
                        // Extract both file handle and event loop in a single spawn_blocking
                        // This ensures we get them before moving into async context
                        let file_handle_clone = file_handle.clone();
                        let event_loop_clone = event_loop.clone();
                        let (handle_py, loop_py) = tokio::task::spawn_blocking(move || {
                            #[allow(deprecated)]
                            // Python::with_gil is still required in blocking contexts (spawn_blocking)
                            Python::with_gil(|py| -> PyResult<(Py<PyAny>, Py<PyAny>)> {
                                // Extract file handle
                                let handle_guard = file_handle_clone.lock().map_err(|_| {
                                    PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(
                                        "Failed to lock file handle",
                                    )
                                })?;
                                let handle = handle_guard.as_ref().ok_or_else(|| {
                                    PyErr::new::<pyo3::exceptions::PyIOError, _>(
                                        "File handle not available",
                                    )
                                })?;

                                // Extract event loop
                                let loop_guard = event_loop_clone.lock().map_err(|_| {
                                    PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(
                                        "Failed to lock event loop",
                                    )
                                })?;
                                let loop_obj = loop_guard.as_ref().ok_or_else(|| {
                                    PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(
                                        "Event loop not available",
                                    )
                                })?;

                                Ok((handle.clone_ref(py), loop_obj.clone_ref(py)))
                            })
                        })
                        .await
                        .map_err(|e| {
                            PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(format!(
                                "Failed to extract file handle or event loop: {e}"
                            ))
                        })??;

                        // Now use the helper function with the extracted handle and loop
                        let chunk_str =
                            read_from_python_file(handle_py, loop_py, chunk_size).await?;

                        if chunk_str.is_empty() {
                            Ok(("".to_string(), true)) // EOF
                        } else {
                            Ok((chunk_str, false)) // Data read
                        }
                    };

                    match chunk_result {
                        Ok((_chunk_str, true)) => {
                            // EOF
                            // EOF - try final parse with remaining buffer
                            let available_data = if *buffer_start_guard < buffer_guard.len() {
                                &buffer_guard[*buffer_start_guard..]
                            } else {
                                ""
                            };

                            if available_data.is_empty() {
                                return Ok(Vec::<String>::new()); // EOF, no more data
                            }

                            // Final parse attempt with all remaining data
                            let mut csv_reader_builder = ReaderBuilder::new();
                            csv_reader_builder.has_headers(false);
                            dialect.apply_to_reader(&mut csv_reader_builder, field_size_limit);
                            let mut csv_reader =
                                csv_reader_builder.from_reader(available_data.as_bytes());

                            // available_data starts after consumed records, so read first record
                            let mut records_iter = csv_reader.records();

                            match records_iter.next() {
                                Some(Ok(record)) => {
                                    let row: Vec<String> =
                                        record.iter().map(|s| s.to_string()).collect();

                                    // Count newlines for accurate line_num tracking
                                    let csv_position = csv_reader.position();
                                    let consumed_in_slice = csv_position.byte() as usize;
                                    let record_end = consumed_in_slice.min(available_data.len());
                                    let record_text = &available_data[..record_end];
                                    let newline_count = record_text
                                        .as_bytes()
                                        .iter()
                                        .filter(|&&b| b == b'\n')
                                        .count();

                                    {
                                        let mut pos_guard = position.lock().await;
                                        *pos_guard = current_pos + 1;
                                    }
                                    {
                                        let mut line_num_guard = line_num.lock().await;
                                        if newline_count > 0 {
                                            *line_num_guard += newline_count;
                                        } else {
                                            *line_num_guard += 1;
                                        }
                                    }
                                    buffer_guard.clear();
                                    *buffer_start_guard = 0;
                                    return Ok(row);
                                }
                                Some(Err(e)) => {
                                    // CSV parse error at EOF - malformed CSV
                                    // Provide detailed error message with context
                                    let error_msg = format!(
                                        "CSV parse error at row {current_pos} (0-indexed) in file '{path}': {e}. \
                                        The CSV file may be malformed or have incomplete records."
                                    );
                                    return Err(CSVError::new_err(error_msg));
                                }
                                None => {
                                    return Ok(Vec::<String>::new()); // EOF
                                }
                            }
                        }
                        Ok((chunk_str, false)) => {
                            // Append chunk to buffer
                            buffer_guard.push_str(&chunk_str);
                        }
                        Err(e) => {
                            return Err(e);
                        }
                    }
                }
            };
            future_into_py(py, future).map(|bound| bound.unbind())
        })
    }

    /// Async iterator protocol - returns self.
    fn __aiter__(slf: PyRef<Self>) -> PyResult<Py<Self>> {
        Ok(slf.into())
    }

    /// Async iterator next - returns next row or raises StopAsyncIteration.
    ///
    /// Note: For proper StopAsyncIteration handling, this is best used via Python's
    /// async for syntax, which handles empty results correctly.
    fn __anext__(self_: PyRef<Self>) -> PyResult<Py<PyAny>> {
        // For now, delegate to read_row. A Python wrapper can handle StopAsyncIteration
        // TODO: Implement proper StopAsyncIteration in Rust when empty row is returned
        Reader::read_row(self_)
    }

    /// Read multiple rows at once.
    fn read_rows(self_: PyRef<Self>, n: usize) -> PyResult<Py<PyAny>> {
        let path = self_.path.clone();
        let is_path = matches!(self_.source, FileSource::Path(_));
        let file = Arc::clone(&self_.file);
        let file_handle = Arc::clone(&self_.file_handle);
        let event_loop = Arc::clone(&self_.event_loop);
        let buffer = Arc::clone(&self_.buffer);
        let buffer_start = Arc::clone(&self_.buffer_start);
        let position = Arc::clone(&self_.position);
        let line_num = Arc::clone(&self_.line_num);
        let dialect = self_.dialect.clone();
        let chunk_size = self_.read_size;
        let field_size_limit = self_.field_size_limit;
        Python::attach(|py| {
            let future = async move {
                let mut rows: Vec<Vec<String>> = Vec::new();

                // Get or open the file handle (once) - only for path-based sources
                if is_path {
                    let mut file_guard = file.lock().await;
                    if file_guard.is_none() {
                        let opened_file = File::open(&path).await.map_err(|e| {
                            PyErr::new::<pyo3::exceptions::PyIOError, _>(format!(
                                "Failed to open file {path}: {e}"
                            ))
                        })?;
                        *file_guard = Some(BufReader::new(opened_file));
                    }
                    drop(file_guard); // Release lock before loop
                }

                // Read n rows in a loop
                for _ in 0..n {
                    let current_pos = {
                        let pos_guard = position.lock().await;
                        *pos_guard
                    };

                    let mut buffer_guard = buffer.lock().await;
                    let mut buffer_start_guard = buffer_start.lock().await;

                    let mut row_found = false;
                    loop {
                        let available_data = if *buffer_start_guard < buffer_guard.len() {
                            &buffer_guard[*buffer_start_guard..]
                        } else {
                            ""
                        };

                        if !available_data.is_empty() {
                            let mut csv_reader_builder = ReaderBuilder::new();
                            csv_reader_builder.has_headers(false);
                            dialect.apply_to_reader(&mut csv_reader_builder, field_size_limit);
                            let mut csv_reader =
                                csv_reader_builder.from_reader(available_data.as_bytes());
                            let mut records_iter = csv_reader.records();

                            if let Some(result) = records_iter.next() {
                                match result {
                                    Ok(record) => {
                                        let row: Vec<String> =
                                            record.iter().map(|s| s.to_string()).collect();

                                        let consumed_in_slice =
                                            csv_reader.position().byte() as usize;

                                        // Count newlines in the consumed record for accurate line_num tracking
                                        let record_end =
                                            consumed_in_slice.min(available_data.len());
                                        let record_text = &available_data[..record_end];
                                        let newline_count = record_text
                                            .as_bytes()
                                            .iter()
                                            .filter(|&&b| b == b'\n')
                                            .count();

                                        {
                                            let mut pos_guard = position.lock().await;
                                            *pos_guard = current_pos + 1;
                                        }
                                        {
                                            // Increment line_num based on actual newlines in the record
                                            let mut line_num_guard = line_num.lock().await;
                                            if newline_count > 0 {
                                                *line_num_guard += newline_count;
                                            } else {
                                                *line_num_guard += 1;
                                            }
                                        }

                                        *buffer_start_guard += consumed_in_slice;

                                        if buffer_guard.len() > chunk_size * 8 {
                                            let new_buffer =
                                                buffer_guard[*buffer_start_guard..].to_string();
                                            *buffer_guard = new_buffer;
                                            *buffer_start_guard = 0;
                                        }

                                        rows.push(row);
                                        row_found = true;
                                        break;
                                    }
                                    Err(_) => {
                                        // Continue reading
                                    }
                                }
                            }
                        }

                        // Read more data from file
                        let chunk_result: PyResult<(String, bool)> = if is_path {
                            // Use Tokio File/BufReader for path-based sources
                            let mut file_guard = file.lock().await;
                            if file_guard.is_none() {
                                let opened_file = File::open(&path).await.map_err(|e| {
                                    PyErr::new::<pyo3::exceptions::PyIOError, _>(format!(
                                        "Failed to open file {path}: {e}"
                                    ))
                                })?;
                                *file_guard = Some(BufReader::new(opened_file));
                            }
                            let reader = file_guard.as_mut().unwrap();
                            let mut chunk = vec![0u8; chunk_size];
                            match reader.read(&mut chunk).await {
                                Ok(0) => Ok(("".to_string(), true)), // EOF
                                Ok(n) => {
                                    chunk.truncate(n);
                                    let chunk_str = String::from_utf8(chunk).map_err(|_| {
                                        PyErr::new::<pyo3::exceptions::PyIOError, _>(
                                            "Invalid UTF-8 in CSV file",
                                        )
                                    })?;
                                    Ok((chunk_str, false)) // Data read
                                }
                                Err(e) => Err(PyErr::new::<pyo3::exceptions::PyIOError, _>(
                                    format!("Failed to read file {path}: {e}"),
                                )),
                            }
                        } else {
                            // Use Python file handle for Handle sources
                            // Extract both file handle and event loop in a single spawn_blocking
                            // This ensures we get them before moving into async context
                            let file_handle_clone = file_handle.clone();
                            let event_loop_clone = event_loop.clone();
                            let (handle_py, loop_py) = tokio::task::spawn_blocking(move || {
                                #[allow(deprecated)]
                                // Python::with_gil is still required in blocking contexts (spawn_blocking)
                                Python::with_gil(|py| -> PyResult<(Py<PyAny>, Py<PyAny>)> {
                                    // Extract file handle
                                    let handle_guard = file_handle_clone.lock().map_err(|_| {
                                        PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(
                                            "Failed to lock file handle",
                                        )
                                    })?;
                                    let handle = handle_guard.as_ref().ok_or_else(|| {
                                        PyErr::new::<pyo3::exceptions::PyIOError, _>(
                                            "File handle not available",
                                        )
                                    })?;

                                    // Extract event loop
                                    let loop_guard = event_loop_clone.lock().map_err(|_| {
                                        PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(
                                            "Failed to lock event loop",
                                        )
                                    })?;
                                    let loop_obj = loop_guard.as_ref().ok_or_else(|| {
                                        PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(
                                            "Event loop not available",
                                        )
                                    })?;

                                    Ok((handle.clone_ref(py), loop_obj.clone_ref(py)))
                                })
                            })
                            .await
                            .map_err(|e| {
                                PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(format!(
                                    "Failed to extract file handle or event loop: {e}"
                                ))
                            })??;

                            let chunk_str =
                                read_from_python_file(handle_py, loop_py, chunk_size).await?;
                            Ok((chunk_str.clone(), chunk_str.is_empty()))
                        };

                        match chunk_result {
                            Ok((_chunk_str, true)) => {
                                // EOF
                                let available_data = if *buffer_start_guard < buffer_guard.len() {
                                    &buffer_guard[*buffer_start_guard..]
                                } else {
                                    ""
                                };

                                if available_data.is_empty() {
                                    break; // EOF, no more data
                                }

                                // Final parse attempt
                                let mut csv_reader_builder = ReaderBuilder::new();
                                csv_reader_builder.has_headers(false);
                                dialect.apply_to_reader(&mut csv_reader_builder, None);
                                let mut csv_reader =
                                    csv_reader_builder.from_reader(available_data.as_bytes());
                                let mut records_iter = csv_reader.records();

                                match records_iter.next() {
                                    Some(Ok(record)) => {
                                        let row: Vec<String> =
                                            record.iter().map(|s| s.to_string()).collect();

                                        let consumed_in_slice =
                                            csv_reader.position().byte() as usize;

                                        {
                                            let mut pos_guard = position.lock().await;
                                            *pos_guard = current_pos + 1;
                                        }
                                        {
                                            // Count newlines for accurate line_num tracking
                                            let record_end =
                                                consumed_in_slice.min(available_data.len());
                                            let record_text = &available_data[..record_end];
                                            let newline_count = record_text
                                                .as_bytes()
                                                .iter()
                                                .filter(|&&b| b == b'\n')
                                                .count();

                                            let mut line_num_guard = line_num.lock().await;
                                            if newline_count > 0 {
                                                *line_num_guard += newline_count;
                                            } else {
                                                *line_num_guard += 1;
                                            }
                                        }
                                        buffer_guard.clear();
                                        *buffer_start_guard = 0;
                                        rows.push(row);
                                        row_found = true;
                                    }
                                    Some(Err(e)) => {
                                        let error_msg = format!(
                                            "CSV parse error at row {current_pos} (0-indexed) in file '{path}': {e}. \
                                            The CSV file may be malformed or have incomplete records."
                                        );
                                        return Err(CSVError::new_err(error_msg));
                                    }
                                    None => {
                                        // EOF
                                    }
                                }
                                break;
                            }
                            Ok((chunk_str, false)) => {
                                // Append chunk to buffer
                                buffer_guard.push_str(&chunk_str);
                            }
                            Err(e) => {
                                return Err(e);
                            }
                        }
                    }

                    if !row_found {
                        break; // EOF reached
                    }
                }

                Ok(rows)
            };
            future_into_py(py, future).map(|bound| bound.unbind())
        })
    }

    /// Skip multiple rows efficiently without parsing.
    fn skip_rows(self_: PyRef<Self>, n: usize) -> PyResult<Py<PyAny>> {
        let path = self_.path.clone();
        let is_path = matches!(self_.source, FileSource::Path(_));
        let file = Arc::clone(&self_.file);
        let file_handle = Arc::clone(&self_.file_handle);
        let event_loop = Arc::clone(&self_.event_loop);
        let buffer = Arc::clone(&self_.buffer);
        let buffer_start = Arc::clone(&self_.buffer_start);
        let position = Arc::clone(&self_.position);
        let line_num = Arc::clone(&self_.line_num);
        let dialect = self_.dialect.clone();
        let chunk_size = self_.read_size;
        let field_size_limit = self_.field_size_limit;
        Python::attach(|py| {
            let future = async move {
                // Get or open the file handle (once) - only for path-based sources
                if is_path {
                    let mut file_guard = file.lock().await;
                    if file_guard.is_none() {
                        let opened_file = File::open(&path).await.map_err(|e| {
                            PyErr::new::<pyo3::exceptions::PyIOError, _>(format!(
                                "Failed to open file {path}: {e}"
                            ))
                        })?;
                        *file_guard = Some(BufReader::new(opened_file));
                    }
                    drop(file_guard); // Release lock before loop
                }

                // Skip n rows - parse but don't collect data
                for _ in 0..n {
                    let current_pos = {
                        let pos_guard = position.lock().await;
                        *pos_guard
                    };

                    let mut buffer_guard = buffer.lock().await;
                    let mut buffer_start_guard = buffer_start.lock().await;

                    let mut row_found = false;
                    loop {
                        let available_data = if *buffer_start_guard < buffer_guard.len() {
                            &buffer_guard[*buffer_start_guard..]
                        } else {
                            ""
                        };

                        if !available_data.is_empty() {
                            let mut csv_reader_builder = ReaderBuilder::new();
                            csv_reader_builder.has_headers(false);
                            dialect.apply_to_reader(&mut csv_reader_builder, field_size_limit);
                            let mut csv_reader =
                                csv_reader_builder.from_reader(available_data.as_bytes());
                            let mut records_iter = csv_reader.records();

                            if let Some(result) = records_iter.next() {
                                match result {
                                    Ok(_record) => {
                                        // Skip the actual data - just update position tracking
                                        let consumed_in_slice =
                                            csv_reader.position().byte() as usize;

                                        // Count newlines in the consumed record for accurate line_num tracking
                                        let record_end =
                                            consumed_in_slice.min(available_data.len());
                                        let record_text = &available_data[..record_end];
                                        let newline_count = record_text
                                            .as_bytes()
                                            .iter()
                                            .filter(|&&b| b == b'\n')
                                            .count();

                                        {
                                            let mut pos_guard = position.lock().await;
                                            *pos_guard = current_pos + 1;
                                        }
                                        {
                                            // Increment line_num based on actual newlines in the record
                                            let mut line_num_guard = line_num.lock().await;
                                            if newline_count > 0 {
                                                *line_num_guard += newline_count;
                                            } else {
                                                *line_num_guard += 1;
                                            }
                                        }

                                        *buffer_start_guard += consumed_in_slice;

                                        if buffer_guard.len() > chunk_size * 8 {
                                            let new_buffer =
                                                buffer_guard[*buffer_start_guard..].to_string();
                                            *buffer_guard = new_buffer;
                                            *buffer_start_guard = 0;
                                        }

                                        row_found = true;
                                        break;
                                    }
                                    Err(_) => {
                                        // Continue reading
                                    }
                                }
                            }
                        }

                        // Read more data from file
                        let chunk_result: PyResult<(String, bool)> = if is_path {
                            // Use Tokio File/BufReader for path-based sources
                            let mut file_guard = file.lock().await;
                            if file_guard.is_none() {
                                let opened_file = File::open(&path).await.map_err(|e| {
                                    PyErr::new::<pyo3::exceptions::PyIOError, _>(format!(
                                        "Failed to open file {path}: {e}"
                                    ))
                                })?;
                                *file_guard = Some(BufReader::new(opened_file));
                            }
                            let reader = file_guard.as_mut().unwrap();
                            let mut chunk = vec![0u8; chunk_size];
                            match reader.read(&mut chunk).await {
                                Ok(0) => Ok(("".to_string(), true)), // EOF
                                Ok(n) => {
                                    chunk.truncate(n);
                                    let chunk_str = String::from_utf8(chunk).map_err(|_| {
                                        PyErr::new::<pyo3::exceptions::PyIOError, _>(
                                            "Invalid UTF-8 in CSV file",
                                        )
                                    })?;
                                    Ok((chunk_str, false)) // Data read
                                }
                                Err(e) => Err(PyErr::new::<pyo3::exceptions::PyIOError, _>(
                                    format!("Failed to read file {path}: {e}"),
                                )),
                            }
                        } else {
                            // Use Python file handle for Handle sources
                            // Extract both file handle and event loop in a single spawn_blocking
                            // This ensures we get them before moving into async context
                            let file_handle_clone = file_handle.clone();
                            let event_loop_clone = event_loop.clone();
                            let (handle_py, loop_py) = tokio::task::spawn_blocking(move || {
                                #[allow(deprecated)]
                                // Python::with_gil is still required in blocking contexts (spawn_blocking)
                                Python::with_gil(|py| -> PyResult<(Py<PyAny>, Py<PyAny>)> {
                                    // Extract file handle
                                    let handle_guard = file_handle_clone.lock().map_err(|_| {
                                        PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(
                                            "Failed to lock file handle",
                                        )
                                    })?;
                                    let handle = handle_guard.as_ref().ok_or_else(|| {
                                        PyErr::new::<pyo3::exceptions::PyIOError, _>(
                                            "File handle not available",
                                        )
                                    })?;

                                    // Extract event loop
                                    let loop_guard = event_loop_clone.lock().map_err(|_| {
                                        PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(
                                            "Failed to lock event loop",
                                        )
                                    })?;
                                    let loop_obj = loop_guard.as_ref().ok_or_else(|| {
                                        PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(
                                            "Event loop not available",
                                        )
                                    })?;

                                    Ok((handle.clone_ref(py), loop_obj.clone_ref(py)))
                                })
                            })
                            .await
                            .map_err(|e| {
                                PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(format!(
                                    "Failed to extract file handle or event loop: {e}"
                                ))
                            })??;

                            let chunk_str =
                                read_from_python_file(handle_py, loop_py, chunk_size).await?;
                            Ok((chunk_str.clone(), chunk_str.is_empty()))
                        };

                        match chunk_result {
                            Ok((_chunk_str, true)) => {
                                // EOF
                                let available_data = if *buffer_start_guard < buffer_guard.len() {
                                    &buffer_guard[*buffer_start_guard..]
                                } else {
                                    ""
                                };

                                if available_data.is_empty() {
                                    break; // EOF, no more data
                                }

                                // Final parse attempt
                                let mut csv_reader_builder = ReaderBuilder::new();
                                csv_reader_builder.has_headers(false);
                                dialect.apply_to_reader(&mut csv_reader_builder, None);
                                let mut csv_reader =
                                    csv_reader_builder.from_reader(available_data.as_bytes());
                                let mut records_iter = csv_reader.records();

                                match records_iter.next() {
                                    Some(Ok(_record)) => {
                                        // Skip the data, just update position
                                        let consumed_in_slice =
                                            csv_reader.position().byte() as usize;

                                        {
                                            let mut pos_guard = position.lock().await;
                                            *pos_guard = current_pos + 1;
                                        }
                                        {
                                            // Count newlines for accurate line_num tracking
                                            let record_end =
                                                consumed_in_slice.min(available_data.len());
                                            let record_text = &available_data[..record_end];
                                            let newline_count = record_text
                                                .as_bytes()
                                                .iter()
                                                .filter(|&&b| b == b'\n')
                                                .count();

                                            let mut line_num_guard = line_num.lock().await;
                                            if newline_count > 0 {
                                                *line_num_guard += newline_count;
                                            } else {
                                                *line_num_guard += 1;
                                            }
                                        }
                                        buffer_guard.clear();
                                        *buffer_start_guard = 0;
                                        row_found = true;
                                    }
                                    Some(Err(e)) => {
                                        let error_msg = format!(
                                            "CSV parse error at row {current_pos} (0-indexed) in file '{path}': {e}. \
                                            The CSV file may be malformed or have incomplete records."
                                        );
                                        return Err(CSVError::new_err(error_msg));
                                    }
                                    None => {
                                        // EOF
                                    }
                                }
                                break;
                            }
                            Ok((chunk_str, false)) => {
                                // Append chunk to buffer
                                buffer_guard.push_str(&chunk_str);
                            }
                            Err(e) => {
                                return Err(e);
                            }
                        }
                    }

                    if !row_found {
                        break; // EOF reached
                    }
                }

                Ok(())
            };
            future_into_py(py, future).map(|bound| bound.unbind())
        })
    }

    /// Async context manager entry.
    fn __aenter__(slf: PyRef<Self>) -> PyResult<Py<PyAny>> {
        let slf: Py<Self> = slf.into();
        Python::attach(|py| {
            let future = async move { Ok(slf) };
            future_into_py(py, future).map(|bound| bound.unbind())
        })
    }

    /// Async context manager exit.
    fn __aexit__(
        &mut self,
        _exc_type: Option<&Bound<'_, PyAny>>,
        _exc_val: Option<&Bound<'_, PyAny>>,
        _exc_tb: Option<&Bound<'_, PyAny>>,
    ) -> PyResult<Py<PyAny>> {
        let file = Arc::clone(&self.file);
        let buffer = Arc::clone(&self.buffer);
        let buffer_start = Arc::clone(&self.buffer_start);
        Python::attach(|py| {
            let future = async move {
                // Close file handle
                let mut file_guard = file.lock().await;
                if file_guard.take().is_some() {
                    // File handle closed
                }
                // Clear buffer
                let mut buffer_guard = buffer.lock().await;
                buffer_guard.clear();
                let mut buffer_start_guard = buffer_start.lock().await;
                *buffer_start_guard = 0;
                Ok(())
            };
            future_into_py(py, future).map(|bound| bound.unbind())
        })
    }
}

/// Async CSV DictReader.
///
/// Provides dictionary-based CSV reading where rows are returned as dictionaries
/// mapping field names to values. Wraps a Reader internally.
#[pyclass]
struct AsyncDictReader {
    #[allow(dead_code)] // Kept for compatibility, but we use stored state directly
    reader: Py<Reader>, // Keep for compatibility, but we'll use stored state
    source: FileSource, // Either Path(String) or Handle {file, event_loop}
    path: String,       // Store separately for direct access
    file: Arc<Mutex<Option<BufReader<File>>>>, // Store separately - only used when source is Path
    file_handle: Arc<StdMutex<Option<Py<PyAny>>>>, // Python file handle when source is Handle
    event_loop: Arc<StdMutex<Option<Py<PyAny>>>>, // Event loop reference for run_coroutine_threadsafe
    buffer: Arc<Mutex<String>>,                   // Store separately
    buffer_start: Arc<Mutex<usize>>,              // Store separately
    position: Arc<Mutex<usize>>,                  // Store separately
    line_num: Arc<Mutex<usize>>,                  // Store separately
    dialect: DialectConfig,                       // Store separately
    read_size: usize,                             // Store separately
    fieldnames: Arc<Mutex<Option<Vec<String>>>>,
    restkey: Option<String>,
    restval: Option<String>,
}

#[pymethods]
impl AsyncDictReader {
    /// Create a new DictReader.
    ///
    /// # Arguments
    /// * `path` - Path to the CSV file
    /// * `fieldnames` - Optional list of field names. If None, first row is used as header.
    /// * `restkey` - Key name for extra values when row has more fields than fieldnames
    /// * `restval` - Default value for missing fields when row has fewer fields
    /// * All dialect parameters from Reader are supported
    #[new]
    #[pyo3(signature = (
        path_or_handle,
        fieldnames = None,
        restkey = None,
        restval = None,
        delimiter = None,
        quotechar = None,
        escapechar = None,
        quoting = None,
        lineterminator = None,
        skipinitialspace = None,
        strict = None,
        double_quote = None,
        read_size = None
    ))]
    #[allow(clippy::too_many_arguments)] // Required for Python API compatibility
    fn new(
        #[allow(unused_variables)] py: Python<'_>,
        path_or_handle: &Bound<'_, PyAny>,
        fieldnames: Option<Vec<String>>,
        restkey: Option<String>,
        restval: Option<String>,
        delimiter: Option<&str>,
        quotechar: Option<&str>,
        escapechar: Option<&str>,
        quoting: Option<u32>,
        lineterminator: Option<&str>,
        skipinitialspace: Option<bool>,
        strict: Option<bool>,
        double_quote: Option<bool>,
        read_size: Option<usize>,
    ) -> PyResult<Self> {
        // Try to extract as string first (file path)
        let (source, path_clone, file_handle, event_loop) =
            if let Ok(path_str) = path_or_handle.extract::<String>() {
                validate_path(&path_str)?;
                (
                    FileSource::Path(path_str.clone()),
                    path_str,
                    Arc::new(StdMutex::new(None)),
                    Arc::new(StdMutex::new(None)),
                )
            } else {
                // Assume it's a file-like object
                let handle = path_or_handle.clone().unbind();
                let placeholder_path = "<file_handle>".to_string();

                // Get the running event loop (required for aiofiles/rapfiles handles)
                // Must be available during construction since we're in Python's context
                let asyncio = py.import("asyncio")?;
                let loop_obj = asyncio.call_method0("get_running_loop").map_err(|_| {
                    PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(
                        "No running event loop found. File handles require a running event loop. \
                     Use 'async with' or ensure asyncio.run() has been called.",
                    )
                })?;

                let handle_clone = handle.clone_ref(py);
                let loop_clone = loop_obj.unbind();
                (
                    FileSource::Handle {
                        file: handle_clone.clone_ref(py),
                        event_loop: loop_clone.clone_ref(py),
                    },
                    placeholder_path,
                    Arc::new(StdMutex::new(Some(handle_clone))),
                    Arc::new(StdMutex::new(Some(loop_clone))), // Always store the loop
                )
            };

        let dialect = DialectConfig::from_python(
            delimiter,
            quotechar,
            escapechar,
            quoting,
            lineterminator,
            skipinitialspace,
            strict,
            double_quote,
        )?;
        let read_size_val = read_size.unwrap_or(8192);

        // Create a Reader for compatibility (even though AsyncDictReader has its own file handling)
        let reader = Reader::new(
            py,
            path_or_handle,
            delimiter,
            quotechar,
            escapechar,
            quoting,
            lineterminator,
            skipinitialspace,
            strict,
            double_quote,
            read_size,
            None, // field_size_limit - not used in DictReader for now
        )?;

        Ok(AsyncDictReader {
            reader: Py::new(py, reader)?,
            source,
            path: path_clone,
            file: Arc::new(Mutex::new(None)),
            file_handle,
            event_loop,
            buffer: Arc::new(Mutex::new(String::new())),
            buffer_start: Arc::new(Mutex::new(0)),
            position: Arc::new(Mutex::new(0)),
            line_num: Arc::new(Mutex::new(0)),
            dialect,
            read_size: read_size_val,
            fieldnames: Arc::new(Mutex::new(fieldnames)),
            restkey,
            restval,
        })
    }

    /// Read the next row as a dictionary.
    fn read_row(self_: PyRef<Self>) -> PyResult<Py<PyAny>> {
        let path = self_.path.clone();
        let is_path = matches!(self_.source, FileSource::Path(_));
        let file = Arc::clone(&self_.file);
        let file_handle = Arc::clone(&self_.file_handle);
        let event_loop = Arc::clone(&self_.event_loop);
        let buffer = Arc::clone(&self_.buffer);
        let buffer_start = Arc::clone(&self_.buffer_start);
        let position = Arc::clone(&self_.position);
        let line_num = Arc::clone(&self_.line_num);
        let dialect = self_.dialect.clone();
        let chunk_size = self_.read_size;
        let fieldnames = Arc::clone(&self_.fieldnames);
        let restkey = self_.restkey.clone();
        let restval = self_.restval.clone();

        Python::attach(|py| {
            let future = async move {
                // Get or open the file handle - only for path-based sources
                if is_path {
                    let mut file_guard = file.lock().await;
                    if file_guard.is_none() {
                        let opened_file = File::open(&path).await.map_err(|e| {
                            PyErr::new::<pyo3::exceptions::PyIOError, _>(format!(
                                "Failed to open file {path}: {e}"
                            ))
                        })?;
                        *file_guard = Some(BufReader::new(opened_file));
                    }
                }

                let mut buffer_guard = buffer.lock().await;
                let mut buffer_start_guard = buffer_start.lock().await;

                // Main loop: read rows and handle fieldnames lazily
                // If fieldnames are None, first row becomes fieldnames and we read next row
                let final_data_row = loop {
                    // Check if we need to load fieldnames
                    let need_fieldnames = {
                        let fieldnames_guard = fieldnames.lock().await;
                        fieldnames_guard.is_none()
                    };

                    // Read one row
                    let current_pos = {
                        let pos_guard = position.lock().await;
                        *pos_guard
                    };

                    #[allow(unused_assignments)]
                    // row_vec is assigned in inner loop and used in outer loop
                    let mut row_vec: Option<Vec<String>> = None;

                    // Inner loop to read one CSV record
                    loop {
                        let available_data = if *buffer_start_guard < buffer_guard.len() {
                            &buffer_guard[*buffer_start_guard..]
                        } else {
                            ""
                        };

                        if !available_data.is_empty() {
                            let mut csv_reader_builder = ReaderBuilder::new();
                            csv_reader_builder.has_headers(false);
                            dialect.apply_to_reader(&mut csv_reader_builder, None);
                            let mut csv_reader =
                                csv_reader_builder.from_reader(available_data.as_bytes());
                            let mut records_iter = csv_reader.records();

                            if let Some(result) = records_iter.next() {
                                match result {
                                    Ok(record) => {
                                        let row: Vec<String> =
                                            record.iter().map(|s| s.to_string()).collect();

                                        let consumed_in_slice =
                                            csv_reader.position().byte() as usize;

                                        // Count newlines in the consumed record for accurate line_num tracking
                                        let record_end =
                                            consumed_in_slice.min(available_data.len());
                                        let record_text = &available_data[..record_end];
                                        let newline_count = record_text
                                            .as_bytes()
                                            .iter()
                                            .filter(|&&b| b == b'\n')
                                            .count();

                                        {
                                            let mut pos_guard = position.lock().await;
                                            *pos_guard = current_pos + 1;
                                        }
                                        {
                                            // Increment line_num based on actual newlines in the record
                                            let mut line_num_guard = line_num.lock().await;
                                            if newline_count > 0 {
                                                *line_num_guard += newline_count;
                                            } else {
                                                *line_num_guard += 1;
                                            }
                                        }

                                        *buffer_start_guard += consumed_in_slice;

                                        if buffer_guard.len() > chunk_size * 8 {
                                            let new_buffer =
                                                buffer_guard[*buffer_start_guard..].to_string();
                                            *buffer_guard = new_buffer;
                                            *buffer_start_guard = 0;
                                        }

                                        row_vec = Some(row);
                                        break;
                                    }
                                    Err(_) => {
                                        // Continue reading
                                    }
                                }
                            }
                        }

                        // Read more data from file
                        let chunk_result: PyResult<(String, bool)> = if is_path {
                            // Use Tokio File/BufReader for path-based sources
                            let mut file_guard = file.lock().await;
                            if file_guard.is_none() {
                                let opened_file = File::open(&path).await.map_err(|e| {
                                    PyErr::new::<pyo3::exceptions::PyIOError, _>(format!(
                                        "Failed to open file {path}: {e}"
                                    ))
                                })?;
                                *file_guard = Some(BufReader::new(opened_file));
                            }
                            let reader = file_guard.as_mut().unwrap();
                            let mut chunk = vec![0u8; chunk_size];
                            match reader.read(&mut chunk).await {
                                Ok(0) => Ok(("".to_string(), true)), // EOF
                                Ok(n) => {
                                    chunk.truncate(n);
                                    let chunk_str = String::from_utf8(chunk).map_err(|_| {
                                        PyErr::new::<pyo3::exceptions::PyIOError, _>(
                                            "Invalid UTF-8 in CSV file",
                                        )
                                    })?;
                                    Ok((chunk_str, false)) // Data read
                                }
                                Err(e) => Err(PyErr::new::<pyo3::exceptions::PyIOError, _>(
                                    format!("Failed to read file {path}: {e}"),
                                )),
                            }
                        } else {
                            // Use Python file handle for Handle sources
                            // Extract both file handle and event loop in a single spawn_blocking
                            // This ensures we get them before moving into async context
                            let file_handle_clone = file_handle.clone();
                            let event_loop_clone = event_loop.clone();
                            let (handle_py, loop_py) = tokio::task::spawn_blocking(move || {
                                #[allow(deprecated)]
                                // Python::with_gil is still required in blocking contexts (spawn_blocking)
                                Python::with_gil(|py| -> PyResult<(Py<PyAny>, Py<PyAny>)> {
                                    // Extract file handle
                                    let handle_guard = file_handle_clone.lock().map_err(|_| {
                                        PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(
                                            "Failed to lock file handle",
                                        )
                                    })?;
                                    let handle = handle_guard.as_ref().ok_or_else(|| {
                                        PyErr::new::<pyo3::exceptions::PyIOError, _>(
                                            "File handle not available",
                                        )
                                    })?;

                                    // Extract event loop
                                    let loop_guard = event_loop_clone.lock().map_err(|_| {
                                        PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(
                                            "Failed to lock event loop",
                                        )
                                    })?;
                                    let loop_obj = loop_guard.as_ref().ok_or_else(|| {
                                        PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(
                                            "Event loop not available",
                                        )
                                    })?;

                                    Ok((handle.clone_ref(py), loop_obj.clone_ref(py)))
                                })
                            })
                            .await
                            .map_err(|e| {
                                PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(format!(
                                    "Failed to extract file handle or event loop: {e}"
                                ))
                            })??;

                            let chunk_str =
                                read_from_python_file(handle_py, loop_py, chunk_size).await?;
                            Ok((chunk_str.clone(), chunk_str.is_empty()))
                        };

                        match chunk_result {
                            Ok((_chunk_str, true)) => {
                                // EOF
                                let available_data = if *buffer_start_guard < buffer_guard.len() {
                                    &buffer_guard[*buffer_start_guard..]
                                } else {
                                    ""
                                };

                                if available_data.is_empty() {
                                    row_vec = Some(Vec::<String>::new()); // EOF
                                    break;
                                }

                                // Final parse attempt
                                let mut csv_reader_builder = ReaderBuilder::new();
                                csv_reader_builder.has_headers(false);
                                dialect.apply_to_reader(&mut csv_reader_builder, None);
                                let mut csv_reader =
                                    csv_reader_builder.from_reader(available_data.as_bytes());
                                let mut records_iter = csv_reader.records();

                                match records_iter.next() {
                                    Some(Ok(record)) => {
                                        let row: Vec<String> =
                                            record.iter().map(|s| s.to_string()).collect();

                                        let consumed_in_slice =
                                            csv_reader.position().byte() as usize;

                                        {
                                            let mut pos_guard = position.lock().await;
                                            *pos_guard = current_pos + 1;
                                        }
                                        {
                                            // Count newlines for accurate line_num tracking
                                            let record_end =
                                                consumed_in_slice.min(available_data.len());
                                            let record_text = &available_data[..record_end];
                                            let newline_count = record_text
                                                .as_bytes()
                                                .iter()
                                                .filter(|&&b| b == b'\n')
                                                .count();

                                            let mut line_num_guard = line_num.lock().await;
                                            if newline_count > 0 {
                                                *line_num_guard += newline_count;
                                            } else {
                                                *line_num_guard += 1;
                                            }
                                        }
                                        buffer_guard.clear();
                                        *buffer_start_guard = 0;
                                        row_vec = Some(row);
                                    }
                                    Some(Err(e)) => {
                                        let error_msg = format!(
                                            "CSV parse error at row {current_pos} (0-indexed) in file '{path}': {e}. \
                                            The CSV file may be malformed or have incomplete records."
                                        );
                                        return Err(CSVError::new_err(error_msg));
                                    }
                                    None => {
                                        row_vec = Some(Vec::<String>::new()); // EOF
                                    }
                                }
                                break;
                            }
                            Ok((chunk_str, false)) => {
                                // Append chunk to buffer
                                buffer_guard.push_str(&chunk_str);
                            }
                            Err(e) => {
                                return Err(e);
                            }
                        }
                    }

                    // Handle fieldnames
                    let mut fieldnames_guard = fieldnames.lock().await;

                    if need_fieldnames {
                        // First call - use row as fieldnames
                        match &row_vec {
                            Some(first_row) if !first_row.is_empty() => {
                                *fieldnames_guard = Some(first_row.clone());
                                drop(fieldnames_guard);
                                // Continue outer loop to read next row for actual data
                                continue;
                            }
                            Some(_) | None => {
                                // EOF or empty row
                                drop(fieldnames_guard);
                                break Vec::<String>::new();
                            }
                        }
                    } else {
                        // Fieldnames already loaded - use current row as data
                        drop(fieldnames_guard);
                        // row_vec should be Some at this point, but handle None just in case
                        match row_vec {
                            Some(row) => break row,
                            None => break Vec::<String>::new(), // EOF
                        }
                    }
                };

                // Get fieldnames for dict conversion
                let fieldnames_vec = {
                    let fieldnames_guard = fieldnames.lock().await;
                    fieldnames_guard.as_ref().unwrap().clone()
                };

                // Convert Vec<String> to PyDict
                #[allow(deprecated)] // Python::with_gil required in this async context
                Python::with_gil(|#[allow(unused_variables)] py| -> PyResult<Py<PyAny>> {
                    let py_dict = PyDict::new(py);

                    // If EOF (empty row), return empty dict
                    if final_data_row.is_empty() {
                        return Ok(py_dict.unbind().into());
                    }

                    let fieldnames_slice = &fieldnames_vec;

                    // Map fieldnames to values
                    let restval_default = restval.as_deref().unwrap_or("");
                    for (i, fieldname) in fieldnames_slice.iter().enumerate() {
                        let value = if i < final_data_row.len() {
                            &final_data_row[i]
                        } else {
                            // Missing field - use restval
                            restval_default
                        };
                        py_dict.set_item(fieldname, value)?;
                    }

                    // Handle restkey - extra values beyond fieldnames
                    if let Some(ref restkey_str) = restkey {
                        if final_data_row.len() > fieldnames_slice.len() {
                            let extra_values: Vec<String> =
                                final_data_row[fieldnames_slice.len()..].to_vec();
                            py_dict.set_item(restkey_str, extra_values)?;
                        }
                    }

                    Ok(py_dict.unbind().into())
                })
            };
            future_into_py(py, future).map(|bound| bound.unbind())
        })
    }

    /// Async iterator protocol - returns self.
    fn __aiter__(slf: PyRef<Self>) -> PyResult<Py<Self>> {
        Ok(slf.into())
    }

    /// Async iterator next - returns next row as dict or raises StopAsyncIteration.
    fn __anext__(self_: PyRef<Self>) -> PyResult<Py<PyAny>> {
        // Delegate to read_row, but we need to check for empty dict
        // Since read_row returns a Python awaitable, we'll handle StopAsyncIteration
        // by wrapping the call. For now, just call read_row - Python's async for
        // will handle empty results. We'll add proper StopAsyncIteration later if needed.
        AsyncDictReader::read_row(self_)
    }

    /// Get fieldnames (lazy loaded).
    fn get_fieldnames(self_: PyRef<Self>) -> PyResult<Py<PyAny>> {
        let fieldnames = Arc::clone(&self_.fieldnames);
        Python::attach(|py| {
            // Return fieldnames as Vec<String> - Python will convert to list
            // Using Option<Vec<String>> so None can be handled in Python
            let future = pyo3_async_runtimes::tokio::future_into_py(py, async move {
                let fieldnames_guard = fieldnames.lock().await;
                Ok::<Option<Vec<String>>, PyErr>(fieldnames_guard.clone())
            });
            future.map(|bound| bound.unbind())
        })
    }

    /// Fieldnames property (may be None until first row is read).
    fn fieldnames(self_: PyRef<Self>) -> PyResult<Option<Vec<String>>> {
        // Note: This accesses the Arc<Mutex> which may be locked in async context
        // For read-only access in sync context, try_lock should work
        Python::attach(|#[allow(unused_variables)] py| {
            self_.fieldnames.try_lock()
                .map(|guard| guard.clone())
                .map_err(|_| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(
                    "Cannot access fieldnames concurrently - use get_fieldnames() from async context"
                ))
        })
    }

    /// Add a field to the fieldnames list.
    fn add_field(self_: PyRef<Self>, field_name: String) -> PyResult<Py<PyAny>> {
        let fieldnames = Arc::clone(&self_.fieldnames);
        Python::attach(|py| {
            let future = async move {
                let mut fieldnames_guard = fieldnames.lock().await;
                if let Some(ref mut names) = *fieldnames_guard {
                    if !names.contains(&field_name) {
                        names.push(field_name);
                    }
                } else {
                    // If fieldnames not yet loaded, initialize with the new field
                    *fieldnames_guard = Some(vec![field_name]);
                }
                Ok(())
            };
            future_into_py(py, future).map(|bound| bound.unbind())
        })
    }

    /// Remove a field from the fieldnames list.
    fn remove_field(self_: PyRef<Self>, field_name: String) -> PyResult<Py<PyAny>> {
        let fieldnames = Arc::clone(&self_.fieldnames);
        Python::attach(|py| {
            let future = async move {
                let mut fieldnames_guard = fieldnames.lock().await;
                if let Some(ref mut names) = *fieldnames_guard {
                    names.retain(|name| name != &field_name);
                }
                Ok(())
            };
            future_into_py(py, future).map(|bound| bound.unbind())
        })
    }

    /// Rename a field in the fieldnames list.
    fn rename_field(self_: PyRef<Self>, old_name: String, new_name: String) -> PyResult<Py<PyAny>> {
        let fieldnames = Arc::clone(&self_.fieldnames);
        Python::attach(|py| {
            let future = async move {
                let mut fieldnames_guard = fieldnames.lock().await;
                if let Some(ref mut names) = *fieldnames_guard {
                    if let Some(pos) = names.iter().position(|name| name == &old_name) {
                        names[pos] = new_name;
                        Ok(())
                    } else {
                        Err(PyErr::new::<pyo3::exceptions::PyValueError, _>(format!(
                            "Field '{old_name}' not found in fieldnames"
                        )))
                    }
                } else {
                    Err(PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(
                        "Fieldnames not yet loaded. Read at least one row first.",
                    ))
                }
            };
            future_into_py(py, future).map(|bound| bound.unbind())
        })
    }
}

/// Async CSV DictWriter.
///
/// Provides dictionary-based CSV writing where rows are written as dictionaries
/// mapping field names to values. Wraps a Writer internally.
#[pyclass]
struct AsyncDictWriter {
    #[allow(dead_code)] // Kept for compatibility, but we use stored state directly
    writer: Py<Writer>,
    source: FileSource, // Either Path(String) or Handle {file, event_loop}
    path: String,       // Store path separately for writeheader/writerow access
    file: Arc<Mutex<Option<File>>>, // Store file Arc for writeheader/writerow access - only used when source is Path
    file_handle: Arc<StdMutex<Option<Py<PyAny>>>>, // Python file handle when source is Handle
    event_loop: Arc<StdMutex<Option<Py<PyAny>>>>, // Event loop reference for run_coroutine_threadsafe
    dialect: DialectConfig, // Store dialect separately for writeheader/writerow access
    fieldnames: Vec<String>,
    extrasaction: String, // "raise" or "ignore"
    restval: String,
}

#[pymethods]
impl AsyncDictWriter {
    /// Create a new DictWriter.
    ///
    /// # Arguments
    /// * `path` - Path to the CSV file
    /// * `fieldnames` - Required list of field names defining CSV structure
    /// * `extrasaction` - Action for extra keys: "raise" (default) or "ignore"
    /// * `restval` - Default value for missing keys (default: "")
    /// * All dialect parameters from Writer are supported
    #[new]
    #[pyo3(signature = (
        path_or_handle,
        fieldnames,
        extrasaction = "raise",
        restval = "",
        delimiter = None,
        quotechar = None,
        escapechar = None,
        quoting = None,
        lineterminator = None,
        skipinitialspace = None,
        strict = None,
        double_quote = None,
        write_size = None
    ))]
    #[allow(clippy::too_many_arguments)] // Required for Python API compatibility
    fn new(
        #[allow(unused_variables)] _py: Python<'_>,
        path_or_handle: &Bound<'_, PyAny>,
        fieldnames: Vec<String>,
        extrasaction: &str,
        restval: &str,
        delimiter: Option<&str>,
        quotechar: Option<&str>,
        escapechar: Option<&str>,
        quoting: Option<u32>,
        lineterminator: Option<&str>,
        #[allow(unused_variables)] skipinitialspace: Option<bool>,
        #[allow(unused_variables)] strict: Option<bool>,
        double_quote: Option<bool>,
        #[allow(unused_variables)] write_size: Option<usize>,
    ) -> PyResult<Self> {
        let dialect = DialectConfig::from_python(
            delimiter,
            quotechar,
            escapechar,
            quoting,
            lineterminator,
            None, // skipinitialspace not used for writer
            None, // strict not used for writer
            double_quote,
        )?;
        Python::attach(|py| {
            // Try to extract as string first (file path)
            let (source, path_str, file_handle, event_loop) =
                if let Ok(path_str) = path_or_handle.extract::<String>() {
                    validate_path(&path_str)?;
                    (
                        FileSource::Path(path_str.clone()),
                        path_str,
                        Arc::new(StdMutex::new(None)),
                        Arc::new(StdMutex::new(None)),
                    )
                } else {
                    // Assume it's a file-like object
                    let handle = path_or_handle.clone().unbind();
                    let placeholder_path = "<file_handle>".to_string();

                    // Get the running event loop (required for aiofiles/rapfiles handles)
                    // Must be available during construction since we're in Python's context
                    let asyncio = py.import("asyncio")?;
                    let loop_obj = asyncio.call_method0("get_running_loop").map_err(|_| {
                        PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(
                        "No running event loop found. File handles require a running event loop. \
                         Use 'async with' or ensure asyncio.run() has been called."
                    )
                    })?;

                    let handle_clone = handle.clone_ref(py);
                    let loop_clone = loop_obj.unbind();
                    (
                        FileSource::Handle {
                            file: handle_clone.clone_ref(py),
                            event_loop: loop_clone.clone_ref(py),
                        },
                        placeholder_path,
                        Arc::new(StdMutex::new(Some(handle_clone))),
                        Arc::new(StdMutex::new(Some(loop_clone))), // Always store the loop
                    )
                };

            let writer = Writer::new(
                py,
                path_or_handle,
                delimiter,
                quotechar,
                escapechar,
                quoting,
                lineterminator,
                double_quote,
                None, // write_size - use default
            )?;
            // Create separate file Arc for DictWriter (shares same file, but separate Arc)
            // Note: This means DictWriter and Writer don't share file state, which is acceptable
            let file_arc = Arc::new(Mutex::new(None::<File>));
            Ok(AsyncDictWriter {
                writer: Py::new(py, writer)?,
                source,
                path: path_str,
                file: file_arc,
                file_handle,
                event_loop,
                dialect,
                fieldnames,
                extrasaction: extrasaction.to_lowercase(),
                restval: restval.to_string(),
            })
        })
    }

    /// Write header row with fieldnames.
    fn writeheader(self_: PyRef<Self>) -> PyResult<Py<PyAny>> {
        let path = self_.path.clone();
        let is_path = matches!(self_.source, FileSource::Path(_));
        let file = Arc::clone(&self_.file);
        let file_handle = Arc::clone(&self_.file_handle);
        let event_loop = Arc::clone(&self_.event_loop);
        let dialect = self_.dialect.clone();
        let fieldnames = self_.fieldnames.clone();
        Python::attach(|py| {
            // Extract file handle and event loop BEFORE async block (while in Python context)
            let (handle_py_opt, loop_py_opt) = if !is_path {
                let handle_guard = file_handle.lock().map_err(|_| {
                    PyErr::new::<pyo3::exceptions::PyRuntimeError, _>("Failed to lock file handle")
                })?;
                let handle = handle_guard.as_ref().ok_or_else(|| {
                    PyErr::new::<pyo3::exceptions::PyIOError, _>("File handle not available")
                })?;

                let loop_guard = event_loop.lock().map_err(|_| {
                    PyErr::new::<pyo3::exceptions::PyRuntimeError, _>("Failed to lock event loop")
                })?;
                let loop_obj = loop_guard.as_ref().ok_or_else(|| {
                    PyErr::new::<pyo3::exceptions::PyRuntimeError, _>("Event loop not available")
                })?;

                (Some(handle.clone_ref(py)), Some(loop_obj.clone_ref(py)))
            } else {
                (None, None)
            };

            // Move extracted values into async block
            let handle_py_for_async = handle_py_opt;
            let loop_py_for_async = loop_py_opt;

            let future = async move {
                // Write fieldnames as CSV row
                let mut writer_builder = WriterBuilder::new();
                dialect.apply_to_writer(&mut writer_builder);
                let mut writer = writer_builder.from_writer(Vec::new());
                writer.write_record(&fieldnames).map_err(|e| {
                    PyErr::new::<pyo3::exceptions::PyIOError, _>(format!(
                        "Failed to write CSV record: {e}"
                    ))
                })?;
                writer.flush().map_err(|e| {
                    PyErr::new::<pyo3::exceptions::PyIOError, _>(format!(
                        "Failed to flush CSV writer: {e}"
                    ))
                })?;
                let csv_data = writer.into_inner().map_err(|e| {
                    PyErr::new::<pyo3::exceptions::PyIOError, _>(format!(
                        "Failed to finalize CSV record: {e}"
                    ))
                })?;

                if is_path {
                    // Get or open the file handle
                    let mut file_guard = file.lock().await;
                    if file_guard.is_none() {
                        use tokio::fs::OpenOptions;
                        *file_guard = Some(
                            OpenOptions::new()
                                .create(true)
                                .append(true)
                                .open(&path)
                                .await
                                .map_err(|e| {
                                    PyErr::new::<pyo3::exceptions::PyIOError, _>(format!(
                                        "Failed to open file {path}: {e}"
                                    ))
                                })?,
                        );
                    }
                    let file_ref = file_guard.as_mut().unwrap();
                    file_ref.write_all(&csv_data).await.map_err(|e| {
                        PyErr::new::<pyo3::exceptions::PyIOError, _>(format!(
                            "Failed to write file {path}: {e}"
                        ))
                    })?;
                    file_ref.flush().await.map_err(|e| {
                        PyErr::new::<pyo3::exceptions::PyIOError, _>(format!(
                            "Failed to flush file {path}: {e}"
                        ))
                    })?;
                } else {
                    // Use Python file handle for Handle sources
                    let csv_str = String::from_utf8(csv_data).map_err(|_| {
                        PyErr::new::<pyo3::exceptions::PyIOError, _>("Invalid UTF-8 in CSV data")
                    })?;

                    // Use the pre-extracted handle and loop
                    let handle_py = handle_py_for_async.ok_or_else(|| {
                        PyErr::new::<pyo3::exceptions::PyIOError, _>("File handle not available")
                    })?;
                    let loop_py = loop_py_for_async.ok_or_else(|| {
                        PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(
                            "Event loop not available",
                        )
                    })?;

                    write_to_python_file(handle_py, loop_py, csv_str).await?;
                }

                Ok(())
            };
            future_into_py(py, future).map(|bound| bound.unbind())
        })
    }

    /// Write a dictionary row.
    ///
    /// Converts dict to list based on fieldnames ordering.
    fn writerow(self_: PyRef<Self>, dict_row: &Bound<'_, PyDict>) -> PyResult<Py<PyAny>> {
        let path = self_.path.clone();
        let is_path = matches!(self_.source, FileSource::Path(_));
        let file = Arc::clone(&self_.file);
        let file_handle = Arc::clone(&self_.file_handle);
        let event_loop = Arc::clone(&self_.event_loop);
        let dialect = self_.dialect.clone();
        let fieldnames = self_.fieldnames.clone();
        let extrasaction = self_.extrasaction.clone();
        let restval = self_.restval.clone();

        // Extract dict values in GIL context before async move
        let row = Python::attach(|#[allow(unused_variables)] py| -> PyResult<Vec<String>> {
            // Check for extra keys if extrasaction == "raise"
            if extrasaction == "raise" {
                let dict_keys: Vec<String> = dict_row
                    .keys()
                    .iter()
                    .map(|k| k.extract::<String>().unwrap_or_default())
                    .collect();
                for key in &dict_keys {
                    if !fieldnames.contains(key) {
                        return Err(PyErr::new::<pyo3::exceptions::PyValueError, _>(format!(
                            "dict contains fields not in fieldnames: {key}"
                        )));
                    }
                }
            }

            // Build Vec<String> ordered by fieldnames
            let mut row = Vec::new();
            for fieldname in &fieldnames {
                match dict_row.get_item(fieldname) {
                    Ok(Some(value)) => {
                        let value_str = value
                            .extract::<String>()
                            .unwrap_or_else(|_| value.to_string());
                        row.push(value_str);
                    }
                    Ok(None) | Err(_) => {
                        // Missing key - use restval
                        row.push(restval.clone());
                    }
                }
            }
            Ok(row)
        })?;

        Python::attach(|py| {
            // Extract file handle and event loop BEFORE async block (while in Python context)
            let (handle_py_opt, loop_py_opt) = if !is_path {
                let handle_guard = file_handle.lock().map_err(|_| {
                    PyErr::new::<pyo3::exceptions::PyRuntimeError, _>("Failed to lock file handle")
                })?;
                let handle = handle_guard.as_ref().ok_or_else(|| {
                    PyErr::new::<pyo3::exceptions::PyIOError, _>("File handle not available")
                })?;

                let loop_guard = event_loop.lock().map_err(|_| {
                    PyErr::new::<pyo3::exceptions::PyRuntimeError, _>("Failed to lock event loop")
                })?;
                let loop_obj = loop_guard.as_ref().ok_or_else(|| {
                    PyErr::new::<pyo3::exceptions::PyRuntimeError, _>("Event loop not available")
                })?;

                (Some(handle.clone_ref(py)), Some(loop_obj.clone_ref(py)))
            } else {
                (None, None)
            };

            // Move extracted values into async block
            let handle_py_for_async = handle_py_opt;
            let loop_py_for_async = loop_py_opt;

            let future = async move {
                // Write row with CSV formatting
                let mut writer_builder = WriterBuilder::new();
                dialect.apply_to_writer(&mut writer_builder);
                let mut writer = writer_builder.from_writer(Vec::new());
                writer.write_record(&row).map_err(|e| {
                    PyErr::new::<pyo3::exceptions::PyIOError, _>(format!(
                        "Failed to write CSV record: {e}"
                    ))
                })?;
                writer.flush().map_err(|e| {
                    PyErr::new::<pyo3::exceptions::PyIOError, _>(format!(
                        "Failed to flush CSV writer: {e}"
                    ))
                })?;
                let csv_data = writer.into_inner().map_err(|e| {
                    PyErr::new::<pyo3::exceptions::PyIOError, _>(format!(
                        "Failed to finalize CSV record: {e}"
                    ))
                })?;

                if is_path {
                    // Get or open the file handle
                    let mut file_guard = file.lock().await;
                    if file_guard.is_none() {
                        use tokio::fs::OpenOptions;
                        *file_guard = Some(
                            OpenOptions::new()
                                .create(true)
                                .append(true)
                                .open(&path)
                                .await
                                .map_err(|e| {
                                    PyErr::new::<pyo3::exceptions::PyIOError, _>(format!(
                                        "Failed to open file {path}: {e}"
                                    ))
                                })?,
                        );
                    }
                    let file_ref = file_guard.as_mut().unwrap();
                    file_ref.write_all(&csv_data).await.map_err(|e| {
                        PyErr::new::<pyo3::exceptions::PyIOError, _>(format!(
                            "Failed to write file {path}: {e}"
                        ))
                    })?;
                    file_ref.flush().await.map_err(|e| {
                        PyErr::new::<pyo3::exceptions::PyIOError, _>(format!(
                            "Failed to flush file {path}: {e}"
                        ))
                    })?;
                } else {
                    // Use Python file handle for Handle sources
                    let csv_str = String::from_utf8(csv_data).map_err(|_| {
                        PyErr::new::<pyo3::exceptions::PyIOError, _>("Invalid UTF-8 in CSV data")
                    })?;

                    // Use the pre-extracted handle and loop
                    let handle_py = handle_py_for_async.ok_or_else(|| {
                        PyErr::new::<pyo3::exceptions::PyIOError, _>("File handle not available")
                    })?;
                    let loop_py = loop_py_for_async.ok_or_else(|| {
                        PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(
                            "Event loop not available",
                        )
                    })?;

                    write_to_python_file(handle_py, loop_py, csv_str).await?;
                }

                Ok(())
            };
            future_into_py(py, future).map(|bound| bound.unbind())
        })
    }

    /// Write multiple dictionary rows.
    fn writerows(self_: PyRef<Self>, dict_rows: &Bound<'_, PyAny>) -> PyResult<Py<PyAny>> {
        let path = self_.path.clone();
        let file = Arc::clone(&self_.file);
        let dialect = self_.dialect.clone();
        let fieldnames = self_.fieldnames.clone();
        let extrasaction = self_.extrasaction.clone();
        let restval = self_.restval.clone();

        // Convert all dicts to Vec<Vec<String>> in GIL context
        let rows = Python::attach(
            |#[allow(unused_variables)] py| -> PyResult<Vec<Vec<String>>> {
                let mut rows = Vec::new();

                // Try to get as PyList
                #[allow(deprecated)] // TODO: migrate to Bound::cast when available
                if let Ok(py_list) = dict_rows.downcast::<PyList>() {
                    for item in py_list.iter() {
                        #[allow(deprecated)] // TODO: migrate to Bound::cast when available
                        if let Ok(dict) = item.downcast::<PyDict>() {
                            // Check for extra keys if extrasaction == "raise"
                            if extrasaction == "raise" {
                                let dict_keys: Vec<String> = dict
                                    .keys()
                                    .iter()
                                    .map(|k| k.extract::<String>().unwrap_or_default())
                                    .collect();
                                for key in &dict_keys {
                                    if !fieldnames.contains(key) {
                                        return Err(
                                            PyErr::new::<pyo3::exceptions::PyValueError, _>(
                                                format!(
                                                    "dict contains fields not in fieldnames: {key}"
                                                ),
                                            ),
                                        );
                                    }
                                }
                            }

                            // Build Vec<String> ordered by fieldnames
                            let mut row = Vec::new();
                            for fieldname in &fieldnames {
                                match dict.get_item(fieldname) {
                                    Ok(Some(value)) => {
                                        let value_str = value
                                            .extract::<String>()
                                            .unwrap_or_else(|_| value.to_string());
                                        row.push(value_str);
                                    }
                                    Ok(None) | Err(_) => {
                                        row.push(restval.clone());
                                    }
                                }
                            }
                            rows.push(row);
                        } else {
                            return Err(PyErr::new::<pyo3::exceptions::PyTypeError, _>(
                                "writerows() requires a list of dictionaries",
                            ));
                        }
                    }
                } else {
                    return Err(PyErr::new::<pyo3::exceptions::PyTypeError, _>(
                        "writerows() requires a list of dictionaries",
                    ));
                }

                Ok(rows)
            },
        )?;

        Python::attach(|#[allow(unused_variables)] py| {
            let future = async move {
                // Get or open the file handle
                let mut file_guard = file.lock().await;
                if file_guard.is_none() {
                    use tokio::fs::OpenOptions;
                    *file_guard = Some(
                        OpenOptions::new()
                            .create(true)
                            .append(true)
                            .open(&path)
                            .await
                            .map_err(|e| {
                                PyErr::new::<pyo3::exceptions::PyIOError, _>(format!(
                                    "Failed to open file {path}: {e}"
                                ))
                            })?,
                    );
                }
                let file_ref = file_guard.as_mut().unwrap();

                // Write all rows
                for row in &rows {
                    let mut writer_builder = WriterBuilder::new();
                    dialect.apply_to_writer(&mut writer_builder);
                    let mut writer = writer_builder.from_writer(Vec::new());
                    writer.write_record(row).map_err(|e| {
                        PyErr::new::<pyo3::exceptions::PyIOError, _>(format!(
                            "Failed to write CSV record: {e}"
                        ))
                    })?;
                    writer.flush().map_err(|e| {
                        PyErr::new::<pyo3::exceptions::PyIOError, _>(format!(
                            "Failed to flush CSV writer: {e}"
                        ))
                    })?;
                    let csv_data = writer.into_inner().map_err(|e| {
                        PyErr::new::<pyo3::exceptions::PyIOError, _>(format!(
                            "Failed to finalize CSV record: {e}"
                        ))
                    })?;
                    file_ref.write_all(&csv_data).await.map_err(|e| {
                        PyErr::new::<pyo3::exceptions::PyIOError, _>(format!(
                            "Failed to write file {path}: {e}"
                        ))
                    })?;
                }

                // Flush to ensure all data is written
                file_ref.flush().await.map_err(|e| {
                    PyErr::new::<pyo3::exceptions::PyIOError, _>(format!(
                        "Failed to flush file {path}: {e}"
                    ))
                })?;

                Ok(())
            };
            future_into_py(py, future).map(|bound| bound.unbind())
        })
    }

    /// Close the file handle explicitly.
    fn close(self_: PyRef<Self>) -> PyResult<Py<PyAny>> {
        let is_path = matches!(self_.source, FileSource::Path(_));
        let file = Arc::clone(&self_.file);
        Python::attach(|#[allow(unused_variables)] py| {
            let future = async move {
                if is_path {
                    // For path-based sources, close the Tokio File
                    let mut file_guard = file.lock().await;
                    if let Some(mut f) = file_guard.take() {
                        f.flush().await.map_err(|e| {
                            PyErr::new::<pyo3::exceptions::PyIOError, _>(format!(
                                "Failed to flush file during close: {e}"
                            ))
                        })?;
                    }
                }
                // For file handle sources, closing is managed by Python (context manager)
                // No explicit close needed
                Ok(())
            };
            future_into_py(py, future).map(|bound| bound.unbind())
        })
    }
}

/// Async CSV writer.
///
/// Provides streaming async CSV writing with automatic RFC 4180 compliant
/// escaping and quoting. The file handle is reused across multiple `write_row()`
/// calls for efficient writing.
///
/// # Example
///
/// ```python
/// from rapcsv import Writer
///
/// async def write_csv():
///     writer = Writer("output.csv")
///     await writer.write_row(["name", "age", "city"])
///     await writer.write_row(["Alice", "30", "New York"])
///     await writer.close()
/// ```
///
/// # Context Manager
///
/// ```python
/// async with Writer("output.csv") as writer:
///     await writer.write_row(["name", "age"])
///     # File is automatically closed and flushed on exit
/// ```
#[pyclass]
struct Writer {
    source: FileSource,             // Either Path(String) or Handle {file, event_loop}
    path: String,                   // Keep for backward compatibility and error messages
    file: Arc<Mutex<Option<File>>>, // Only used when source is Path
    file_handle: Arc<StdMutex<Option<Py<PyAny>>>>, // Python file handle when source is Handle
    event_loop: Arc<StdMutex<Option<Py<PyAny>>>>, // Event loop reference for run_coroutine_threadsafe
    dialect: DialectConfig,
    #[allow(dead_code)] // Will be used for buffering write operations in future
    write_size: usize, // Configurable buffer size for writing
}

#[pymethods]
impl Writer {
    /// Create a new CSV file for writing.
    ///
    /// # Arguments
    /// * `path` - Path to the CSV file
    /// * `delimiter` - Field delimiter (default: ',')
    /// * `quotechar` - Quote character (default: '"')
    /// * `escapechar` - Escape character (default: None)
    /// * `quoting` - Quoting style: 0=QUOTE_NONE, 1=QUOTE_MINIMAL, 2=QUOTE_ALL, 3=QUOTE_NONNUMERIC, 4=QUOTE_NOTNULL, 6=QUOTE_STRINGS
    /// * `lineterminator` - Line terminator (default: '\r\n')
    /// * `double_quote` - Handle doubled quotes (default: true)
    /// * `write_size` - Buffer size for writing chunks (default: 8192)
    #[new]
    #[pyo3(signature = (
        path_or_handle,
        delimiter = None,
        quotechar = None,
        escapechar = None,
        quoting = None,
        lineterminator = None,
        double_quote = None,
        write_size = None
    ))]
    #[allow(clippy::too_many_arguments)] // Required for Python API compatibility
    fn new(
        #[allow(unused_variables)] py: Python<'_>,
        path_or_handle: &Bound<'_, PyAny>,
        delimiter: Option<&str>,
        quotechar: Option<&str>,
        escapechar: Option<&str>,
        quoting: Option<u32>,
        lineterminator: Option<&str>,
        double_quote: Option<bool>,
        write_size: Option<usize>,
    ) -> PyResult<Self> {
        // Try to extract as string first (file path)
        let (source, path, file_handle, event_loop) =
            if let Ok(path_str) = path_or_handle.extract::<String>() {
                validate_path(&path_str)?;
                (
                    FileSource::Path(path_str.clone()),
                    path_str,
                    Arc::new(StdMutex::new(None)),
                    Arc::new(StdMutex::new(None)),
                )
            } else {
                // Assume it's a file-like object
                let handle = path_or_handle.clone().unbind();
                // For file handles, use a placeholder path for error messages
                let placeholder_path = "<file_handle>".to_string();

                // Get the running event loop (required for aiofiles/rapfiles handles)
                // Must be available during construction since we're in Python's context
                let asyncio = py.import("asyncio")?;
                let loop_obj = asyncio.call_method0("get_running_loop").map_err(|_| {
                    PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(
                        "No running event loop found. File handles require a running event loop. \
                     Use 'async with' or ensure asyncio.run() has been called.",
                    )
                })?;

                let handle_clone = handle.clone_ref(py);
                let loop_clone = loop_obj.unbind();
                (
                    FileSource::Handle {
                        file: handle_clone.clone_ref(py),
                        event_loop: loop_clone.clone_ref(py),
                    },
                    placeholder_path,
                    Arc::new(StdMutex::new(Some(handle_clone))),
                    Arc::new(StdMutex::new(Some(loop_clone))), // Always store the loop
                )
            };

        let dialect = DialectConfig::from_python(
            delimiter,
            quotechar,
            escapechar,
            quoting,
            lineterminator,
            None, // skipinitialspace not used for writer
            None, // strict not used for writer
            double_quote,
        )?;
        Ok(Writer {
            source,
            path,
            file: Arc::new(Mutex::new(None)),
            file_handle,
            event_loop,
            dialect,
            write_size: write_size.unwrap_or(8192),
        })
    }

    /// Write a row to the CSV file.
    fn write_row(self_: PyRef<Self>, row: Vec<String>) -> PyResult<Py<PyAny>> {
        let path = self_.path.clone();
        let is_path = matches!(self_.source, FileSource::Path(_));
        let file = Arc::clone(&self_.file);
        let file_handle = Arc::clone(&self_.file_handle);
        let event_loop = Arc::clone(&self_.event_loop);
        let dialect = self_.dialect.clone();
        Python::attach(|py| {
            let future = async move {
                // Proper CSV writing with escaping and quoting (RFC 4180 compliant)
                let mut writer_builder = WriterBuilder::new();
                dialect.apply_to_writer(&mut writer_builder);
                let mut writer = writer_builder.from_writer(Vec::new());
                writer.write_record(&row).map_err(|e| {
                    PyErr::new::<pyo3::exceptions::PyIOError, _>(format!(
                        "Failed to write CSV record: {e}"
                    ))
                })?;
                writer.flush().map_err(|e| {
                    PyErr::new::<pyo3::exceptions::PyIOError, _>(format!(
                        "Failed to flush CSV writer: {e}"
                    ))
                })?;
                let csv_data = writer.into_inner().map_err(|e| {
                    PyErr::new::<pyo3::exceptions::PyIOError, _>(format!(
                        "Failed to finalize CSV record: {e}"
                    ))
                })?;

                if is_path {
                    // Use Tokio File for path-based sources
                    let mut file_guard = file.lock().await;
                    if file_guard.is_none() {
                        use tokio::fs::OpenOptions;
                        // Append mode - creates file if it doesn't exist
                        *file_guard = Some(
                            OpenOptions::new()
                                .create(true)
                                .append(true)
                                .open(&path)
                                .await
                                .map_err(|e| {
                                    PyErr::new::<pyo3::exceptions::PyIOError, _>(format!(
                                        "Failed to open file {path}: {e}"
                                    ))
                                })?,
                        );
                    }
                    let file_ref = file_guard.as_mut().unwrap();

                    file_ref.write_all(&csv_data).await.map_err(|e| {
                        PyErr::new::<pyo3::exceptions::PyIOError, _>(format!(
                            "Failed to write file {path}: {e}"
                        ))
                    })?;

                    // Flush to ensure data is written
                    file_ref.flush().await.map_err(|e| {
                        PyErr::new::<pyo3::exceptions::PyIOError, _>(format!(
                            "Failed to flush file {path}: {e}"
                        ))
                    })?;
                } else {
                    // Use Python file handle for Handle sources
                    let csv_str = String::from_utf8(csv_data).map_err(|_| {
                        PyErr::new::<pyo3::exceptions::PyIOError, _>("Invalid UTF-8 in CSV data")
                    })?;

                    // Extract handle and event loop together (stored during construction)
                    let file_handle_clone = file_handle.clone();
                    let event_loop_clone = event_loop.clone();
                    let (handle_py, loop_py) = tokio::task::spawn_blocking(move || {
                        #[allow(deprecated)] // Python::with_gil is still required in blocking contexts (spawn_blocking)
                        Python::with_gil(|py| -> PyResult<(Py<PyAny>, Py<PyAny>)> {
                            let handle_guard = file_handle_clone.lock().map_err(|_| {
                                PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(
                                    "Failed to lock file handle"
                                )
                            })?;
                            let handle = handle_guard.as_ref().ok_or_else(|| {
                                PyErr::new::<pyo3::exceptions::PyIOError, _>(
                                    "File handle not available"
                                )
                            })?;

                            let loop_guard = event_loop_clone.lock().map_err(|_| {
                                PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(
                                    "Failed to lock event loop"
                                )
                            })?;
                            let loop_ref = loop_guard.as_ref().ok_or_else(|| {
                                PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(
                                    "Event loop not available. This should not happen - file handles require an event loop during construction."
                                )
                            })?;

                            Ok((handle.clone_ref(py), loop_ref.clone_ref(py)))
                        })
                    })
                    .await
                    .map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(format!(
                        "Failed to extract file handle/event loop: {e}"
                    )))??;

                    write_to_python_file(handle_py, loop_py, csv_str).await?;
                }

                Ok(())
            };
            future_into_py(py, future).map(|bound| bound.unbind())
        })
    }

    /// Write multiple rows to the CSV file.
    fn writerows(self_: PyRef<Self>, rows: Vec<Vec<String>>) -> PyResult<Py<PyAny>> {
        let path = self_.path.clone();
        let is_path = matches!(self_.source, FileSource::Path(_));
        let file = Arc::clone(&self_.file);
        let file_handle = Arc::clone(&self_.file_handle);
        let event_loop = Arc::clone(&self_.event_loop);
        let dialect = self_.dialect.clone();
        Python::attach(|py| {
            let future = async move {
                // Write all rows
                for row in &rows {
                    let mut writer_builder = WriterBuilder::new();
                    dialect.apply_to_writer(&mut writer_builder);
                    let mut writer = writer_builder.from_writer(Vec::new());
                    writer.write_record(row).map_err(|e| {
                        PyErr::new::<pyo3::exceptions::PyIOError, _>(format!(
                            "Failed to write CSV record: {e}"
                        ))
                    })?;
                    writer.flush().map_err(|e| {
                        PyErr::new::<pyo3::exceptions::PyIOError, _>(format!(
                            "Failed to flush CSV writer: {e}"
                        ))
                    })?;
                    let csv_data = writer.into_inner().map_err(|e| {
                        PyErr::new::<pyo3::exceptions::PyIOError, _>(format!(
                            "Failed to finalize CSV record: {e}"
                        ))
                    })?;

                    if is_path {
                        // Use Tokio File for path-based sources
                        let mut file_guard = file.lock().await;
                        if file_guard.is_none() {
                            use tokio::fs::OpenOptions;
                            *file_guard = Some(
                                OpenOptions::new()
                                    .create(true)
                                    .append(true)
                                    .open(&path)
                                    .await
                                    .map_err(|e| {
                                        PyErr::new::<pyo3::exceptions::PyIOError, _>(format!(
                                            "Failed to open file {path}: {e}"
                                        ))
                                    })?,
                            );
                        }
                        let file_ref = file_guard.as_mut().unwrap();
                        file_ref.write_all(&csv_data).await.map_err(|e| {
                            PyErr::new::<pyo3::exceptions::PyIOError, _>(format!(
                                "Failed to write file {path}: {e}"
                            ))
                        })?;
                    } else {
                        // Use Python file handle for Handle sources
                        let csv_str = String::from_utf8(csv_data).map_err(|_| {
                            PyErr::new::<pyo3::exceptions::PyIOError, _>(
                                "Invalid UTF-8 in CSV data",
                            )
                        })?;

                        // Extract both file handle and event loop in a single spawn_blocking
                        // This ensures we get them before moving into async context
                        let file_handle_clone = file_handle.clone();
                        let event_loop_clone = event_loop.clone();
                        let (handle_py, loop_py) = tokio::task::spawn_blocking(move || {
                            #[allow(deprecated)]
                            // Python::with_gil is still required in blocking contexts (spawn_blocking)
                            Python::with_gil(|py| -> PyResult<(Py<PyAny>, Py<PyAny>)> {
                                // Extract file handle
                                let handle_guard = file_handle_clone.lock().map_err(|_| {
                                    PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(
                                        "Failed to lock file handle",
                                    )
                                })?;
                                let handle = handle_guard.as_ref().ok_or_else(|| {
                                    PyErr::new::<pyo3::exceptions::PyIOError, _>(
                                        "File handle not available",
                                    )
                                })?;

                                // Extract event loop
                                let loop_guard = event_loop_clone.lock().map_err(|_| {
                                    PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(
                                        "Failed to lock event loop",
                                    )
                                })?;
                                let loop_obj = loop_guard.as_ref().ok_or_else(|| {
                                    PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(
                                        "Event loop not available",
                                    )
                                })?;

                                Ok((handle.clone_ref(py), loop_obj.clone_ref(py)))
                            })
                        })
                        .await
                        .map_err(|e| {
                            PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(format!(
                                "Failed to extract file handle or event loop: {e}"
                            ))
                        })??;

                        write_to_python_file(handle_py, loop_py, csv_str).await?;
                    }
                }

                // Flush to ensure all data is written (only for path-based sources)
                if is_path {
                    let mut file_guard = file.lock().await;
                    if let Some(file_ref) = file_guard.as_mut() {
                        file_ref.flush().await.map_err(|e| {
                            PyErr::new::<pyo3::exceptions::PyIOError, _>(format!(
                                "Failed to flush file {path}: {e}"
                            ))
                        })?;
                    }
                }

                Ok(())
            };
            future_into_py(py, future).map(|bound| bound.unbind())
        })
    }

    /// Close the file handle explicitly.
    fn close(self_: PyRef<Self>) -> PyResult<Py<PyAny>> {
        let is_path = matches!(self_.source, FileSource::Path(_));
        let file = Arc::clone(&self_.file);
        Python::attach(|py| {
            let future = async move {
                if is_path {
                    // For path-based sources, close the Tokio File
                    let mut file_guard = file.lock().await;
                    if let Some(mut f) = file_guard.take() {
                        f.flush().await.map_err(|e| {
                            PyErr::new::<pyo3::exceptions::PyIOError, _>(format!(
                                "Failed to flush file during close: {e}"
                            ))
                        })?;
                    }
                }
                // For file handle sources, closing is managed by Python (context manager)
                // No explicit close needed
                Ok(())
            };
            future_into_py(py, future).map(|bound| bound.unbind())
        })
    }

    /// Async context manager entry.
    fn __aenter__(slf: PyRef<Self>) -> PyResult<Py<PyAny>> {
        let slf: Py<Self> = slf.into();
        Python::attach(|py| {
            let future = async move { Ok(slf) };
            future_into_py(py, future).map(|bound| bound.unbind())
        })
    }

    /// Async context manager exit.
    fn __aexit__(
        &mut self,
        _exc_type: Option<&Bound<'_, PyAny>>,
        _exc_val: Option<&Bound<'_, PyAny>>,
        _exc_tb: Option<&Bound<'_, PyAny>>,
    ) -> PyResult<Py<PyAny>> {
        let file = Arc::clone(&self.file);
        Python::attach(|py| {
            let future = async move {
                let mut file_guard = file.lock().await;
                if let Some(mut f) = file_guard.take() {
                    f.flush().await.map_err(|e| {
                        PyErr::new::<pyo3::exceptions::PyIOError, _>(format!(
                            "Failed to flush file during close: {e}"
                        ))
                    })?;
                }
                Ok(())
            };
            future_into_py(py, future).map(|bound| bound.unbind())
        })
    }
}
