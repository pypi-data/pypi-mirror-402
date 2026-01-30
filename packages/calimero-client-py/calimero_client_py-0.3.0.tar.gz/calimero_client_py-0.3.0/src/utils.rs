//! Utility functions for JSON to Python conversion

use pyo3::prelude::*;
use pyo3::types::{PyDict, PyList};

/// Convert serde_json::Value to Python object
pub fn json_to_python(py: Python, value: &serde_json::Value) -> PyObject {
    match value {
        serde_json::Value::Null => py.None(),
        serde_json::Value::Bool(b) => b.into_py(py),
        serde_json::Value::Number(n) => {
            if let Some(i) = n.as_i64() {
                i.into_py(py)
            } else if let Some(f) = n.as_f64() {
                f.into_py(py)
            } else {
                n.to_string().into_py(py)
            }
        }
        serde_json::Value::String(s) => s.into_py(py),
        serde_json::Value::Array(arr) => {
            let list = PyList::new_bound(py, Vec::<PyObject>::new());
            for item in arr {
                list.append(json_to_python(py, item)).unwrap();
            }
            list.into_py(py)
        }
        serde_json::Value::Object(obj) => {
            let dict = PyDict::new_bound(py);
            for (k, v) in obj {
                dict.set_item(k, json_to_python(py, v)).unwrap();
            }
            dict.into_py(py)
        }
    }
}
