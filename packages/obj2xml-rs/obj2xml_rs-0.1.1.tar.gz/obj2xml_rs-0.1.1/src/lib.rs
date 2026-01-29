use pyo3::prelude::*;
use pyo3::types::{PyBool, PyDict, PyFloat, PyInt, PyIterator, PyList, PyNone, PyString};
use quick_xml::Writer;
use quick_xml::events::{BytesCData, BytesDecl, BytesEnd, BytesPI, BytesStart, BytesText, Event};
use rustc_hash::{FxHashMap, FxHashSet};
use std::borrow::Cow;
use std::fs::File;
use std::io::{BufWriter, Cursor, Write};

struct Config {
    attr_prefix: String,
    cdata_key: String,
    default_func: Option<Py<PyAny>>,
    item_name: String,
    sort_attrs: bool,
    namespaces: FxHashMap<String, String>,
}

#[derive(Clone, Copy, PartialEq)]
enum CompatMode {
    Native,
    Obj2Xml,
}

#[inline]
fn extract_str<'py>(value: &'py pyo3::Bound<'py, pyo3::PyAny>) -> PyResult<Cow<'py, str>> {
    if let Ok(pystr) = value.cast::<PyString>() {
        let slice = pystr.to_str()?;
        Ok(Cow::Borrowed(slice))
    } else {
        Ok(Cow::Owned(value.to_string()))
    }
}

struct PyWriter<'py> {
    obj: Bound<'py, PyAny>,
}

impl<'py> Write for PyWriter<'py> {
    fn write(&mut self, buf: &[u8]) -> std::io::Result<usize> {
        self.obj
            .call_method1("write", (buf,))
            .map_err(|e| std::io::Error::new(std::io::ErrorKind::Other, e.to_string()))?;
        Ok(buf.len())
    }
    fn flush(&mut self) -> std::io::Result<()> {
        if self.obj.hasattr("flush").unwrap_or(false) {
            self.obj
                .call_method0("flush")
                .map_err(|e| std::io::Error::new(std::io::ErrorKind::Other, e.to_string()))?;
        }
        Ok(())
    }
}

#[derive(Clone)]
struct NamespaceContext {
    uri_to_prefix: FxHashMap<String, String>,
    prefix_to_uri: FxHashMap<String, String>,
    next_auto: usize,
}

impl NamespaceContext {
    fn new(predefined: &FxHashMap<String, String>) -> Self {
        let mut uri_to_prefix = FxHashMap::default();
        let mut prefix_to_uri = FxHashMap::default();
        for (prefix, uri) in predefined {
            uri_to_prefix.insert(uri.clone(), prefix.clone());
            prefix_to_uri.insert(prefix.clone(), uri.clone());
        }
        Self {
            uri_to_prefix,
            prefix_to_uri,
            next_auto: 0,
        }
    }

    fn get_or_create_prefix(&mut self, uri: &str) -> String {
        if let Some(p) = self.uri_to_prefix.get(uri) {
            return p.clone();
        }
        let prefix = format!("ns{}", self.next_auto);
        self.next_auto += 1;
        self.uri_to_prefix.insert(uri.to_string(), prefix.clone());
        self.prefix_to_uri.insert(prefix.clone(), uri.to_string());
        prefix
    }
}

fn format_path(stack: &[String]) -> String {
    if stack.is_empty() {
        "root".to_string()
    } else {
        stack.join("/")
    }
}

#[inline(always)]
fn wrap_err<T, E: std::fmt::Display>(res: Result<T, E>, stack: &[String]) -> PyResult<T> {
    res.map_err(|e| {
        PyErr::new::<pyo3::exceptions::PyValueError, _>(format!(
            "{} (at {})",
            e,
            format_path(stack)
        ))
    })
}

#[inline(always)]
fn wrap_py_err<T>(res: PyResult<T>, stack: &[String]) -> PyResult<T> {
    res.map_err(|e| {
        PyErr::new::<pyo3::exceptions::PyValueError, _>(format!(
            "{} (at {})",
            e,
            format_path(stack)
        ))
    })
}

#[inline]
fn py_value_to_cow<'py>(
    py: Python<'py>,
    value: &'py pyo3::Bound<'py, pyo3::PyAny>,
    default_func: &Option<Py<PyAny>>,
    path: &[String],
) -> PyResult<Option<Cow<'py, str>>> {
    if value.is_instance_of::<PyNone>() {
        return Ok(None);
    }
    if value.is_instance_of::<PyBool>() {
        return Ok(Some(if value.extract::<bool>()? {
            "true".into()
        } else {
            "false".into()
        }));
    }
    if let Ok(pystr) = value.cast::<PyString>() {
        return Ok(Some(Cow::Borrowed(pystr.to_str()?)));
    }
    if value.is_instance_of::<PyInt>() || value.is_instance_of::<PyFloat>() {
        return Ok(Some(Cow::Owned(value.to_string())));
    }

    if let Some(func) = default_func {
        match func.call1(py, (value,)) {
            Ok(serialized) => return Ok(Some(Cow::Owned(serialized.to_string()))),
            Err(e) => {
                return Err(PyErr::new::<pyo3::exceptions::PyValueError, _>(format!(
                    "Custom serialization failed: {} (at {})",
                    e,
                    format_path(path)
                )));
            }
        }
    }
    Ok(Some(Cow::Owned(value.to_string())))
}

#[inline]
fn qualify_tag<'a>(
    tag: &'a str,
    dict: Option<&Bound<'_, PyDict>>,
    ns: &mut NamespaceContext,
) -> Cow<'a, str> {
    if tag.contains(':') {
        return Cow::Borrowed(tag);
    }
    if let Some(d) = dict {
        if let Ok(Some(ns_val)) = d.get_item("@ns") {
            let ns_str = ns_val.to_string();
            if ns.prefix_to_uri.contains_key(&ns_str) {
                return Cow::Owned(format!("{}:{}", ns_str, tag));
            }
            let prefix = ns.get_or_create_prefix(&ns_str);
            return Cow::Owned(format!("{}:{}", prefix, tag));
        }
    }
    Cow::Borrowed(tag)
}

fn process_node<W: Write>(
    writer: &mut Writer<W>,
    tag_name: &str,
    value: &Bound<'_, PyAny>,
    config: &Config,
    compat: CompatMode,
    ns: &mut NamespaceContext,
    is_root: bool,
    path: &mut Vec<String>,
    visited: &mut FxHashSet<usize>,
) -> PyResult<()> {
    let py = value.py();

    if value.is_instance_of::<PyString>()
        || value.is_instance_of::<PyBool>()
        || value.is_instance_of::<PyNone>()
        || value.is_instance_of::<PyInt>()
        || value.is_instance_of::<PyFloat>()
    {
    } else if let Ok(dict) = value.cast::<PyDict>() {
        let ptr = dict.as_ptr() as usize;
        if !visited.insert(ptr) {
            return Err(PyErr::new::<pyo3::exceptions::PyRecursionError, _>(
                format!("Circular reference detected (at {})", format_path(path)),
            ));
        }

        let mut tail_text: Option<String> = None;
        if let Ok(Some(tail_val)) = dict.get_item("#tail") {
            path.push("#tail".to_string());
            if let Some(cow) = py_value_to_cow(py, &tail_val, &config.default_func, path)? {
                tail_text = Some(cow.into_owned());
            }
            path.pop();
        }
        let mut ns_local = ns.clone();
        let qualified = qualify_tag(tag_name, Some(&dict), &mut ns_local);
        let mut elem = BytesStart::new(qualified.as_ref());
        let mut attrs = Vec::new();
        let mut xmlns_attrs = Vec::new();

        if is_root {
            for (prefix, uri) in &config.namespaces {
                if prefix.is_empty() {
                    xmlns_attrs.push(("xmlns".to_string(), uri.clone()));
                } else {
                    xmlns_attrs.push((format!("xmlns:{}", prefix), uri.clone()));
                }
            }
        }

        for (k, v) in dict {
            let k_cow = extract_str(&k)?;
            let k_str = k_cow.as_ref();
            if k_str == "#comment" || k_str == "#tail" || k_str.starts_with("?") {
                continue;
            }

            if k_str == "@xmlns" {
                let uri = v.to_string();
                if !config.namespaces.values().any(|u| u == &uri) {
                    let prefix = ns_local.get_or_create_prefix(&uri);
                    xmlns_attrs.push((format!("xmlns:{}", prefix), uri));
                }
            } else if let Some(p) = k_str.strip_prefix("@xmlns:") {
                let uri = v.to_string();
                ns_local.uri_to_prefix.insert(uri.clone(), p.to_string());
                ns_local.prefix_to_uri.insert(p.to_string(), uri.clone());
                xmlns_attrs.push((format!("xmlns:{}", p), uri));
            } else if let Some(attr) = k_str.strip_prefix(&config.attr_prefix) {
                path.push(format!("@{}", attr));
                if let Some(val) = py_value_to_cow(py, &v, &config.default_func, path)? {
                    attrs.push((attr.to_string(), val.into_owned()));
                }
                path.pop();
            }
        }

        if config.sort_attrs {
            attrs.sort_by(|a, b| a.0.cmp(&b.0));
            xmlns_attrs.sort_by(|a, b| a.0.cmp(&b.0));
        }
        for (k, v) in xmlns_attrs {
            elem.push_attribute((k.as_str(), v.as_str()));
        }
        for (k, v) in attrs {
            elem.push_attribute((k.as_str(), v.as_str()));
        }

        let has_children = dict.iter().any(|(k, _)| {
            let k_cow = k
                .cast::<PyString>()
                .map(|s| s.to_string_lossy())
                .unwrap_or_default();
            let ks = k_cow.as_ref();
            !ks.starts_with(&config.attr_prefix) && ks != "#tail"
        });

        if !has_children {
            wrap_err(writer.write_event(Event::Empty(elem)), path)?;
            visited.remove(&ptr);
            if let Some(text) = tail_text {
                wrap_err(writer.write_event(Event::Text(BytesText::new(&text))), path)?;
            }
            return Ok(());
        }

        wrap_err(writer.write_event(Event::Start(elem)), path)?;

        for (k, v) in dict {
            let k_cow = extract_str(&k)?;
            let k_str = k_cow.as_ref();

            if k_str.starts_with(&config.attr_prefix) {
                continue;
            }
            if k_str == "#tail" {
                continue;
            }

            path.push(k_str.to_string());

            if k_str == "#comment" {
                if let Some(comment_txt) = py_value_to_cow(py, &v, &config.default_func, path)? {
                    wrap_err(
                        writer.write_event(Event::Comment(BytesText::new(&comment_txt))),
                        path,
                    )?;
                }
            } else if k_str.starts_with("?") {
                if let Some(content) = py_value_to_cow(py, &v, &config.default_func, path)? {
                    let target = k_str.strip_prefix("?").unwrap_or(&k_str);
                    let pi_content = format!("{} {}", target, content);
                    wrap_err(
                        writer.write_event(Event::PI(BytesPI::new(&pi_content))),
                        path,
                    )?;
                }
            } else if k_str == config.cdata_key {
                let mut written = false;
                if let Ok(inner) = v.cast::<PyDict>() {
                    if let Ok(Some(cdata)) = inner.get_item("__cdata__") {
                        let s = cdata.to_string();
                        wrap_err(writer.write_event(Event::CData(BytesCData::new(&s))), path)?;
                        written = true;
                    }
                }
                if !written {
                    if let Some(text) = py_value_to_cow(py, &v, &config.default_func, path)? {
                        wrap_err(writer.write_event(Event::Text(BytesText::new(&text))), path)?;
                    }
                }
            } else {
                process_node(
                    writer,
                    k_str,
                    &v,
                    config,
                    compat,
                    &mut ns_local,
                    false,
                    path,
                    visited,
                )?;
            }
            path.pop();
        }
        wrap_err(
            writer.write_event(Event::End(BytesEnd::new(qualified.as_ref()))),
            path,
        )?;
        visited.remove(&ptr);

        if let Some(text) = tail_text {
            wrap_err(writer.write_event(Event::Text(BytesText::new(&text))), path)?;
        }

        return Ok(());
    } else if let Ok(list) = value.cast::<PyList>() {
        let ptr = list.as_ptr() as usize;
        if !visited.insert(ptr) {
            return Err(PyErr::new::<pyo3::exceptions::PyRecursionError, _>(
                format!("Circular ref (at {})", format_path(path)),
            ));
        }
        for (i, item) in list.iter().enumerate() {
            path.push(format!("[{}]", i));
            process_node(
                writer, tag_name, &item, config, compat, ns, is_root, path, visited,
            )?;
            path.pop();
        }
        visited.remove(&ptr);
        return Ok(());
    } else if let Ok(iter) = PyIterator::from_object(value) {
        let mut i = 0;
        for item in iter {
            let obj = item?;
            path.push(format!("[{}]", i));
            process_node(
                writer, tag_name, &obj, config, compat, ns, is_root, path, visited,
            )?;
            path.pop();
            i += 1;
        }
        return Ok(());
    }

    if value.is_instance_of::<PyNone>() {
        match compat {
            CompatMode::Native => {
                wrap_err(
                    writer.write_event(Event::Empty(BytesStart::new(tag_name))),
                    path,
                )?;
            }
            CompatMode::Obj2Xml => {
                wrap_err(
                    writer.write_event(Event::Start(BytesStart::new(tag_name))),
                    path,
                )?;
                wrap_err(
                    writer.write_event(Event::End(BytesEnd::new(tag_name))),
                    path,
                )?;
            }
        }
    } else if let Some(text) = py_value_to_cow(py, value, &config.default_func, path)? {
        let elem = BytesStart::new(tag_name);
        wrap_err(writer.write_event(Event::Start(elem)), path)?;
        wrap_err(writer.write_event(Event::Text(BytesText::new(&text))), path)?;
        wrap_err(
            writer.write_event(Event::End(BytesEnd::new(tag_name))),
            path,
        )?;
    }
    Ok(())
}

fn generate_xml<W: Write>(
    writer: W,
    input: &Bound<'_, PyAny>,
    encoding: &str,
    full_document: bool,
    pretty: bool,
    indent: &str,
    config: &Config,
    compat: CompatMode,
    attr_prefix: &str,
) -> PyResult<W> {
    let mut writer = if pretty {
        Writer::new_with_indent(writer, b' ', indent.len())
    } else {
        Writer::new(writer)
    };
    if full_document {
        writer
            .write_event(Event::Decl(BytesDecl::new("1.0", Some(encoding), None)))
            .map_err(|e| PyErr::new::<pyo3::exceptions::PyValueError, _>(e.to_string()))?;
    }
    let mut ns = NamespaceContext::new(&config.namespaces);
    let mut path = Vec::with_capacity(16);
    let mut visited = FxHashSet::default();

    if let Ok(dict) = input.cast::<PyDict>() {
        let roots = dict
            .iter()
            .filter(|(k, _)| !k.to_string().starts_with(attr_prefix))
            .count();
        if full_document && roots != 1 {
            return Err(PyErr::new::<pyo3::exceptions::PyValueError, _>(
                "Document must have exactly one root",
            ));
        }
        for (k, v) in dict {
            let key_cow = extract_str(&k)?;
            let key = key_cow.as_ref();
            if key.starts_with(attr_prefix) {
                continue;
            }
            path.push(key.to_string());
            process_node(
                &mut writer,
                key,
                &v,
                config,
                compat,
                &mut ns,
                true,
                &mut path,
                &mut visited,
            )?;
            path.pop();
        }
    } else {
        let iter = PyIterator::from_object(input)?;
        let mut i = 0;
        for item in iter {
            let obj = item?;
            path.push(format!("[{}]", i));
            if let Ok(d) = obj.cast::<PyDict>() {
                for (k, v) in d {
                    let k_cow = extract_str(&k)?;
                    let k_str = k_cow.as_ref();
                    path.push(k_str.to_string());
                    process_node(
                        &mut writer,
                        k_str,
                        &v,
                        config,
                        compat,
                        &mut ns,
                        true,
                        &mut path,
                        &mut visited,
                    )?;
                    path.pop();
                }
            } else {
                process_node(
                    &mut writer,
                    &config.item_name,
                    &obj,
                    config,
                    compat,
                    &mut ns,
                    true,
                    &mut path,
                    &mut visited,
                )?;
            }
            path.pop();
            i += 1;
        }
    }
    Ok(writer.into_inner())
}

#[pyfunction]
#[pyo3(signature = (
    input, *,
    output=None,
    encoding="utf-8",
    full_document=true,
    attr_prefix="@",
    cdata_key="#text",
    pretty=false, indent="  ",
    compat="native",
    streaming=false,
    default=None,
    item_name="item",
    sort_attributes=false,
    namespaces=None
))]
fn unparse(
    _py: Python<'_>,
    input: &Bound<'_, PyAny>,
    output: Option<&Bound<'_, PyAny>>,
    encoding: &str,
    full_document: bool,
    attr_prefix: &str,
    cdata_key: &str,
    pretty: bool,
    indent: &str,
    compat: &str,
    streaming: bool,
    default: Option<Py<PyAny>>,
    item_name: &str,
    sort_attributes: bool,
    namespaces: Option<FxHashMap<String, String>>,
) -> PyResult<String> {
    let config = Config {
        attr_prefix: attr_prefix.to_string(),
        cdata_key: cdata_key.to_string(),
        default_func: default,
        item_name: item_name.to_string(),
        sort_attrs: sort_attributes,
        namespaces: namespaces.unwrap_or_default(),
    };
    let compat_mode = if compat == "legacy" {
        CompatMode::Obj2Xml
    } else {
        CompatMode::Native
    };

    if streaming {
        let out_obj = output.ok_or_else(|| {
            PyErr::new::<pyo3::exceptions::PyValueError, _>(
                "streaming=True requires output argument",
            )
        })?;
        let sink: Box<dyn Write> = if let Ok(path) = out_obj.extract::<String>() {
            let f = File::create(path)?;
            Box::new(BufWriter::new(f))
        } else {
            Box::new(PyWriter {
                obj: out_obj.clone(),
            })
        };
        wrap_err(
            generate_xml(
                sink,
                input,
                encoding,
                full_document,
                pretty,
                indent,
                &config,
                compat_mode,
                attr_prefix,
            ),
            &[],
        )?;
        return Ok(String::new());
    }

    let cursor = Cursor::new(Vec::with_capacity(32 * 1024));
    let cursor = wrap_py_err(
        generate_xml(
            cursor,
            input,
            encoding,
            full_document,
            pretty,
            indent,
            &config,
            compat_mode,
            attr_prefix,
        ),
        &[],
    )?;
    let xml = String::from_utf8(cursor.into_inner())
        .map_err(|e| PyErr::new::<pyo3::exceptions::PyValueError, _>(e.to_string()))?;
    if let Some(out_obj) = output {
        if let Ok(path) = out_obj.extract::<String>() {
            std::fs::write(path, &xml)?;
        } else {
            out_obj.call_method1("write", (xml.as_bytes(),))?;
        }
        return Ok(String::new());
    }
    Ok(xml)
}

#[pymodule]
fn _obj2xml_rs(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(unparse, m)?)?;
    Ok(())
}
