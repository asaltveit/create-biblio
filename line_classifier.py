import os
import re

MODEL_DIR = os.path.join(os.path.dirname(__file__), "models", "line_crf")
MODEL_PATH = os.path.join(MODEL_DIR, "line_crf.joblib")

_crf_model = None


def _missing_required_fields(output):
    return not output.get("title") or not output.get("authors")


def merge_metadata(rule_dict, ml_dict, overwrite=False):
    merged = dict(rule_dict)
    for key, value in ml_dict.items():
        if value in (None, "", []):
            continue
        if overwrite or key not in merged or merged[key] in (None, "", []):
            merged[key] = value
    return merged


def _apply_label_to_output(label, text, output):
    text = text.strip()
    if not text or label in ("LABEL", "IGNORE"):
        return
    if label == "AUTHOR":
        authors = [author.strip() for author in re.split(r",\s*", text) if author.strip()]
        if authors:
            output["authors"] = authors
    elif label == "TITLE":
        output["title"] = text
    elif label == "JOURNAL":
        output["journal_name"] = text.split("(")[0].strip()
    elif label == "YEAR":
        year_match = re.search(r"\b(19|20)\d{2}\b", text)
        if year_match:
            output["year"] = year_match.group(0)
    elif label == "VOLUME":
        output["volume"] = re.sub(r"[^\d]", "", text) or text
    elif label == "ISSUE":
        output["issue"] = text
    elif label == "PAGES":
        pages_match = re.search(r"(\d{1,6})\s*[-–—]\s*(\d{1,6})", text)
        if pages_match:
            output["start_page"] = pages_match.group(1)
            output["end_page"] = pages_match.group(2)
    elif label == "DOI":
        output["doi"] = text
    elif label == "ISSN":
        output["issn"] = text
    elif label == "PUBLISHER":
        publisher = text
        if " Stable" in publisher:
            publisher = publisher.split(" Stable")[0].strip()
        if " URL" in publisher:
            publisher = publisher.split(" URL")[0].strip()
        output["publisher"] = publisher


def labels_to_output(lines, predicted_labels):
    from line_features import fuzzy_match_label

    output = {"type_of_reference": "JOUR"}
    for line, label in zip(lines, predicted_labels):
        text = line.get("text", "") if isinstance(line, dict) else line
        if label == "LABEL" and ":" in text:
            field_key, value = fuzzy_match_label(text)
            if field_key == "authors":
                _apply_label_to_output("AUTHOR", value, output)
            elif field_key == "title":
                _apply_label_to_output("TITLE", value, output)
            elif field_key == "journal_name":
                _apply_label_to_output("JOURNAL", value, output)
            elif field_key == "year":
                _apply_label_to_output("YEAR", value, output)
            elif field_key == "volume":
                _apply_label_to_output("VOLUME", value, output)
            elif field_key == "issue":
                _apply_label_to_output("ISSUE", value, output)
            elif field_key == "pages":
                _apply_label_to_output("PAGES", value, output)
            elif field_key == "doi":
                _apply_label_to_output("DOI", value, output)
            elif field_key == "issn":
                _apply_label_to_output("ISSN", value, output)
            elif field_key == "publisher":
                _apply_label_to_output("PUBLISHER", value, output)
            continue
        _apply_label_to_output(label, text, output)
    return output


def load_crf_model():
    global _crf_model
    if _crf_model is not None:
        return _crf_model
    if not os.path.isfile(MODEL_PATH):
        raise FileNotFoundError(
            f"ML model not found at {MODEL_PATH}. "
            "Run scripts/train_line_classifier.py to create it."
        )
    try:
        import joblib
    except ImportError as exc:
        raise ImportError(
            "joblib is required for --use-ml (installed with sklearn-crfsuite)."
        ) from exc
    _crf_model = joblib.load(MODEL_PATH)
    return _crf_model


def predict_fields(structured_lines, feature_dicts):
    model = load_crf_model()
    from line_features import features_to_crf_dict

    x = [[features_to_crf_dict(f) for f in feature_dicts]]
    predicted = model.predict(x)[0]
    return labels_to_output(structured_lines, predicted)


def maybe_apply_ml_fallback(output, structured_lines, feature_dicts, use_ml=False):
    if not use_ml or not _missing_required_fields(output):
        return output
    if not structured_lines:
        return output
    try:
        ml_output = predict_fields(structured_lines, feature_dicts)
        return merge_metadata(output, ml_output)
    except (ImportError, FileNotFoundError) as exc:
        print(f"Warn: ML fallback unavailable: {exc}")
        return output
