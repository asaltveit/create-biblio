#!/usr/bin/env python3
"""Train the line-level CRF classifier from labeled JSON training data."""

import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from line_features import line_to_features, features_to_crf_dict
from line_classifier import MODEL_DIR, MODEL_PATH

TRAINING_DATA = os.path.join(ROOT, "data", "training_lines.json")


def load_training_documents(path=TRAINING_DATA):
    with open(path, encoding="utf-8") as handle:
        return json.load(handle)


def documents_to_xy(documents):
    x_docs = []
    y_docs = []
    for document in documents:
        x_sentence = []
        y_sentence = []
        lines = document["lines"]
        max_font = max(line.get("size", 0) for line in lines) or 1
        page_height = max(line.get("y0", 0) for line in lines) + 200
        for line in lines:
            features = line_to_features(line, page_height=page_height, max_font_size=max_font)
            x_sentence.append(features_to_crf_dict(features))
            y_sentence.append(line["label"])
        x_docs.append(x_sentence)
        y_docs.append(y_sentence)
    return x_docs, y_docs


def train_and_save():
    try:
        import sklearn_crfsuite
    except ImportError as exc:
        raise SystemExit(
            "Install ML dependencies first: pip install -r requirements-ml.txt"
        ) from exc

    documents = load_training_documents()
    x_train, y_train = documents_to_xy(documents)

    crf = sklearn_crfsuite.CRF(
        algorithm="lbfgs",
        c1=0.1,
        c2=0.1,
        max_iterations=200,
        all_possible_transitions=True,
    )
    crf.fit(x_train, y_train)

    os.makedirs(MODEL_DIR, exist_ok=True)
    import joblib

    joblib.dump(crf, MODEL_PATH)
    print(f"Saved model to {MODEL_PATH}")
    print(f"Labels: {crf.classes_}")


if __name__ == "__main__":
    train_and_save()
