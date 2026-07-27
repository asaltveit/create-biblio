import pytest

from line_features import (
    extract_patterns,
    fuzzy_match_label,
    features_to_crf_dict,
    line_to_features,
)
from line_classifier import merge_metadata, labels_to_output, maybe_apply_ml_fallback


def test_fuzzy_match_label_author_variants():
    field, value = fuzzy_match_label("ARTICLE AUTHOR:Zurli, Loriano")
    assert field == "authors"
    assert value == "Zurli, Loriano"


def test_fuzzy_match_label_typo():
    field, value = fuzzy_match_label("Artide Author: Jane Doe")
    assert field == "authors"
    assert value == "Jane Doe"


def test_extract_patterns():
    text = "Source: Journal (1998), pp. 211-237, doi: 10.1234/example"
    patterns = extract_patterns(text)
    assert patterns["year"] == "1998"
    assert patterns["start_page"] == "211"
    assert patterns["end_page"] == "237"
    assert patterns["doi"] == "10.1234/example"


def test_line_to_features():
    line = {
        "text": "Author(s): John Doe",
        "font": "Helvetica-Bold",
        "size": 12,
        "y0": 50,
    }
    features = line_to_features(line, page_height=800, max_font_size=14)
    assert features["is_bold"] is True
    assert features["has_colon"] is True
    assert features_to_crf_dict(features)["fuzzy_label"] == "authors"


def test_merge_metadata_fills_gaps_only():
    rule = {"title": "Existing", "year": "1998"}
    ml = {"title": "Other", "authors": ["Jane Doe"]}
    merged = merge_metadata(rule, ml)
    assert merged["title"] == "Existing"
    assert merged["authors"] == ["Jane Doe"]


def test_merge_metadata_overwrite():
    rule = {"title": "Existing"}
    ml = {"title": "Other", "authors": ["Jane Doe"]}
    merged = merge_metadata(rule, ml, overwrite=True)
    assert merged["title"] == "Other"


def test_labels_to_output():
    lines = [
        {"text": "ARTICLE TITLE:Sample Title"},
        {"text": "ARTICLE AUTHOR:Smith, John"},
    ]
    output = labels_to_output(lines, ["LABEL", "LABEL"])
    assert output["title"] == "Sample Title"
    assert output["authors"] == ["Smith", "John"]


def test_maybe_apply_ml_fallback_skips_when_complete():
    output = {"title": "Done", "authors": ["A"]}
    result = maybe_apply_ml_fallback(output, [], [], use_ml=True)
    assert result == output


def test_get_command_line_use_ml_flag():
    from other_functions import getCommandLineArguments

    result = getCommandLineArguments(["--inputPath", "/tmp", "--use-ml"])
    assert result[2] is True
