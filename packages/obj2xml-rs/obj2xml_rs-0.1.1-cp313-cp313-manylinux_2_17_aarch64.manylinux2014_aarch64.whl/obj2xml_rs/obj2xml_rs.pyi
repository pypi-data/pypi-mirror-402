from typing import Any, Callable, Dict, IO, Iterable, Optional, Union

def unparse(
    input: Union[Dict[str, Any], Iterable[Any], Any],
    *,
    output: Optional[Union[str, IO[bytes], Any]] = None,
    encoding: str = "utf-8",
    full_document: bool = True,
    attr_prefix: str = "@",
    cdata_key: str = "#text",
    pretty: bool = False,
    indent: str = "  ",
    compat: str = "native",
    streaming: bool = False,
    default: Optional[Callable[[Any], str]] = None,
    item_name: str = "item",
    sort_attributes: bool = False,
    namespaces: Optional[Dict[str, str]] = None,
) -> str:
    """
    High-performance, feature-rich dictionary to XML converter.

    :param input:
        The input data to convert. Can be:
        - A dictionary representing the XML structure.
        - An iterable/generator (for streaming lists).
        - A primitive value.

    :param output:
        Destination to write the XML to. Can be:
        - None (returns the XML as a string).
        - A string (file path to write to).
        - A file-like object (must have a .write() method, like open() or io.BytesIO).

    :param encoding:
        The encoding to declare in the XML header (default: "utf-8").

    :param full_document:
        If True, adds the `<?xml ...?>` declaration and ensures a single root element.
        If False, generates an XML fragment (useful for streaming chunks).

    :param attr_prefix:
        The prefix used to identify attributes in the dictionary keys (default: "@").

    :param cdata_key:
        The key used to identify text content (default: "#text").

    :param pretty:
        If True, outputs formatted XML with indentation.

    :param indent:
        The string used for indentation if pretty is True (default: "  ").

    :param compat:
        Compatibility mode.
        - "native" (default): Produces clean XML (e.g., self-closing tags `<tag/>` for None).
        - "legacy": Emulates legacy behavior (e.g., `<tag></tag>` for None).

    :param streaming:
        If True, writes to `output` incrementally as the input is traversed.
        Useful for huge datasets that do not fit in memory.

    :param default:
        A callback function `f(obj) -> str` to handle types that are not natively supported
        (like datetime objects). Should raise TypeError or ValueError if conversion fails.

    :param item_name:
        The default tag name used for items in a list/generator if the tag cannot be
        inferred from a dictionary key (default: "item").

    :param sort_attributes:
        If True, sorts attributes alphabetically by name.
        Useful for deterministic output and testing.

    :param namespaces:
        A dictionary mapping prefixes to URIs (e.g., `{'soap': 'http://...'}`).
        These will be declared at the root element of the document.

    :return:
        The generated XML string if `output` is None, otherwise an empty string.
    """
    ...
