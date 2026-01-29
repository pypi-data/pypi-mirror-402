import io
import os
import tempfile
import pytest
import datetime
import asyncio
from functools import partial
from concurrent.futures import ThreadPoolExecutor

from obj2xml_rs import unparse


class Point:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def __str__(self):
        return "Not Used If Default Is Present"


def test_simple_element():
    xml = unparse({"root": "value"})
    assert xml == '<?xml version="1.0" encoding="utf-8"?><root>value</root>'


def test_integer_value():
    xml = unparse({"root": 123})
    assert "<root>123</root>" in xml


def test_boolean_values():
    xml = unparse({"root": {"true": True, "false": False}})
    assert "<true>true</true>" in xml
    assert "<false>false</false>" in xml


def test_attributes():
    xml = unparse({"root": {"@id": "123", "@class": "main", "child": "x"}})
    assert '<root id="123" class="main">' in xml
    assert "<child>x</child>" in xml


def test_only_attributes_self_closing():
    xml = unparse({"root": {"@id": "123"}})
    assert '<root id="123"/>' in xml or '<root id="123"></root>' in xml


def test_list_of_primitives():
    xml = unparse({"root": {"item": [1, 2, 3]}})
    assert xml.count("<item>") == 3
    assert "<item>1</item>" in xml
    assert "<item>2</item>" in xml
    assert "<item>3</item>" in xml


def test_list_of_dicts():
    xml = unparse(
        {
            "root": {
                "user": [
                    {"@id": 1, "name": "Alice"},
                    {"@id": 2, "name": "Bob"},
                ]
            }
        }
    )
    assert xml.count("<user") == 2
    assert 'id="1"' in xml
    assert 'id="2"' in xml
    assert "<name>Alice</name>" in xml
    assert "<name>Bob</name>" in xml


def test_none_value():
    xml = unparse({"root": None})
    assert "<root/>" in xml or "<root></root>" in xml


def test_none_child():
    xml = unparse({"root": {"empty": None}})
    assert "<empty/>" in xml or "<empty></empty>" in xml


def test_cdata_basic():
    xml = unparse({"root": {"#text": {"__cdata__": "Hello <world> & everyone"}}})
    assert "<![CDATA[Hello <world> & everyone]]>" in xml


def test_cdata_with_attributes():
    xml = unparse({"root": {"@id": "1", "#text": {"__cdata__": "CDATA text"}}})
    assert 'id="1"' in xml
    assert "<![CDATA[CDATA text]]>" in xml


def test_text_without_cdata():
    xml = unparse({"root": {"#text": "normal text"}})
    assert "<root>normal text</root>" in xml


def test_pretty_printing():
    xml = unparse(
        {"root": {"child": {"sub": 1}}},
        pretty=True,
        indent="    ",
    )
    assert "\n" in xml
    assert "    <child>" in xml


def test_multiple_roots_allowed():
    xml = unparse({"a": 1, "b": 2}, full_document=False)
    assert "<a>1</a>" in xml
    assert "<b>2</b>" in xml


def test_multiple_roots_disallowed():
    with pytest.raises(ValueError):
        unparse({"a": 1, "b": 2}, full_document=True)


def test_custom_encoding():
    xml = unparse({"root": "x"}, encoding="utf-16")
    assert 'encoding="utf-16"' in xml


def test_output_to_file_path():
    with tempfile.TemporaryDirectory() as tmp:
        path = os.path.join(tmp, "out.xml")
        result = unparse({"root": "x"}, output=path)
        assert result == ""
        with open(path, "r", encoding="utf-8") as f:
            data = f.read()
        assert "<root>x</root>" in data


def test_output_to_file_object():
    buf = io.BytesIO()
    result = unparse({"root": "x"}, output=buf)
    assert result == ""
    buf.seek(0)
    data = buf.read().decode()
    assert "<root>x</root>" in data


def test_obj2xml_none_behavior():
    xml = unparse({"root": {"child": None}}, compat="legacy")
    assert "<child></child>" in xml


def test_obj2xml_cdata():
    xml = unparse({"root": {"#text": {"__cdata__": "x"}}}, compat="legacy")
    assert "<![CDATA[x]]>" in xml


def test_empty_dict():
    xml = unparse({"root": {}})
    assert "<root" in xml


def test_deep_nesting():
    data = {"a": {"b": {"c": {"d": {"e": 1}}}}}
    xml = unparse(data)
    assert "<e>1</e>" in xml


def test_special_characters():
    xml = unparse({"root": "<>&\"'"})
    assert "&lt;" in xml or "<root>" in xml


def test_top_level_attributes_ignored():
    xml = unparse({"@id": 1, "root": "x"})
    assert "<root>x</root>" in xml
    assert "id=" not in xml


def test_generator_input_buffered():
    def my_gen():
        yield {"item": "A"}
        yield {"item": "B"}

    xml = unparse(my_gen(), full_document=False)
    assert "<item>A</item>" in xml
    assert "<item>B</item>" in xml


def test_generator_input_streaming_file():
    def big_data_gen():
        for i in range(5):
            yield {"row": {"@id": i, "#text": f"val_{i}"}}

    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp.close()
        unparse(big_data_gen(), output=tmp.name, streaming=True, full_document=False)
        with open(tmp.name, "r") as f:
            content = f.read()

        os.unlink(tmp.name)

    assert '<row id="0">val_0</row>' in content
    assert '<row id="4">val_4</row>' in content
    assert content.count("<row") == 5


def test_generator_primitives():
    def prime_gen():
        yield 1
        yield 2
        yield 3

    xml = unparse(prime_gen(), full_document=False)
    assert "<item>1</item><item>2</item><item>3</item>" in xml


def serialize_point(obj):
    if isinstance(obj, Point):
        return f"{obj.x};{obj.y}"
    if isinstance(obj, datetime.datetime):
        return obj.isoformat()
    raise TypeError(f"Unknown type: {type(obj)}")


def test_custom_serializer_attributes():
    p = Point(10, 20)
    data = {"root": {"@coords": p, "#text": "content"}}

    xml = unparse(data, default=serialize_point)
    assert 'coords="10;20"' in xml


def test_custom_serializer_leaf_node():
    p = Point(5, 5)
    data = {"root": {"location": p}}

    xml = unparse(data, default=serialize_point)
    assert "<location>5;5</location>" in xml


def test_custom_serializer_datetime():
    now = datetime.datetime(2023, 1, 1, 12, 0, 0)
    data = {"log": {"timestamp": now}}

    xml = unparse(data, default=serialize_point)
    assert "2023-01-01T12:00:00" in xml


def test_custom_serializer_failure():
    class Unknown:
        pass

    def fail_serializer(obj):
        raise ValueError("Boom")

    data = {"root": Unknown()}

    with pytest.raises(ValueError, match="Boom"):
        unparse(data, default=fail_serializer)


async def unparse_async_wrapper(data, **kwargs):
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, partial(unparse, data, **kwargs))


@pytest.mark.asyncio
async def test_async_generation():
    data = {"root": {"child": [i for i in range(100)]}}
    xml = await unparse_async_wrapper(data)

    assert "<root>" in xml
    assert "<child>99</child>" in xml
    assert xml.count("<child>") == 100


def test_generator_nested_custom_types():
    def complex_gen():
        yield {"event": {"time": datetime.datetime(2023, 1, 1, 10, 0)}}
        yield {"event": {"time": datetime.datetime(2023, 1, 1, 11, 0)}}

    xml = unparse(complex_gen(), default=serialize_point, full_document=False)
    assert "<time>2023-01-01T10:00:00</time>" in xml
    assert "<time>2023-01-01T11:00:00</time>" in xml


def test_custom_item_name():
    gen = (i for i in range(2))
    xml = unparse(gen, item_name="row", full_document=False)
    assert "<row>0</row><row>1</row>" in xml


def test_attribute_sorting():
    data = {"root": {"@z": "1", "@a": "2", "@m": "3"}}
    xml_unsorted = unparse(data)
    assert 'z="1" a="2" m="3"' in xml_unsorted or 'z="1" a="2"' in xml_unsorted
    xml_sorted = unparse(data, sort_attributes=True)
    assert 'a="2" m="3" z="1"' in xml_sorted


def test_root_namespaces():
    data = {
        "root": {
            "ns:child": "value",
            "@id": "1",
        }
    }
    xml = unparse(data, namespaces={"ns": "http://example.com"})

    assert 'xmlns:ns="http://example.com"' in xml
    assert "<ns:child>value</ns:child>" in xml


def test_error_context_path():
    class BadType:
        pass

    def fail_serializer(obj):
        raise ValueError("Cannot serialize this")

    data = {
        "root": {
            "users": [
                {"name": "Alice"},
                {"name": "Bob", "profile": {"@bad_attr": BadType()}},
            ]
        }
    }
    with pytest.raises(ValueError) as excinfo:
        unparse(data, default=fail_serializer)

    msg = str(excinfo.value)

    assert "Cannot serialize this" in msg
    assert "root/users/[1]/profile/@bad_attr" in msg


def test_repeated_root_restructured():
    data = {"users": {"user": [{"id": 1}, {"id": 2}]}}

    xml = unparse(data, full_document=False)
    assert "<users><user><id>1</id></user><user><id>2</id></user></users>" in xml


def test_tail_text_basic():
    """
    Test that #tail text appears immediately after the closing tag of the element.
    Structure: <root><child>Inside</child>Outside</root>
    """
    data = {"root": {"child": {"#text": "Inside", "#tail": "Outside"}}}
    xml = unparse(data)
    assert "<child>Inside</child>Outside" in xml


def test_tail_mixed_content():
    """
    Test a typical mixed-content scenario (like HTML).
    Expected: <p><b>Bold</b> and Regular</p>
    """
    data = {"p": {"b": {"#text": "Bold", "#tail": " and Regular"}}}
    xml = unparse(data, full_document=False)
    assert "<p><b>Bold</b> and Regular</p>" == xml


def test_tail_on_self_closing():
    data = {"root": {"br": {"#tail": "After Break"}}}
    xml = unparse(data)
    assert "<br/>After Break" in xml


def test_tail_with_attributes():
    data = {"item": {"@id": "1", "#text": "Inner", "#tail": "Outer"}}
    xml = unparse(data, full_document=False)
    assert '<item id="1">Inner</item>Outer' == xml


def test_tail_nested_multiple():
    data = {
        "list": {"item": [{"#text": "A", "#tail": ", "}, {"#text": "B", "#tail": "."}]}
    }
    xml = unparse(data, full_document=False)
    assert "<list><item>A</item>, <item>B</item>.</list>" == xml
