import os
import pytest

from create_biblio import (
    findInfo,
    main,
)

# try/excepts are required for tests to run
# https://stackoverflow.com/questions/54071312/how-to-pass-command-line-argument-from-pytest-to-code
# https://stackoverflow.com/questions/54898578/how-to-keep-unit-tests-and-integrations-tests-separate-in-pytest
# TODO Add unit tests to commit requirements? (?)


@pytest.mark.parametrize(
    "data",
    [
        (
            """Bibliothèque de l'école des chartes
Citer ce document / Cite this document :
Pellegrin Elisabeth. Les manuscrits de Loup de Ferrières. . In: Bibliothèque de l'école des chartes. 1957, tome 115. pp. 5- 31;
doi : https://doi.org/10.3406/bec.1957.449558
https://www.persee.fr/doc/bec_0373-6237_1957_num_115_1_449558
Fichier pdf généré le 15/03/2022""",
            "Update: Using Persee format",
        ),
        (
            """Journal of World Literature 1 (2016) 143–157
Scriptworlds Lost and Found
David Damrosch
Harvard University
ddamrosc@fas.harvard.edu
Abstract
When writing systems spread beyond their language of origin, they bring literacy to formerly oral cultures or intrude on or displace an existing system. The process of learning a new script often entails learning a good deal about the source culture and its literature, sometimes overwriting earlier local traditions, other times creatively stimulating them. This essay looks first at some of the literary consequences of the spread of cuneiform writing in relation to its hieroglyphic and alphabetic rivals in the ancient Near East, and then discusses the advance and later loss of Chinese script in Vietnam and Korea, in the examples of the foundational work of modern Vietnamese literature, Nguyen Du’s The Tale of Kieu, and poems by the modern Korean poet Pak Tujin.
Keywords
scriptworlds – writing systems – cuneiform – Sinosphere – Nguyen Du – Pak Tujin
It was an archaeological map that first led me to think about the shaping force of writing systems on literary cultures. This was a map showing the various sites from which texts of The Epic of Gilgamesh have been recovered. Gilgamesh can fairly be called the first true work of world literature, as it circulated over many centuries far beyond its origins in southern Mesopotamia, and it is the earliest literary text known to have been translated into several languages. Portions of the epic have been found in Hittite and in Hurrian, and the Akkadian original itself is an expansive adaptation of an earlier Sumerian song cycle commissioned by King Shulgi of Ur (r. 2094–2047bce), the world’s first known patron of literature. Gilgamesh appears, in fact, to have been the most popular literary hero of the ancient Near East; texts and related artifacts
© koninklijke brill nv, leiden, 2016 | doi: 10.1163/24056480-00102002""",
            "Update: Using Brill format",
        ),
        (
            """Dancing at the End of the Rope: Optatian Porfyry and the Field of Roman Verse
Author(s): W. Levitan
Source: Transactions of the American Philological Association (1974-2014), 1985, Vol. 115
(1985), pp. 245-269
Published by: The Johns Hopkins University Press
Stable URL: https://www.jstor.org/stable/284201
REFERENCES
Linked references are available on JSTOR for this article:
https://www.jstor.org/stable/284201?seq=1&cid=pdf-
reference#references_tab_contents
You may need to log in to JSTOR to access the linked references.
JSTOR is a not-for-profit service that helps scholars, researchers, and students discover, use, and build upon a wide
range of content in a trusted digital archive. We use information technology and tools to increase productivity and
facilitate new forms of scholarship. For more information about JSTOR, please contact support@jstor.org.
Your use of the JSTOR archive indicates your acceptance of the Terms & Conditions of Use, available at """,
            "Update: Using JSTOR format",
        ),
        (
            """Rapid #: -23496420
CROSS REF ID: 708350
LENDER: NJR (Rutgers University) :: Main Library
BORROWER: MDY (Middlebury College) :: Davis Family Library
TYPE: Article CC:CCL
JOURNAL TITLE: Giornale italiano di filologia
USER JOURNAL TITLE: GIORNALE ITALIANO DI FILOLOGIA
ARTICLE TITLE: Il cod. Vindobonensis Palatinus 9401* dell'Anthologia Latina
ARTICLE AUTHOR: Zurli, Loriano
VOLUME: 50
ISSUE:
MONTH:
YEAR: 1998
PAGES: 211-237
ISSN: 0017-0461
OCLC #:
Processed by RapidX: 11/12/2024 10:51:39 AM
This material may be protected by copyright law (Title 17 U.S. Code)""",
            "Update: Didn't identify a known format (from JSTOR or Persee or Brill) - will use a general format",
        ),
    ],
)
def test_findInfo_prints(tmp_path, capsys, data):
    # Will this fail if run on Windows?
    f = tmp_path / "mydir/output.pdf"
    f.parent.mkdir()
    f.touch()
    f.write_text(data[0])
    try:
        findInfo(f)
        captured = capsys.readouterr().out
        assert captured == data[1]
    except Exception as e:
        print("test_findInfo_unit exception, ", e)


# Pay attention to counts, additional prints needed
def set_up_test_directory(tmp_path):
    # paths directory
    # Typical top-level PDF
    pdf1 = tmp_path / "paths/myFile.pdf"
    pdf1.parent.mkdir()
    pdf1.touch()
    pdf1.write_text("jknjknjkn ISBN \n Author(s): John")
    # Top-level PDF with dashes
    pdf2 = tmp_path / "paths/my-file-2.pdf"
    pdf2.touch()
    pdf2.write_text(
        """Bibliothèque de l'école des chartes
Citer ce document / Cite this document :
Pellegrin Elisabeth. Les manuscrits de Loup de Ferrières. . In: Bibliothèque de l'école des chartes. 1957, tome 115. pp. 5- 31;
doi : https://doi.org/10.3406/bec.1957.449558
https://www.persee.fr/doc/bec_0373-6237_1957_num_115_1_449558
Fichier pdf généré le 15/03/2022"""
    )
    # Subfolder PDF starting with a dash
    pdf3 = tmp_path / "paths/innerFolder/-testFile3.pdf"
    pdf3.parent.mkdir()
    pdf3.touch()
    # Subfolder not a pdf
    docx1 = tmp_path / "paths/innerFolder/testFile4.docx"
    docx1.touch()

    # no-path directory
    # Typical top-level PDF
    pdf4 = tmp_path / "no-paths/myfile.py"
    pdf4.parent.mkdir()
    pdf4.touch()
    # Top-level PDF with dashes
    pdf5 = tmp_path / "no-paths/my-file-2.txt"
    pdf5.touch()
    # Subfolder PDF starting with a dash
    pdf6 = tmp_path / "no-paths/innerFolder/-testFile3.pdf"
    pdf6.parent.mkdir()
    pdf6.touch()


no_path_prints = [
    "Update: Input path exists",
    "Update: Searching for PDFs",
    "Update: Found 0 paths",
    "Update: No output files created",
    "Update: Finished",
]
# Path for "Update: Finding info for - " will be difficult (no tmp_file out here)
with_path_prints = [
    "Update: Input path exists",
    "Update: Searching for PDFs",
    "Update: Found 2 paths",
    "Update: Finding info for - ",
    "Update: Finding info for - ",
    "Update: Using Persee format",
    "Update: Didn't identify a known format (from JSTOR or Persee or Brill) - will use a general format",
    "Update: Collecting info from file name",
    "Update: Author found",
    "Update: Article title found",
    "Update: Parsing info from a general format",
    "Update: PDF is from Persee",
    "Update: There were 0 PDFs from JSTOR",
    "Update: There were 1 PDFs from Persee",
    "Update: There were 1 PDFs with unknown format",
    "Update: Searched file names for info for 1 PDFs",
    "Update: Creating RIS file",
    "Update: Successfully wrote to RIS file",
    "Updated: Finished",
]

# @pytest.mark.integration  # Marks as integration test
@pytest.mark.parametrize(
    "inputPath",
    [
        ["paths", "", "paths.ris", with_path_prints],
        ["paths", "output.ris", "output.ris", with_path_prints],
        ["no-paths", "output.ris", "output.ris", no_path_prints],
        ["no-paths", "", "no-paths.ris", no_path_prints],
    ],
)
def test_main_prints(tmp_path, capsys, monkeypatch, inputPath):
    set_up_test_directory(tmp_path)
    # Always need a try+except to avoid pymupdf error opening file
    try:
        with monkeypatch.context() as m:
            m.setattr(
                "sys.argv",
                [
                    "create_biblio.py",
                    "--inputPath",
                    str(tmp_path / inputPath[0]),
                    "--outputPath",
                    str(tmp_path / inputPath[1]),
                ],
            )
            main()
            captured = capsys.readouterr().out
            for p in inputPath[3]:
                assert p in captured
    except Exception as e:
        print("test_main_prints exception, ", e)


# @pytest.mark.integration  # Marks as integration test
@pytest.mark.parametrize(
    "inputPath",
    [
        ["paths", "", "paths.ris"],
        ["paths", "output.ris", "output.ris"],
        ["no-paths", "output.ris", "output.ris"],
        ["no-paths", "", "no-paths.ris"],
    ],
)
def test_main_output(tmp_path, capsys, monkeypatch, inputPath):
    set_up_test_directory(tmp_path)
    try:
        with monkeypatch.context() as m:
            m.setattr(
                "sys.argv",
                [
                    "create_biblio.py",
                    "--inputPath",
                    str(tmp_path / inputPath[0]),
                    "--outputPath",
                    str(tmp_path / inputPath[1]),
                ],
            )
            main()
            captured = capsys.readouterr().out
            if "No output files created" not in captured:
                assert os.path.isfile(
                    os.path.join(str(tmp_path), inputPath[0], inputPath[2])
                )
            else:
                assert not os.path.isfile(
                    os.path.join(str(tmp_path), inputPath[0], inputPath[2])
                )
    except Exception as e:
        print("test_main_output exception, ", e)
