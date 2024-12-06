import sys
import pytest

from create_biblio import (
    findInfo,
    main,
)

# TODO Add unit tests to commit requirements?

# How to mock inner functions?
# Should it be unit test or integration test?
# Should there be both?
def test_findInfo_unit(tmp_path):
    findInfo(tmp_path)
    # pass


# https://stackoverflow.com/questions/54898578/how-to-keep-unit-tests-and-integrations-tests-separate-in-pytest
@pytest.mark.integtest  # Marks as integration test
def test_findInfo_integration(tmp_path):
    findInfo(tmp_path)


# TODO: Not unit test, an integration test:

# https://stackoverflow.com/questions/54071312/how-to-pass-command-line-argument-from-pytest-to-code
@pytest.mark.parametrize("inputPath", ["spam", "eggs", "bacon"])
@pytest.mark.integtest  # Marks as integration test
def test_main_no_output_file(tmp_path, monkeypatch, inputPath):
    with monkeypatch.context() as m:
        m.setattr(sys, "argv", ["InputPath", inputPath])
        main()


@pytest.mark.integtest  # Marks as integration test
@pytest.mark.parametrize("outputPath", ["spam", "eggs", "bacon"])
@pytest.mark.parametrize("inputPath", ["spam", "eggs", "bacon"])
def test_main_with_output_file(tmp_path, monkeypatch, inputPath, outputPath):
    with monkeypatch.context() as m:
        m.setattr(sys, "argv", ["InputPath", inputPath])
        m.setattr(sys, "argv", ["InputPath", outputPath])
        main()
