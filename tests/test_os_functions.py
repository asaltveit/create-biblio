from os_functions import (
    searchFolder,
    checkOutputFileType,
    checkInputPathExists,
    getLastInputPathParameter,
)


def set_up_test_directory(tmp_path):
    # Typical top-level PDF
    pdf1 = tmp_path / "mydir/myfile.pdf"
    pdf1.parent.mkdir()
    pdf1.touch()
    # Top-level PDF with dashes
    pdf2 = tmp_path / "mydir/my-file-2.pdf"
    pdf2.touch()
    # Subfolder PDF starting with a dash
    pdf3 = tmp_path / "mydir/innerFolder/-testFile3.pdf"
    pdf3.parent.mkdir()
    pdf3.touch()
    # Subfolder not a pdf
    docx1 = tmp_path / "mydir/innerFolder/testFile4.docx"
    docx1.touch()


# searchFolder
def test_searchFolder(tmp_path, capsys):
    paths = ["mydir/myfile.pdf", "mydir/my-file-2.pdf"]
    set_up_test_directory(tmp_path)
    result = searchFolder(tmp_path)
    captured = capsys.readouterr().out
    for i in range(len(result)):
        assert result[i].endswith(paths[i])
        # Make sure files to be avoided are avoided
        assert not result[i].endswith("-testFile3.pdf")
        assert not result[i].endswith("testFile4.docx")
    assert len(captured.split("U")[1:]) == 2
    assert len(captured.split("E")[1:]) == 0
    assert "Update: Found 2 paths" in captured


# checkOutputFileType
def test_checkOutputFileType(tmp_path):
    set_up_test_directory(tmp_path)
    assert checkOutputFileType("test.ris", tmp_path) == "test.ris"
    assert checkOutputFileType("test.pdf", tmp_path) == "test.ris"
    # Do I need this? It's tested below
    assert checkOutputFileType("", tmp_path).endswith("test_checkOutputFileType0.ris")


# checkInputPathExists
def test_checkInputPathExists_true(tmp_path, capsys):
    set_up_test_directory(tmp_path)
    assert checkInputPathExists(tmp_path)
    captured = capsys.readouterr().out
    assert len(captured.split("U")[1:]) == 1
    assert len(captured.split("E")[1:]) == 0
    assert "Input path exists" in captured


def test_checkInputPathExists_false(tmp_path, capsys):
    set_up_test_directory(tmp_path)
    assert not checkInputPathExists("mydit")
    captured = capsys.readouterr().out
    # Looking for "Error", not "Update"
    assert len(captured.split("E")[1:]) == 1
    assert len(captured.split("U")[1:]) == 0
    assert "Input path does not exist" in captured


# How to create an exception?
def test_checkInputPathExists_except(tmp_path, capsys):
    pass


# getLastInputPathParameter
def test_getLastInputPathParameter(tmp_path):
    set_up_test_directory(tmp_path)
    # MacOS
    assert getLastInputPathParameter(tmp_path).endswith(
        "test_getLastInputPathParameter0.ris"
    )
    # Windows
    assert getLastInputPathParameter("C:\\Users\\CongenerManuscripts").endswith(
        "CongenerManuscripts.ris"
    )
