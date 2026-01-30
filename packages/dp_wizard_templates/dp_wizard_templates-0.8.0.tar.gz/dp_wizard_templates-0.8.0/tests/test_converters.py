import json
import re
from pathlib import Path

import nbconvert
import pytest

from dp_wizard_templates.converters import (
    ConversionException,
    convert_from_notebook,
    convert_to_notebook,
)

fixtures_path = Path(__file__).parent / "fixtures"


def norm_notebook_json(nb_json_str):
    nb_dict = json.loads(nb_json_str)
    del nb_dict["metadata"]
    nb_json_str = json.dumps(nb_dict, indent=2)
    nb_json_str = re.sub(r'"id": "[^"]+"', '"id": "12345678"', nb_json_str)
    nb_json_str = re.sub(
        r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d+Z",
        "2024-01-01T00:00:00.000000Z",
        nb_json_str,
    )
    return nb_json_str


def test_convert_python_to_notebook():
    python_str = (fixtures_path / "fake.py").read_text()
    actual_nb_dict = convert_to_notebook(python_str, "Title!")
    actual_nb_json_str = json.dumps(actual_nb_dict)
    (fixtures_path / "actual-fake.ipynb").write_text(actual_nb_json_str)
    expected_nb_json_str = (fixtures_path / "expected-fake.ipynb").read_text()

    normed_actual_nb_json_str = norm_notebook_json(actual_nb_json_str)
    normed_expected_nb_json_str = norm_notebook_json(expected_nb_json_str)
    assert normed_actual_nb_json_str == normed_expected_nb_json_str


def test_convert_python_to_notebook_execute():
    python_str = (fixtures_path / "fake.py").read_text()
    actual_nb_dict = convert_to_notebook(python_str, "Title!", execute=True)
    actual_nb_json_str = json.dumps(actual_nb_dict, indent=1)
    (fixtures_path / "actual-fake-executed.ipynb").write_text(actual_nb_json_str)
    expected_nb_json_str = (fixtures_path / "expected-fake-executed.ipynb").read_text()

    normed_actual_nb_json_str = norm_notebook_json(actual_nb_json_str)
    normed_expected_nb_json_str = norm_notebook_json(expected_nb_json_str)
    assert normed_actual_nb_json_str == normed_expected_nb_json_str


def test_convert_notebook_to_html():
    notebook_str = (fixtures_path / "expected-fake-executed.ipynb").read_text()
    notebook_dict = json.loads(notebook_str)
    actual_html = convert_from_notebook(notebook_dict)
    (fixtures_path / "actual-fake-executed.html").write_text(actual_html)
    assert "[1]:" in actual_html
    assert "<pre>4" in actual_html

    expected_html = (fixtures_path / "expected-fake-executed.html").read_text()
    assert actual_html == expected_html


def test_convert_notebook_to_markdown():
    notebook_str = (fixtures_path / "expected-fake-executed.ipynb").read_text()
    notebook_dict = json.loads(notebook_str)
    md_exporter = nbconvert.MarkdownExporter()
    actual_md = convert_from_notebook(notebook_dict, exporter=md_exporter)
    (fixtures_path / "actual-fake-executed.md").write_text(actual_md)
    assert "```python" in actual_md

    expected_md = (fixtures_path / "expected-fake-executed.md").read_text()
    assert actual_md == expected_md


def test_convert_python_to_notebook_error():
    python_str = "Invalid python!"
    with pytest.raises(
        ConversionException,
        # There's more, but what's most important is that
        # the line with the error shows up in the message.
        match=(r"Invalid python!"),
    ):
        convert_to_notebook(python_str, "Title!", execute=True, reformat=False)
