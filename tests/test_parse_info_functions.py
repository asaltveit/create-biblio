from parse_info_functions import (
    getInfoFromFileName,
)


# getInfoFromFileName
def test_author_year_title_format():
    assert getInfoFromFileName(
        "Ammannati 2023 Lupus in fabula - Sulla vera mano di Lupo di Ferrières.pdf"
    ) == (
        {
            "authors": ["Ammannati"],
            "title": "Lupus in fabula - Sulla vera mano di Lupo di Ferrières",
            "year": "2023",
        },
        2,
    )


def test_title_year_format():
    assert getInfoFromFileName("text 2023.pdf") == (
        {"title": "text", "year": "2023"},
        2,
    )


def test_dashes():
    assert getInfoFromFileName("Levitan-DancingEndRope-1985.pdf") == (
        {"title": "Levitan-DancingEndRope-", "year": "1985"},
        2,
    )


def test_multiple_years_format():
    assert getInfoFromFileName(
        "Zurli 1998 Il cod Vindobonensis Palatinus 9401 asterisk dell Anthologia Latina"
    ) == (
        {
            "title": "Il cod Vindobonensis Palatinus",
            "authors": ["Zurli"],
            "year": "1998",
        },
        2,
    )


def test_no_year():
    assert getInfoFromFileName(
        "Zurli Il cod Vindobonensis Palatinus asterisk dell Anthologia Latina"
    ) == (
        {
            "title": "Zurli Il cod Vindobonensis Palatinus asterisk dell Anthologia Latina"
        },
        2,
    )


# Mock tools:
# with mock.patch('os.walk') as mockwalk:
# mockwalk.return_value = [
# ('/foo', ('bar',), ('baz',)),
# ('/foo/bar', (), ('spam', 'eggs')),
# ]

# @mock.patch('os.system')
# def test_my_function(os_system):
# type: (unittest.mock.Mock) -> None
# my_function("/path/to/dir")
# os_system.assert_called_once_with('ls /path/to/dir')

# @pytest.mark.parametrize("earned,spent,expected", [
# (30, 10, 20),
# (20, 2, 18),
# ])

# CI pipeline:
# https://semaphoreci.com/community/tutorials/testing-python-applications-with-pytest

# Faker:
# from faker import Faker
# fake = Faker()

# pip install Faker
