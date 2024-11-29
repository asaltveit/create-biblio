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
