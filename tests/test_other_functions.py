# Test:
# getCommandLineArguments,
# createBiblio

import pytest

from other_functions import (
    createBiblio,
    getCommandLineArguments,
)

success_prints = "Update: Successfully wrote to RIS file"
fail_prints = "Error: Writing to RIS file failed: "


@pytest.mark.parametrize(
    "data", [([{"title": "test1"}], success_prints), (["blah blah"], fail_prints)]
)
def test_createBiblio(tmp_path, capsys, data):
    risEntries = data[0]
    f = tmp_path / "output.ris"
    f.touch()
    createBiblio(f, risEntries)
    captured = capsys.readouterr().out
    assert "Update: Creating RIS file" in captured
    assert data[1] in captured


# Working
@pytest.mark.parametrize(
    "inputPath, outputPath, expected",
    [
        ("test", "", ("", "test")),
        ("test", "out.ris", ("out.ris", "test")),
        ("test", "out", ("out", "test")),
    ],
)
def test_getCommandLineArguments_valid_input(tmp_path, inputPath, outputPath, expected):
    # Just need a test directory
    pdf1 = tmp_path / "test/myfile.pdf"
    pdf1.parent.mkdir()
    result = getCommandLineArguments(
        [
            "--inputPath",
            str(tmp_path / inputPath),
            "--outputPath",
            str(tmp_path / outputPath),
        ]
    )
    expected = (str(tmp_path / expected[0]), str(tmp_path / expected[1]))
    assert result == expected


def set_up_test_directory(tmp_path):
    # Typical top-level PDF
    pdf1 = tmp_path / "test/myfile.pdf"
    pdf1.parent.mkdir()
    pdf1.touch()
    # Top-level PDF with dashes
    pdf2 = tmp_path / "test/my-file-2.pdf"
    pdf2.touch()


# This test not working
@pytest.mark.parametrize("inputPath, outputPath", [("test/foo", ""), ("", "test")])
def test_getCommandLineArguments_invalid_input(tmp_path, capsys, inputPath, outputPath):
    p1 = tmp_path / "test/foo"
    o1 = tmp_path / "test"
    set_up_test_directory(
        tmp_path
    )  # getCommandLineArguments(["--inputPath", str(tmp_path / inputPath), "--outputPath", str(tmp_path / outputPath)])
    with pytest.raises(SystemExit):
        result = getCommandLineArguments(
            ["--inputPath", str(p1), "--outputPath", str(o1)]
        )
        assert result == (str(tmp_path / "test"), str(tmp_path / "test/foo"))
        captured = capsys.readouterr()
        assert captured == "Error: Input path does not exist\nUpdate: Exiting program"


# Working
def test_getCommandLineArguments_invalid_input_arguments(tmp_path, capsys):
    set_up_test_directory(tmp_path)
    with pytest.raises(SystemExit):
        getCommandLineArguments([])
        captured = capsys.readouterr()
        assert (
            "usage: create_biblio.py [-h] --inputPath INPUTPATH [--outputPath OUTPUTPATH]\ncreate_biblio.py: error: argument --inputPath: expected one argument"
            in captured.err
        )
        getCommandLineArguments(["--inputPath"])
        captured = capsys.readouterr()
        assert (
            "usage: create_biblio.py [-h] --inputPath INPUTPATH [--outputPath OUTPUTPATH]\ncreate_biblio.py: error: argument --inputPath: expected one argument"
            in captured.err
        )
