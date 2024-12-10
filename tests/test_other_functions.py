# Test:
# getCommandLineArguments,
# findInfo, createBiblio

import pytest

from other_functions import (
    createBiblio,
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
