from hypothesis import given, strategies as st

@given(st.recursive(
	st.none() | st.booleans() | st.integers() | st.floats(allow_nan=False) | st.text(),
	lambda children: st.lists(children, max_size=5) | st.dictionaries(st.text(), children, max_size=5),
	max_leaves=10
))

def test_encode_with_hypothesis(data):
	try:
		result = encode(data)
		assert isinstance(result, str)
	except Exception as e:
		assert isinstance(e, (ToonEncodingError, CircularReferenceError, DatasetTooLargeError))
		

from src.python_toon import ToonEncodingError, CircularReferenceError, DatasetTooLargeError

def test_encode_circular_reference():
	a = {}
	a["self"] = a
	with pytest.raises(CircularReferenceError):
		encode(a)

def test_encode_dataset_too_large(monkeypatch):
	import json
	monkeypatch.setattr(json, "dumps", lambda d, default=None: "x" * (31 * 1024 * 1024))
	with pytest.raises(DatasetTooLargeError):
		encode({"a": 1})
		
from src.python_toon import EncodeOptions, Delimiter

def test_encode_with_indent():
	data = {"x": 1, "y": [1, 2]}
	options = EncodeOptions(indent=4)
	result = encode(data, options)
	assert isinstance(result, str)
	assert "x" in result and "y" in result

def test_encode_with_pipe_delimiter():
	data = {"nums": [1, 2, 3]}
	options = EncodeOptions(delimiter=Delimiter.PIPE)
	result = encode(data, options)
	assert "|" in result

import pytest
from src.python_toon import encode

def test_encode_simple_dict():
	data = {"a": 1, "b": 2}
	result = encode(data)
	assert isinstance(result, str)
	assert "a" in result and "b" in result

def test_encode_list():
	data = [1, 2, 3]
	result = encode(data)
	assert isinstance(result, str)
	assert "1" in result and "2" in result and "3" in result

def test_encode_nested():
	data = {"user": {"name": "Alice", "age": 30}, "active": True}
	result = encode(data)
	assert isinstance(result, str)
	assert "user" in result and "Alice" in result and "30" in result
