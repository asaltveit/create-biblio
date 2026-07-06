import pytest

from line_classifier import predict_fields, load_crf_model
from line_features import structured_lines_to_features


@pytest.mark.integration
def test_load_crf_model():
    model = load_crf_model()
    assert model is not None


@pytest.mark.integration
def test_predict_fields_from_training_example():
    lines = [
        {"text": "ARTICLE TITLE:Sample Article", "font": "Helvetica-Bold", "size": 12, "y0": 40},
        {"text": "ARTICLE AUTHOR:Doe, Jane", "font": "Helvetica", "size": 10, "y0": 60},
    ]
    features = structured_lines_to_features(lines, page_height=200)
    output = predict_fields(lines, features)
    assert "title" in output or "authors" in output
