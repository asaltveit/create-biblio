import pymupdf  # For reading PDF
import re
import os
from constants import END_KEYWORDS, KEYWORDS
from line_features import (
    extract_patterns,
    fuzzy_match_label,
    is_end_line,
    is_keyword_line,
    structured_lines_to_features,
)
from line_classifier import maybe_apply_ml_fallback

# Other formats:
# Taylor and Francis = https://www.tandfonline.com/doi/full/10.1080/02549948.2016.1170348?scroll=top&needAccess=true

# TODO Likely need a format specific to Taylor and Francis


# Has test
def collectYearManuscriptCode(file_name, output):
    numbers4digits = re.findall(r"[0-9]{4}", file_name)
    numbersAllDigits = re.findall(r"[0-9]{3,9}", file_name)
    secondItem = True

    if numbers4digits:
        # Do I need this check?
        if " " in file_name:
            space_sections = file_name.split(" ")
            secondItem = space_sections[1] == numbers4digits[0]
        intYear = int(numbers4digits[0])
        if len(numbers4digits) >= 1 and intYear > 0 and intYear < 2050 and secondItem:
            output["year"] = numbers4digits[0]
            print("Update: Year found: " + numbers4digits[0])
            additionalNums = [x for x in numbersAllDigits if x != numbers4digits[0]]
            if additionalNums:
                output["number_of_volumes"] = additionalNums[0]
                print("Update: Manuscript code found")
    elif numbersAllDigits:
        output["number_of_volumes"] = numbersAllDigits[0]
        print("Update: Manuscript code found")
    return output


# Has tests
def collectPageNumbers(file_name, output):
    pageSections = re.findall(r" pp [0-9]{1,8}-[0-9]{1,8}", file_name)
    if pageSections:
        startPage, endPage = pageSections[0].replace(" pp ", "", 1).split("-")
        output["start_page"] = startPage
        startLength = len(startPage)
        endLength = len(endPage)
        if endLength >= startLength:
            output["end_page"] = endPage
        else:
            # 56-7 is pages 56 and 57, not pages 56 to 07
            output["end_page"] = startPage[: startLength - endLength] + endPage
        file_name_parts = re.split(r" pp [0-9]{1,8}-[0-9]{1,8}", file_name)
        file_name = "".join(file_name_parts)
        print("Update: Found page numbers")
    else:
        print("Warn: pp found in filename but unable to parse")
    return output


# Has tests
def getInfoFromFileName(file_path, output={}):
    print("Update: Collecting info from file name")
    file_name = os.path.basename(os.path.normpath(file_path))
    # Remove .pdf
    file_name = file_name.replace(".pdf", "", 1)

    # Detect page numbers
    if " pp " in file_name:
        output = collectPageNumbers(file_name, output)

    # Numbers
    output = collectYearManuscriptCode(file_name, output)

    textSections = re.split(r"(?<!\d)\d{4}(?!\d)", file_name)
    # Seems to be too many print statements
    if len(textSections) == 2 and textSections[1]:
        author, title = textSections
        output["authors"] = [author.strip()]
        output["title"] = title.strip()
        print("Update: Author found")
        print("Update: Article title found")
    # If there was only text and year, nothing after
    elif len(textSections) == 2:
        title = textSections[0]
        output["title"] = title.strip()
        print("Update: Article title found")
    elif len(textSections) > 2:
        author = textSections[0]
        title = textSections[1]
        output["authors"] = [author.strip()]
        output["title"] = title.strip()
        print("Update: Author found")
        print("Update: Article title found")
    else:
        # Strip is unlikely to do anything here, just to be safe?
        output["title"] = file_name.strip()
        # print("Update: Article title found")

    return output, 2


def _set_if_empty(output, key, value):
    if value and (key not in output or not output[key]):
        output[key] = value


def _apply_labeled_field(output, field_key, value):
    if not value:
        return
    if field_key == "authors":
        output["authors"] = [
            author.strip() for author in value.split(", ") if author.strip()
        ]
    elif field_key == "title":
        _set_if_empty(output, "title", value)
    elif field_key == "journal_name":
        output["journal_name"] = value
    elif field_key == "year":
        if "/" in value:
            parts = value.split("/")
            output["year"] = parts[1] if len(parts) > 1 else parts[0]
        else:
            output["year"] = value
    elif field_key == "volume":
        output["volume"] = value
    elif field_key == "issue":
        output["issue"] = value
    elif field_key == "pages":
        if "-" in value:
            start_page, end_page = value.split("-", 1)
            output["start_page"] = start_page.strip()
            output["end_page"] = end_page.strip()
    elif field_key == "doi":
        output["doi"] = value
    elif field_key == "issn":
        output["issn"] = value
    elif field_key == "publisher":
        if " Stable" in value:
            value = value.split(" Stable")[0].strip()
        if " URL" in value:
            value = value.split(" URL")[0].strip()
        output["publisher"] = value
    elif field_key == "type_of_reference":
        output["type_of_reference"] = value.split(" ")[0]
    elif field_key == "isbn":
        output["type_of_reference"] = "BOOK"


def _apply_reference_type_from_line(output, line):
    if line.startswith("ISBN:"):
        output["type_of_reference"] = "BOOK"
    elif line.startswith("Print: Manuscript"):
        output["type_of_reference"] = "MANSCPT"
    elif line.startswith("Print: Ancient Text"):
        output["type_of_reference"] = "ANCIENT"
    elif line.startswith("Print: Classical Work"):
        output["type_of_reference"] = "CLSWK"
    elif line.startswith(("TYPE:", "Type:")):
        value = line.split(":", 1)[1].strip()
        if value:
            output["type_of_reference"] = value.split(" ")[0]
    elif ":" in line and fuzzy_match_label(line)[0]:
        if output.get("type_of_reference") not in (
            "BOOK",
            "MANSCPT",
            "ANCIENT",
            "CLSWK",
        ):
            output["type_of_reference"] = "JOUR"


def _apply_pattern_fields(output, line):
    patterns = extract_patterns(line)
    for key, value in patterns.items():
        _set_if_empty(output, key, value)


def _apply_heuristic_fields(output, structured_lines):
    if not structured_lines:
        return output
    header_lines = [
        line
        for line in structured_lines
        if line.get("y0", 0)
        <= max(line.get("y0", 0) for line in structured_lines) + 200
        and line.get("text")
        and not is_end_line(line["text"])
        and not is_keyword_line(line["text"])
        and "http" not in line["text"].lower()
    ]
    if not header_lines:
        return output
    max_size = max(line.get("size", 0) for line in structured_lines) or 1
    if not output.get("title"):
        title_candidates = [
            line for line in header_lines if line.get("size", 0) >= max_size - 1
        ]
        if title_candidates:
            output["title"] = title_candidates[0]["text"].strip()
    if not output.get("authors"):
        for line in header_lines:
            text = line["text"].strip()
            if "," in text and len(text.split()) <= 8 and not text.startswith("http"):
                output["authors"] = [
                    name.strip() for name in text.split(",") if name.strip()
                ]
                break
    for line in structured_lines:
        text = line.get("text", "")
        if not output.get("journal_name") and re.search(r"\(\d{4}\)", text):
            journal_name = re.split(r"\(\d{4}\)", text)[0].strip()
            if journal_name:
                output["journal_name"] = journal_name
    return output


# TODO Doesn't have tests - Does it need tests if everything else is tested?
def generalInfoCollector(page, output, use_ml=False):
    structured_lines = getStructuredLines(page)
    info = [line["text"] for line in structured_lines if line.get("text")]
    if not info:
        info = getInfoGeneral(page)
    output = parseInfoGeneral(info, output, structured_lines=structured_lines)
    if use_ml:
        feature_dicts = structured_lines_to_features(
            structured_lines, page_height=page.rect.height
        )
        output = maybe_apply_ml_fallback(
            output, structured_lines, feature_dicts, use_ml=True
        )
    return output


# Has tests
def parseInfoGeneral(infoLines, output, structured_lines=None):
    print("Update: Parsing info from a general format")
    for line in infoLines:
        if not line or is_end_line(line):
            continue
        _apply_pattern_fields(output, line)
        if ":" in line:
            field_key, value = fuzzy_match_label(line)
            if field_key:
                if field_key == "type_of_reference" and line.startswith(
                    ("TYPE:", "Type:")
                ):
                    _apply_labeled_field(output, field_key, value)
                elif field_key == "isbn":
                    _apply_labeled_field(output, field_key, value)
                else:
                    _apply_labeled_field(output, field_key, value)
                _apply_reference_type_from_line(output, line)
            elif line.startswith("Source: "):
                print("Odd: Found source line outside of JSTOR parser: ", line)
            else:
                _apply_reference_type_from_line(output, line)
        else:
            if line.startswith("tome"):
                output["volume"] = line.strip("tome ")
    if structured_lines:
        output = _apply_heuristic_fields(output, structured_lines)
    return output


# Has test
# TODO remove () and numbers from journal name?
# pymupdf used here
# Assumes all sections are present, whether they have info or not
def findInfoPersee(page, citeThisDocRec, pdf_path):
    yearSet = False
    # Reminder: Any field may be missing
    ISBN = page.search_for("ISBN")
    if ISBN:
        print("Info: " + pdf_path + " has ISBN")
        output = {"type_of_reference": "BOOK"}
    else:
        output = {"type_of_reference": "JOUR"}

    # If the string is shorter like 'http', doi will be missing

    endRec = page.search_for("https://")
    if not endRec:
        endRec = page.search_for("http://")  # Just in case?
    if not endRec:
        endRec = page.search_for("Fichier")
    if not endRec:
        end = page.rect.y1
    else:
        end = endRec[0].y0

    # Extract text from the page, starting from the coordinates of "Source", stopping before "Published by"
    section = page.get_text(
        "text",
        clip=pymupdf.Rect(citeThisDocRec.x0, citeThisDocRec.y0, page.rect.x1, end),
    )
    # Remove the search string itself from the extracted text
    section = section.replace("Citer ce document / Cite this document :", "", 1).strip()
    citation, doi = section.split(";")
    citation = citation.split(". ")

    # Parse text

    doi = doi.strip("\ndoi : ")
    if doi:
        output["doi"] = doi

    authors = citation[0].split(", ")
    reversedAuthors = []
    for author in authors:
        author = author.strip().split(" ")
        author.reverse()  # author is backwards 'lastname firstname'
        author = " ".join(author)
        reversedAuthors.append(author)
    output["authors"] = reversedAuthors

    title = citation[1]  # Title will be strange if authors are missing

    # This is unlikely to happen
    # if no title, it'll break the ris file - use file name for info instead
    if not title:
        print("Update: Didn't find title, searching file name")
        # TODO Should general info be parsed for this as well?
        # Returned number will come from getInfoFromFileName
        info = getInfoFromFileName(pdf_path, output)
        return generalInfoCollector(page, info)(pdf_path, info)

    output["title"] = title

    for index in range(2, len(citation)):
        item = citation[index]
        # Not every journal name is followed by a period before the year
        if item.startswith("In: "):
            if "(" in item:
                journalName, remainder = item.split("(")
                output["journal_name"] = journalName.strip()
                year = remainder.split(")")[0].strip()
                output["year"] = year
                yearSet = True
            output["journal_name"] = item.strip("In: ")
        if citation[index - 1].startswith("pp"):
            pages = item
            startPage, endPage = re.sub("\n", "", pages).split(
                "-"
            )  # 'startPage-\nendPage;'
            output["start_page"] = startPage.strip()
            output["end_page"] = endPage.strip(";")
        elif item.startswith("1") or item.startswith("2"):
            # Ex: 1957, tome 115
            parts = item.split(", ")
            for part in parts:
                if part.startswith("tome"):
                    output["volume"] = part.strip("tome ")
                elif not yearSet:
                    output["year"] = part.strip(")")

    return output, 1


# Has test
# Brill = https://brill.com/view/journals/jwl/1/2/article-p143_2.xml?rskey=LBePrJ&result=2&ebody=pdf-117260
def findInfoBrill(page, endRec, pdf_path):
    output = {}

    # Extract text from the page, starting from the coordinates of "Source", stopping before "Published by"
    section = page.get_text(
        "text",
        clip=pymupdf.Rect(page.rect.x0, page.rect.y0, page.rect.x1, endRec.y0),
    )
    lines = section.split("\n")
    journal, pages = re.split(r"\([0-9]{4}\)", lines[0])
    start, end = re.findall(r"[0-9]{1,6}", pages.strip())
    output["journal_name"] = journal.strip()
    output["start_page"] = start.strip()
    output["end_page"] = end.strip()
    year = re.findall(r"[0-9]{4}", lines[0])[0]
    output["year"] = year.strip()
    if len(lines) < 3:
        print("Update: Didn't find title, searching file name")
        # Returned number will come from getInfoFromFileName
        info = getInfoFromFileName(pdf_path, output)
        return generalInfoCollector(page, info)
    output["title"] = lines[2].strip()
    output["authors"] = [x.strip() for x in lines[3].split(",")]
    return output, 1


# Has tests
# Assumes all sections are present, whether they have info or not
def findInfoJSTOR(page, pdf_path):
    # Reminder: Any field may be missing

    ISBN = page.search_for("ISBN")
    isManuscript = page.search_for("Print: Manuscript")
    isAncientText = page.search_for("Print: Ancient Text")
    isClassicalWork = page.search_for("Print: Classical Work")
    if ISBN:
        print("Info: " + pdf_path + " has ISBN")
        output = {"type_of_reference": "BOOK"}
    elif isManuscript:
        output = {"type_of_reference": "MANSCPT"}
    elif isAncientText:
        output = {"type_of_reference": "ANCIENT"}
    elif isClassicalWork:
        output = {"type_of_reference": "CLSWK"}
    else:
        output = {"type_of_reference": "JOUR"}

    infoLines = getInfoGeneral(page)
    if not infoLines:
        print("Update: Didn't find title, searching file name")
        # TODO Should general info be parsed for this as well?
        # Returned number will come from getInfoFromFileName
        info = getInfoFromFileName(pdf_path, output)
        return generalInfoCollector(page, info)

    output["title"] = infoLines[0].strip()
    for line in infoLines[1:]:
        if line.startswith("Author(s):"):
            authors = line[10:].split(", ")
            output["authors"] = [author.strip(" ") for author in authors]
        if line.startswith("Published by:"):
            if "Stable" in line:
                output["publisher"] = (
                    line.replace("Published by: ", "", 1).split(" Stable")[0].strip()
                )
            elif "URL" in line:
                output["publisher"] = (
                    line.replace("Published by: ", "", 1).split(" URL")[0].strip()
                )
            else:
                output["publisher"] = line.replace("Published by: ", "", 1).strip()
        if line.startswith("ISSN:"):
            output["issn"] = line.replace("ISSN: ", "", 1).strip()
        if line.startswith("Source: "):
            text = line.replace("Source: ", "", 1).strip().split(", ")
            output["journal_name"] = text[0].split("(")[0].strip()
            for item in text[1:]:
                if item.startswith("Vol."):
                    volume = item.replace("Vol.", "", 1).strip()
                    volume = re.sub(" \n", "", volume).split("(")[0]
                    output["volume"] = volume
                if item.startswith("1") or item.startswith("2"):
                    year = item
                    year = year.strip(")")
                    output["year"] = year
                if item.startswith("pp."):
                    pages = item
                    startPage, endPage = pages.strip("pp. ").split("-")
                    output["start_page"] = startPage
                    output["end_page"] = endPage

    return output, 1


def getStructuredLines(page):
    """Return header lines with text, font, size, and vertical position."""
    spans = []
    for block in page.get_text("dict")["blocks"]:
        try:
            for line in block["lines"]:
                y0 = line["bbox"][1]
                for span in line["spans"]:
                    text = span["text"]
                    if not text.strip():
                        continue
                    spans.append(
                        {
                            "text": text,
                            "font": span["font"],
                            "size": round(span["size"]),
                            "y0": y0,
                        }
                    )
        except KeyError:
            pass
    structured_lines = []
    cur_line = None
    for span in spans:
        if is_keyword_line(span["text"]) or is_end_line(span["text"]):
            if cur_line and cur_line["text"].strip():
                structured_lines.append(cur_line)
            if is_end_line(span["text"]):
                cur_line = None
                continue
            cur_line = dict(span)
            continue
        if cur_line is None:
            cur_line = dict(span)
        else:
            cur_line["text"] += span["text"]
            if span["size"] > cur_line["size"]:
                cur_line["size"] = span["size"]
                cur_line["font"] = span["font"]
    if cur_line and cur_line["text"].strip():
        structured_lines.append(cur_line)
    return structured_lines


# Has test
# pymupdf used here
def getInfoGeneral(page):
    structured_lines = getStructuredLines(page)
    info_lines = []
    for line in structured_lines:
        text = line["text"]
        if is_keyword_line(text):
            info_lines.append(text)
        elif info_lines:
            info_lines[-1] += text
        else:
            info_lines.append(text)
    return info_lines
