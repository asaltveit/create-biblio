import pytest
from faker import Faker
import fitz
from parse_info_functions import (
    getInfoFromFileName,
    parseInfoGeneral,
    collectYearManuscriptCode,
)

fake = Faker()

# collectYearManuscriptCode
@pytest.mark.parametrize(
    "file_name,output,expected",
    [
        (
            "Ammannati 2023 Lupus in fabula - Sulla vera mano di Lupo di Ferrières",
            {},
            {"year": "2023"},
        ),
        (
            "Zurli 1998 Il cod Vindobonensis Palatinus 9401 asterisk dell Anthologia Latina",
            {},
            {"year": "1998", "number_of_volumes": 9401},
        ),
        ("Levitan-DancingEndRope-1985", {}, {"year": 1985}),  # fails
        ("Les manuscrits de Loup de Ferrières", {}, {}),  # fails
    ],
)
def test_collectYearManuscriptCode(file_name, output, expected):
    assert collectYearManuscriptCode(file_name, output) == expected


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


def test_multiple_numbers_format():
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


# parseInfoGeneral
infolines_middlebury_all_caps_expected = {
    "type_of_reference": "JOUR",
    "journal_name": "Giornale italiano di filologia",
    "authors": ["Zurli", "Loriano"],
    "title": "Il cod Vindobonensis Palatinus",
    "volume": "50",
    "year": "1998",
    "start_page": "211",
    "end_page": "237",
}
infolines_middlebury_all_caps = (
    [
        "Rapid #: -23496420CROSS REF ID:708350LENDER:NJR (Rutgers University) :: Main LibraryBORROWER:MDY (Middlebury College) :: Davis Family Library",
        "TYPE:Article CC:CCL",
        "JOURNAL TITLE:Giornale italiano di filologia",
        "GIORNALE ITALIANO DI FILOLOGIA",
        "ARTICLE TITLE:Il cod. Vindobonensis Palatinus 9401* dell'Anthologia Latina",
        "ARTICLE AUTHOR:Zurli, Loriano",
        "VOLUME:50",
        "ISSUE:",
        "",
        "YEAR:1998",
        "PAGES:211-237",
    ],
    {"authors": ["Zurli"], "title": "Il cod Vindobonensis Palatinus", "year": "1998"},
    infolines_middlebury_all_caps_expected,
)
infolines_jstor = [
    "Some Medieval Advertisements of Rome ",
    "Author(s): J. R. Hulbert ",
    "Source: Modern Philology , May, 1923, Vol. 20, No. 4 (May, 1923), pp. 403-424  Published by: The University of Chicago Press Stable URL: https://www.jstor.org/stable/433697JSTOR is a not-for-profit service that helps scholars, researchers, and students discover, use, and build upon a wide range of content in a trusted digital archive. We use information technology and tools to increase productivity and facilitate new forms of scholarship. For more information about JSTOR, please contact support@jstor.org.  Your use of the JSTOR archive indicates your acceptance of the Terms & Conditions of Use, available at ",
]
no_infolines = ([], {"title": "blah, blah, blah"}, {"title": "blah, blah, blah"})
# Persee - not working
# infolines_persee_output = {'authors': ['Pellegrin'], 'title': 'Les manuscrits de Loup de Ferrières', 'year': '1957'}
# infolines_persee = (["Bibliothèque de l'école deschartesLes manuscrits de Loup de Ferrières.A propos du ms. Orléans 162 (139) corrigé de sa main.Elisabeth PellegrinCiter ce document / Cite this document :Pellegrin Elisabeth. Les manuscrits de Loup de Ferrières. . In: Bibliothèque de l'école des chartes. 1957, tome 115. pp. 5-31;doi : https://doi.org/10.3406/bec.1957.449558", ''], infolines_persee_output, {'authors': ['Pellegrin'], 'title': 'Les manuscrits de Loup de Ferrières', 'year': '1957', 'type_of_reference': 'JOUR'})
# infolines_persee_no_output = (["Bibliothèque de l'école deschartesLes manuscrits de Loup de Ferrières.A propos du ms. Orléans 162 (139) corrigé de sa main.Elisabeth PellegrinCiter ce document / Cite this document :Pellegrin Elisabeth. Les manuscrits de Loup de Ferrières. . In: Bibliothèque de l'école des chartes. 1957, tome 115. pp. 5-31;doi : https://doi.org/10.3406/bec.1957.449558", ''], {}, {'authors': ['Pellegrin'], 'title': 'Les manuscrits de Loup de Ferrières', 'year': '1957', 'type_of_reference': 'JOUR'})


@pytest.mark.parametrize(
    "inputLines,output,expected",
    [
        no_infolines,
        infolines_middlebury_all_caps,
    ],
)
def test_parseInfoGeneral(inputLines, output, expected):
    assert parseInfoGeneral(inputLines, output) == expected


JSTOR_title = (fitz.open(), ({}, 1))
JSTOR_no_title = ({}, ({}, 2))
f1 = ""
f2 = ""

# findInfoJSTOR
def set_up_test(tmp_path):
    f1 = tmp_path / "mydir/myfile.pdf"
    f1.parent.mkdir()  # create a directory "mydir" in temp folder (which is the parent directory of "myfile"
    f1.touch()  # create a file "myfile" in "mydir"
    f2 = tmp_path / "mydir/myfile2.pdf"
    f2.parent.mkdir()
    f2.touch()
    f2.write_text("ISBN \n Author(s):")
    global JSTOR_title
    global JSTOR_no_title
    JSTOR_no_title = (fitz.open("mydir/myfile")[0], ({"title": "myfile"}, 2))
    JSTOR_title = (fitz.open("mydir/myfile2")[0], ({"title": "myfile"}, 2))


def test_findInfoJSTOR(tmp_path):
    f1 = tmp_path / "mydir/myfile.pdf"
    f1.parent.mkdir()  # create a directory "mydir" in temp folder (which is the parent directory of "myfile"
    f1.touch()  # create a file "myfile" in "mydir"
    # JSTOR_no_title = ((fitz.open('mydir/myfile')[0], ({'title': 'myfile'}, 2)))
    # doc = fitz.open("mydir/myfile.pdf")
    # assert findInfoJSTOR(doc[0], "mydir/myfile.pdf") == ({"title": "myfile"}, 2)


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

# Might be more for backend objects:
# https://factoryboy.readthedocs.io/en/stable/

# tmp_dir:  https://stackoverflow.com/questions/36070031/creating-a-temporary-directory-in-pytest
# fitz open - https://github.com/pymupdf/PyMuPDF/issues/612
# mocking issues - https://stackoverflow.com/questions/65728499/python-pytest-mocking-three-functions
