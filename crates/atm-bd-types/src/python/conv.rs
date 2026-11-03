//! One conversion trait between a contract type and its Python value, plus the Python annotation it shows.
//!
//! The record stubs are generated from these annotations, so a field's stub type always follows its Rust type.
use std::collections::BTreeMap;

use pyo3::exceptions::PyValueError;
use pyo3::prelude::*;

use crate::plugin::Sha;

/// A contract type with a Python-side value: `to_py` for getters, `from_py` for constructors.
pub(crate) trait Conv: Sized {
    /// The Python-side value pyo3 converts.
    type Py;
    /// The annotation the generated stub shows for this type.
    fn py_type() -> String;
    fn to_py(&self) -> Self::Py;
    fn from_py(value: Self::Py) -> PyResult<Self>;
}

macro_rules! conv_identity {
    ($($ty:ty => $name:literal),* $(,)?) => {
        $(impl Conv for $ty {
            type Py = $ty;
            fn py_type() -> String { $name.to_owned() }
            fn to_py(&self) -> $ty { self.clone() }
            fn from_py(value: $ty) -> PyResult<Self> { Ok(value) }
        })*
    };
}

conv_identity! { String => "str", bool => "bool", i32 => "int", i64 => "int", u32 => "int", u64 => "int" }

impl<T: Conv> Conv for Option<T> {
    type Py = Option<T::Py>;
    fn py_type() -> String {
        format!("{} | None", T::py_type())
    }
    fn to_py(&self) -> Self::Py {
        self.as_ref().map(T::to_py)
    }
    fn from_py(value: Self::Py) -> PyResult<Self> {
        value.map(T::from_py).transpose()
    }
}

impl<T: Conv> Conv for Vec<T> {
    type Py = Vec<T::Py>;
    fn py_type() -> String {
        format!("list[{}]", T::py_type())
    }
    fn to_py(&self) -> Self::Py {
        self.iter().map(T::to_py).collect()
    }
    fn from_py(value: Self::Py) -> PyResult<Self> {
        value.into_iter().map(T::from_py).collect()
    }
}

impl<K: Conv + Ord, V: Conv> Conv for BTreeMap<K, V>
where
    K::Py: Ord,
{
    type Py = BTreeMap<K::Py, V::Py>;
    fn py_type() -> String {
        format!("dict[{}, {}]", K::py_type(), V::py_type())
    }
    fn to_py(&self) -> Self::Py {
        self.iter().map(|(k, v)| (k.to_py(), v.to_py())).collect()
    }
    fn from_py(value: Self::Py) -> PyResult<Self> {
        value
            .into_iter()
            .map(|(k, v)| Ok((K::from_py(k)?, V::from_py(v)?)))
            .collect()
    }
}

impl Conv for Sha {
    type Py = String;
    fn py_type() -> String {
        "Sha".to_owned()
    }
    fn to_py(&self) -> String {
        self.as_str().to_owned()
    }
    fn from_py(value: String) -> PyResult<Self> {
        Sha::parse(&value)
            .ok_or_else(|| PyValueError::new_err(format!("not a 40-hex commit id: {value:?}")))
    }
}

/// Implements `Conv` for a newtype pyclass wrapper `$py($rust)` whose Python annotation is `$name`.
macro_rules! conv_wrapper {
    ($($rust:ty => $py:ident as $name:literal),* $(,)?) => {
        $(impl $crate::python::conv::Conv for $rust {
            type Py = $py;
            fn py_type() -> String { $name.to_owned() }
            fn to_py(&self) -> $py { $py(self.clone()) }
            fn from_py(value: $py) -> pyo3::PyResult<Self> { Ok(value.0) }
        })*
    };
}
pub(crate) use conv_wrapper;
