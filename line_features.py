import re
from difflib import SequenceMatcher

from constants import (
    DOI_PATTERN,
    END_KEYWORDS,
    FUZZY_LABEL_THRESHOLD,
    ISSN_PATTERN,
    KEYWORDS,
    LABEL_FIELD_MAP,
    PAGES_PATTERN,
    TOME_PATTERN,
    VOLUME_PATTERN,
    YEAR_PATTERN,
)


def _normalize_label(text):
    return text.strip().lower().rstrip(":")


def fuzzy_match_label(line):
    """Return (field_key, value) if line starts with a known label, else (None, None)."""
    if ":" not in line:
        return None, None
    label_part, value = line.split(":", 1)
    normalized = _normalize_label(label_part)
    if normalized in LABEL_FIELD_MAP:
        return LABEL_FIELD_MAP[normalized], value.strip()
    best_field = None
    best_score = 0.0
    for label_key, field_key in LABEL_FIELD_MAP.items():
        score = SequenceMatcher(None, normalized, label_key).ratio()
        if score > best_score:
            best_score = score
            best_field = field_key
    if best_score >= FUZZY_LABEL_THRESHOLD:
        return best_field, value.strip()
    for keyword in KEYWORDS:
        if line.startswith(keyword):
            normalized_kw = _normalize_label(keyword)
            return LABEL_FIELD_MAP.get(normalized_kw), value.strip()
    return None, None


def is_end_line(text):
    return text.startswith(tuple(END_KEYWORDS))


def is_keyword_line(text):
    return text.startswith(tuple(KEYWORDS))


def extract_patterns(text):
    """Extract bibliographic patterns from any line text."""
    found = {}
    doi_match = re.search(DOI_PATTERN, text)
    if doi_match:
        found["doi"] = doi_match.group(0).rstrip(".,;")
    issn_match = re.search(ISSN_PATTERN, text)
    if issn_match:
        found["issn"] = issn_match.group(0)
    year_match = re.search(YEAR_PATTERN, text)
    if year_match:
        found["year"] = year_match.group(0)
    pages_match = re.search(PAGES_PATTERN, text, re.IGNORECASE)
    if pages_match:
        found["start_page"] = pages_match.group(1)
        found["end_page"] = pages_match.group(2)
    volume_match = re.search(VOLUME_PATTERN, text, re.IGNORECASE)
    if volume_match:
        found["volume"] = volume_match.group(1)
    tome_match = re.search(TOME_PATTERN, text, re.IGNORECASE)
    if tome_match:
        found["volume"] = tome_match.group(1)
    return found


def line_to_features(line, page_height=None, max_font_size=None):
    text = line.get("text", "")
    font = line.get("font", "")
    size = line.get("size", 0)
    y0 = line.get("y0", 0.0)
    lower = text.lower()
    patterns = extract_patterns(text)
    relative_size = size / max_font_size if max_font_size else 1.0
    header_region = y0 <= (page_height * 0.35) if page_height else True
    return {
        "text": text,
        "lower": lower,
        "font": font,
        "size": size,
        "y0": y0,
        "length": len(text),
        "word_count": len(text.split()),
        "has_colon": ":" in text,
        "starts_with_digit": text[:1].isdigit() if text else False,
        "is_bold": "bold" in font.lower(),
        "relative_size": round(relative_size, 2),
        "header_region": header_region,
        "has_doi": "doi" in patterns,
        "has_issn": "issn" in patterns,
        "has_year": "year" in patterns,
        "has_pages": "start_page" in patterns,
        "is_url": lower.startswith("http") or "https://" in lower,
        "is_ignore": is_end_line(text),
        "fuzzy_label": fuzzy_match_label(text)[0] or "",
    }


def features_to_crf_dict(features):
    return {
        "bias": 1.0,
        "text": features["text"][:80],
        "lower": features["lower"][:80],
        "length": features["length"],
        "word_count": features["word_count"],
        "has_colon": features["has_colon"],
        "starts_with_digit": features["starts_with_digit"],
        "is_bold": features["is_bold"],
        "relative_size": features["relative_size"],
        "header_region": features["header_region"],
        "has_doi": features["has_doi"],
        "has_issn": features["has_issn"],
        "has_year": features["has_year"],
        "has_pages": features["has_pages"],
        "is_url": features["is_url"],
        "is_ignore": features["is_ignore"],
        "fuzzy_label": features["fuzzy_label"],
    }


def structured_lines_to_features(structured_lines, page_height=None):
    if not structured_lines:
        return []
    max_font = max(line.get("size", 0) for line in structured_lines) or 1
    return [
        line_to_features(line, page_height=page_height, max_font_size=max_font)
        for line in structured_lines
    ]
