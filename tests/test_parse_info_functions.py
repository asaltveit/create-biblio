import pytest
import pymupdf
import pathlib
from parse_info_functions import (
    getInfoFromFileName,
    parseInfoGeneral,
    collectYearManuscriptCode,
    collectPageNumbers,
    findInfoJSTOR,
    findInfoPersee,
    findInfoBrill,
    getInfoGeneral,
)

# collectPageNumbers
@pytest.mark.parametrize(
    "file_name,output,expectedOutput,expectedPrint",
    [
        (
            "Zurli 1998 Il cod Vindobonensis Palatinus 9401 asterisk dell Anthologia Latina",
            {},
            {},
            "Warn: pp found in filename but unable to parse",
        ),
        (
            "De Rossi ICUR II pp 244-9 from Paris Lat 8071.pdf",
            {},
            {"start_page": "244", "end_page": "249"},
            "Update: Found page numbers",
        ),
        (
            "De Rossi ICUR II pp 56-7 from Paris Lat 8071.pdf",
            {"authors": ["Blake"]},
            {"authors": ["Blake"], "start_page": "56", "end_page": "57"},
            "Update: Found page numbers",
        ),
    ],
)
def test_collectPageNumbers(file_name, output, expectedOutput, expectedPrint, capsys):
    result = collectPageNumbers(file_name, output)
    captured = capsys.readouterr().out
    assert result == expectedOutput
    assert captured.strip() == expectedPrint


# collectYearManuscriptCode
@pytest.mark.parametrize(
    "file_name,output,expected,numPrints",
    [
        (
            "Ammannati 2023 Lupus in fabula - Sulla vera mano di Lupo di Ferrières",
            {},
            {"year": "2023"},
            1,
        ),
        (
            "Zurli 1998 Il cod Vindobonensis Palatinus 9401 asterisk dell Anthologia Latina",
            {},
            {"year": "1998", "number_of_volumes": "9401"},
            2,
        ),
        ("Levitan-DancingEndRope-1985", {}, {"year": "1985"}, 1),
        ("Les manuscrits de Loup de Ferrières", {}, {}, 0),
    ],
)
def test_collectYearManuscriptCode(file_name, output, expected, numPrints, capsys):
    result = collectYearManuscriptCode(file_name, output)
    captured = capsys.readouterr().out
    assert result == expected
    # Splitting on the 'U' adds an extra empty item to the list for the first occurence
    # captured = ['Update: Year foundUpdate: Manuscript code found']
    assert len(captured.split("U")[1:]) == numPrints


def test_dashes():
    assert getInfoFromFileName("Levitan-DancingEndRope-1985.pdf") == (
        {"title": "Levitan-DancingEndRope-", "year": "1985"},
        2,
    )


def test_title_year_format():
    assert getInfoFromFileName("text 2023.pdf") == (
        {"title": "text", "year": "2023"},
        2,
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


def test_findInfoPersee(tmp_path, capsys):
    f1 = tmp_path / "mydir/myfile.pdf"
    f1.parent.mkdir()  # create a directory "mydir" in temp folder (which is the parent directory of "myfile"
    f1.touch()  # create a file "myfile" in "mydir"
    f1.write_text(
        """Bibliothèque de l'école des chartes
Citer ce document / Cite this document :
Pellegrin Elisabeth. Les manuscrits de Loup de Ferrières. . In: Bibliothèque de l'école des chartes. 1957, tome 115. pp. 5- 31;
doi : https://doi.org/10.3406/bec.1957.449558
https://www.persee.fr/doc/bec_0373-6237_1957_num_115_1_449558
Fichier pdf généré le 15/03/2022"""
    )

    fs = [
        [
            f1,
            "mydir/myfile.pdf",
            (
                {
                    "title": "Les manuscrits de Loup de Ferrières",
                    "issn": "6547",
                    "issue": "20",
                    "year": "1957",
                    "start_page": "5",
                    "end_page": "31",
                    "volume": "115",
                    "journal_name": "Bibliothèque de l'école des chartes",
                    "doi": "https://doi.org/10.3406/bec.1957.449558",
                    "authors": ["Elisabeth Pellegrin"],
                    "type_of_reference": "JOUR",
                },
                2,
            ),
        ],
    ]
    # i used in pathlib.Path(fs[i][0])
    i = 0
    try:
        for file in fs:
            doc = pymupdf.open(file[0])
            assert findInfoPersee(doc[0], file[1]) == file[2]
            i += 1
        captured = capsys.readouterr().out
        assert "Update: PDF is from Persee" == captured
    except Exception:
        print(pymupdf.TOOLS.mupdf_warnings())
        pth = pathlib.Path(fs[i][0])
        buffer = pth.read_bytes()
        print(buffer[:200])  # shows the first few hundred bytes of the file
        # save the file to another place for later investigation
        out = open(tmp_path / "persee-test.pdf", "wb")
        out.write(buffer)
        out.close()


@pytest.mark.parametrize(
    "inputLines,output,expected",
    [
        no_infolines,
        infolines_middlebury_all_caps,
    ],
)  # What's wrong here?
def test_parseInfoGeneral(inputLines, output, expected, capsys):
    assert parseInfoGeneral(inputLines, output) == expected
    captured = capsys.readouterr().out
    assert "Update: Parsing info from a general format" == captured.strip()


# findInfoJSTOR - TODO test if title isn't found
def test_findInfoJSTOR(tmp_path, capsys):
    # TODO What needs to be tested here?
    f1 = tmp_path / "mydir/myfile.pdf"
    f1.parent.mkdir()  # create a directory "mydir" in temp folder (which is the parent directory of "myfile"
    f1.touch()  # create a file "myfile" in "mydir"
    f1.write_text(
        "hgjfghfkfgkf  ISSN: 6547 \n Title: John \n\n Issue: 20 What you are looking at are just Windows explorer views to your files. That's no proof that those are valid"
    )
    # TODO A way to make some more realistic PDFs? mv/duplicate?
    f2 = tmp_path / "mydir/myfile2.pdf"
    f2.touch()
    f2.write_text("jknjknjkn ISBN \n Author(s): John")
    fs = [
        [
            f1,
            "mydir/myfile.pdf",
            (
                {
                    "title": "John",
                    "issn": "6547",
                    "issue": "20",
                    "type_of_reference": "JOUR",
                },
                2,
            ),
        ],
        [
            f2,
            "mydir/myfile2.pdf",
            ({"title": "myfile", "type_of_reference": "BOOK", "authors": ["John"]}, 2),
        ],
    ]

    i = 0
    try:
        for file in fs:
            doc = pymupdf.open(file[0])
            assert findInfoJSTOR(doc[0], file[1]) == file[2]
            i += 1
        captured = capsys.readouterr().out
        assert "Update: PDF is from JSTOR" == captured
    except Exception:
        print(pymupdf.TOOLS.mupdf_warnings())
        pth = pathlib.Path(fs[i][0])
        buffer = pth.read_bytes()
        print(buffer[:200])  # shows the first few hundred bytes of the file
        # save the file to another place for later investigation
        out = open(tmp_path / "JSTOR-test.pdf", "wb")
        out.write(buffer)
        out.close()


# TODO test if title isn't found
def test_findInfoBrill(tmp_path, capsys):
    # TODO What needs to be tested here?
    f1 = tmp_path / "mydir/myfile.pdf"
    f1.parent.mkdir()
    f1.touch()
    f1.write_text(
        "Journal of World Literature 1 (2016) 143–157 \n\n\n Scriptworlds Lost and Found \n\t David Damrosch \n\t\t Harvard University\nddamrosc@fas.harvard.edu"
    )
    # TODO A way to make some more realistic PDFs? mv/duplicate?
    fs = [
        [
            f1,
            "mydir/myfile.pdf",
            (
                {
                    "title": "Scriptworlds Lost and Found",
                    "journal_name": "Journal of World Literature 1",
                    "start_page": "143",
                    "end_page": "157",
                    "year": "2016",
                    "authors": ["David Damrosch"],
                    "type_of_reference": "JOUR",
                },
                2,
            ),
        ],
    ]

    i = 0
    try:
        for file in fs:
            doc = pymupdf.open(file[0])
            assert findInfoBrill(doc[0], file[1]) == file[2]
            i += 1
        captured = capsys.readouterr().out
        assert "Update: PDF is from Brill" == captured

    except Exception:
        print(pymupdf.TOOLS.mupdf_warnings())
        pth = pathlib.Path(fs[i][0])
        buffer = pth.read_bytes()
        print(buffer[:200])  # shows the first few hundred bytes of the file
        # save the file to another place for later investigation
        out = open(tmp_path / "brill-test.pdf", "wb")
        out.write(buffer)
        out.close()


# TODO Make all these tests more robust
# getInfoGeneral - TODO test if title isn't found
def set_up_test_directory(tmp_path):
    # Typical top-level PDF
    pdf1 = tmp_path / "mydir/myfile.pdf"
    pdf1.parent.mkdir()
    pdf1.touch()
    pdf1.write_text("Title: test title\nAuthor: Test Athor\nYear: 1985\nIssue: 20")
    # Top-level PDF with dashes
    pdf2 = tmp_path / "mydir/my-file-2.pdf"
    pdf2.touch()
    pdf2.write_text(
        """Bibliothèque de l'école des chartes
Citer ce document / Cite this document :
Pellegrin Elisabeth. Les manuscrits de Loup de Ferrières. . In: Bibliothèque de l'école des chartes. 1957, tome 115. pp. 5- 31;
doi : https://doi.org/10.3406/bec.1957.449558
https://www.persee.fr/doc/bec_0373-6237_1957_num_115_1_449558
Fichier pdf généré le 15/03/2022"""
    )

    fs = [
        [pdf1, ["Title: test title", "Author: Test Athor", "Year: 1985", "Issue: 20"]],
        [
            pdf2,
            [
                "Citer ce document / Cite this document :Pellegrin Elisabeth. Les manuscrits de Loup de Ferrières. . In: Bibliothèque de l'école des chartes. 1957, tome 115. pp. 5- 31;",
                "doi : https://doi.org/10.3406/bec.1957.449558",
            ],
        ],
    ]
    return fs


# Doesn't have prints
def test_getInfoGeneral(tmp_path):
    fs = set_up_test_directory(tmp_path)

    i = 0
    try:
        for file in fs:
            doc = pymupdf.open(file[0])
            assert getInfoGeneral(doc[0]) == file[1]
            i += 1

    except Exception:
        print(pymupdf.TOOLS.mupdf_warnings())
        pth = pathlib.Path(fs[i][0])
        buffer = pth.read_bytes()
        print(buffer[:200])  # shows the first few hundred bytes of the file
        # save the file to another place for later investigation
        out = open(tmp_path / "general-infolines--test.pdf", "wb")
        out.write(buffer)
        out.close()


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
# pymupdf open - https://github.com/pymupdf/PyMuPDF/issues/612
# mocking issues - https://stackoverflow.com/questions/65728499/python-pytest-mocking-three-functions
