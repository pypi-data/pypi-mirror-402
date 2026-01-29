#![allow(non_local_definitions)] // False positive from pyo3 macros

use csv::{ReaderBuilder, WriterBuilder};
use pyo3::create_exception;
use pyo3::exceptions::PyException;
use pyo3::prelude::*;
use pyo3_async_runtimes::tokio::future_into_py;
use std::sync::Arc;
use tokio::fs::File;
use tokio::io::{AsyncReadExt, AsyncWriteExt, BufReader};
use tokio::sync::Mutex;

// Exception classes (ABI3 compatible)
create_exception!(_rapcsv, CSVError, PyException);
create_exception!(_rapcsv, CSVFieldCountError, PyException);

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
    // Register exception classes (required for create_exception! to be accessible from Python)
    m.add("CSVError", py.get_type::<CSVError>())?;
    m.add("CSVFieldCountError", py.get_type::<CSVFieldCountError>())?;
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
    path: String,
    file: Arc<Mutex<Option<BufReader<File>>>>,
    buffer: Arc<Mutex<String>>,
    buffer_start: Arc<Mutex<usize>>, // Start position in buffer for next parse
    position: Arc<Mutex<usize>>,
}

#[pymethods]
impl Reader {
    /// Open a CSV file for reading.
    #[new]
    fn new(path: String) -> PyResult<Self> {
        validate_path(&path)?;
        Ok(Reader {
            path,
            file: Arc::new(Mutex::new(None)),
            buffer: Arc::new(Mutex::new(String::new())),
            buffer_start: Arc::new(Mutex::new(0)),
            position: Arc::new(Mutex::new(0)),
        })
    }

    /// Read the next row from the CSV file.
    fn read_row(self_: PyRef<Self>) -> PyResult<Py<PyAny>> {
        let path = self_.path.clone();
        let file = Arc::clone(&self_.file);
        let buffer = Arc::clone(&self_.buffer);
        let buffer_start = Arc::clone(&self_.buffer_start);
        let position = Arc::clone(&self_.position);
        Python::attach(|py| {
            let future = async move {
                // Get or open the file handle
                let mut file_guard = file.lock().await;
                if file_guard.is_none() {
                    let opened_file = File::open(&path).await.map_err(|e| {
                        PyErr::new::<pyo3::exceptions::PyIOError, _>(format!(
                            "Failed to open file {}: {e}",
                            path
                        ))
                    })?;
                    *file_guard = Some(BufReader::new(opened_file));
                }
                let reader = file_guard.as_mut().unwrap();

                // Get current position
                let current_pos = {
                    let pos_guard = position.lock().await;
                    *pos_guard
                };

                // Read data incrementally in chunks until we can parse the next record
                // This is streaming because we only read chunks, not the entire file
                let mut buffer_guard = buffer.lock().await;
                let mut buffer_start_guard = buffer_start.lock().await;
                const CHUNK_SIZE: usize = 8192; // 8KB chunks for efficient streaming

                loop {
                    // Try to parse CSV from current buffer (starting from buffer_start)
                    let available_data = if *buffer_start_guard < buffer_guard.len() {
                        &buffer_guard[*buffer_start_guard..]
                    } else {
                        ""
                    };

                    if !available_data.is_empty() {
                        let mut csv_reader = ReaderBuilder::new()
                            .has_headers(false)
                            .from_reader(available_data.as_bytes());

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

                                    // Update position
                                    {
                                        let mut pos_guard = position.lock().await;
                                        *pos_guard = current_pos + 1;
                                    }

                                    // Update buffer_start to track consumed bytes
                                    *buffer_start_guard += consumed_in_slice;

                                    // Only trim buffer when it gets very large to prevent unbounded growth
                                    // This is still streaming as we read incrementally
                                    if buffer_guard.len() > CHUNK_SIZE * 8 {
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
                    let mut chunk = vec![0u8; CHUNK_SIZE];
                    match reader.read(&mut chunk).await {
                        Ok(0) => {
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
                            let mut csv_reader = ReaderBuilder::new()
                                .has_headers(false)
                                .from_reader(available_data.as_bytes());

                            // available_data starts after consumed records, so read first record
                            let mut records_iter = csv_reader.records();

                            match records_iter.next() {
                                Some(Ok(record)) => {
                                    let row: Vec<String> =
                                        record.iter().map(|s| s.to_string()).collect();
                                    let mut pos_guard = position.lock().await;
                                    *pos_guard = current_pos + 1;
                                    buffer_guard.clear();
                                    *buffer_start_guard = 0;
                                    return Ok(row);
                                }
                                Some(Err(e)) => {
                                    // CSV parse error at EOF - malformed CSV
                                    // Provide detailed error message with context
                                    let error_msg = format!(
                                        "CSV parse error at row {} (0-indexed) in file '{}': {}. \
                                        The CSV file may be malformed or have incomplete records.",
                                        current_pos, path, e
                                    );
                                    return Err(CSVError::new_err(error_msg));
                                }
                                None => {
                                    return Ok(Vec::<String>::new()); // EOF
                                }
                            }
                        }
                        Ok(n) => {
                            // Append chunk to buffer
                            chunk.truncate(n);
                            match String::from_utf8(chunk) {
                                Ok(chunk_str) => {
                                    buffer_guard.push_str(&chunk_str);
                                }
                                Err(_) => {
                                    return Err(PyErr::new::<pyo3::exceptions::PyIOError, _>(
                                        "Invalid UTF-8 in CSV file",
                                    ));
                                }
                            }
                        }
                        Err(e) => {
                            return Err(PyErr::new::<pyo3::exceptions::PyIOError, _>(format!(
                                "Failed to read file {}: {e}",
                                path
                            )));
                        }
                    }
                }
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
    path: String,
    file: Arc<Mutex<Option<File>>>,
}

#[pymethods]
impl Writer {
    /// Create a new CSV file for writing.
    #[new]
    fn new(path: String) -> PyResult<Self> {
        validate_path(&path)?;
        Ok(Writer {
            path,
            file: Arc::new(Mutex::new(None)),
        })
    }

    /// Write a row to the CSV file.
    fn write_row(self_: PyRef<Self>, row: Vec<String>) -> PyResult<Py<PyAny>> {
        let path = self_.path.clone();
        let file = Arc::clone(&self_.file);
        Python::attach(|py| {
            let future = async move {
                // Get or open the file handle
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
                                    "Failed to open file {}: {e}",
                                    path
                                ))
                            })?,
                    );
                }
                let file_ref = file_guard.as_mut().unwrap();

                // Proper CSV writing with escaping and quoting (RFC 4180 compliant)
                let mut writer = WriterBuilder::new()
                    .has_headers(false)
                    .from_writer(Vec::new());
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
                file_ref.write_all(&csv_data).await.map_err(|e| {
                    PyErr::new::<pyo3::exceptions::PyIOError, _>(format!(
                        "Failed to write file {}: {e}",
                        path
                    ))
                })?;

                // Flush to ensure data is written
                file_ref.flush().await.map_err(|e| {
                    PyErr::new::<pyo3::exceptions::PyIOError, _>(format!(
                        "Failed to flush file {}: {e}",
                        path
                    ))
                })?;

                Ok(())
            };
            future_into_py(py, future).map(|bound| bound.unbind())
        })
    }

    /// Close the file handle explicitly.
    fn close(self_: PyRef<Self>) -> PyResult<Py<PyAny>> {
        let file = Arc::clone(&self_.file);
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
