import pymupdf  # For reading PDF
import re
import os
from constants import END_KEYWORDS, KEYWORDS

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
        print("Update: Article title found")

    return output, 2


# TODO Doesn't have tests - Does it need tests if everything else is tested?
def generalInfoCollector(page, output):
    # Get from file name is run before this and
    # the output is fed here in the output argument
    info = getInfoGeneral(page)
    output = parseInfoGeneral(info, output)
    return output


# Has tests
def parseInfoGeneral(infoLines, output):
    # TODO This update can be more clear
    print("Update: Parsing info from a general format")
    for line in infoLines:
        # Can't split on non-existent colon
        if ":" in line:
            noLabelLine = line.split(":")[1].strip(" ")
            # Some labels are present without info attached
            if noLabelLine:
                if line.startswith("TYPE:") or line.startswith("Type:"):
                    output["type_of_reference"] = noLabelLine.split(" ")[0]
                elif line.startswith("ISBN:"):
                    # TODO rispy doesn't have ISBN field
                    output["type_of_reference"] = "BOOK"
                elif line.startswith("Print: Manuscript"):
                    output["type_of_reference"] = "MANSCPT"
                elif line.startswith("Print: Ancient Text"):
                    output["type_of_reference"] = "ANCIENT"
                elif line.startswith("Print: Classical Work"):
                    output["type_of_reference"] = "CLSWK"
                else:
                    output["type_of_reference"] = "JOUR"
                if line.startswith("ISSN:"):
                    output["issn"] = noLabelLine
                if (
                    line.startswith("Author(s):")
                    or line.startswith("Artide Author:")
                    or line.startswith("ARTICLE AUTHOR:")
                    or line.startswith("Article Author:")
                ):
                    # TODO Add to README - authors split by ','
                    # some formats have last, first or first, last names
                    authors = noLabelLine.split(", ")
                    output["authors"] = [author.strip(" ") for author in authors]
                if line.startswith("Source: "):
                    # JSTORs shouldn't get here, but if so,
                    # want some data to look through
                    print("Odd: Found source line outside of JSTOR parser: ", line)
                if (
                    line.startswith("Vol.")
                    or line.startswith("VOLUME:")
                    or line.startswith("Volume:")
                ):
                    output["volume"] = noLabelLine
                elif line.startswith("tome"):
                    output["volume"] = line.strip("tome ")
                if (
                    line.startswith("Journal Name:")
                    or line.startswith("Journal Title:")
                    or line.startswith("JOURNAL TITLE:")
                    or line.startswith("Journal:")
                    or line.startswith("In:")
                ):
                    output["journal_name"] = noLabelLine
                if line.startswith("Published By:") or line.startswith("Published by:"):
                    if "Stable" in noLabelLine:
                        output["publisher"] = noLabelLine.split(" Stable")[0].strip()
                    elif "URL" in noLabelLine:
                        output["publisher"] = noLabelLine.split(" URL")[0].strip()
                    else:
                        output["publisher"] = line.strip()
                if line.startswith("Year:") or line.startswith("YEAR:"):
                    output["year"] = noLabelLine
                elif line.startswith("Month/Year:"):
                    monthYear = noLabelLine.split("/")
                    if len(monthYear) > 1:
                        year = monthYear[1]
                    else:
                        year = monthYear[0]
                    output["year"] = year
                if (
                    line.startswith("Pages:")
                    or line.startswith("pp.")
                    or line.startswith("PAGES:")
                ):
                    if "-" in noLabelLine:
                        startPage, endPage = noLabelLine.split("-")
                        output["start_page"] = startPage
                        output["end_page"] = endPage
                if line.startswith("DOI:") or line.startswith("doi:"):
                    output["doi"] = noLabelLine
                if line.startswith("Issue:") or line.startswith("ISSUE:"):
                    output["issue"] = noLabelLine
        else:
            if line.startswith("tome"):
                output["volume"] = line.strip("tome ")

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
        return getInfoFromFileName(pdf_path, info)
    else:
        print("Update: PDF is from Persee")

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
    else:
        print("Update: PDF is from Brill")
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
    else:
        print("Update: PDF is from JSTOR")

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


# Has test
# pymupdf used here
def getInfoGeneral(page):
    # Get list of lines of text, with fonts and line size
    lis = []
    for i in page.get_text("dict")["blocks"]:
        try:
            lines = i["lines"]
            for line in range(len(lines)):
                for k in range(len(lines[line]["spans"])):
                    li = list(
                        (
                            lines[line]["spans"][k]["text"],
                            i["lines"][line]["spans"][k]["font"],
                            round(i["lines"][line]["spans"][k]["size"]),
                        )
                    )
                    lis.append(li)
        except KeyError:
            pass
    # Get list of only relevant lines of text
    curStr = ""
    infoLines = []
    for i in range(len(lis)):
        if lis[i][0].startswith(tuple(KEYWORDS)):
            infoLines.append(curStr)
            curStr = lis[i][0]
        elif lis[i][0].startswith(tuple(END_KEYWORDS)):
            infoLines.append(curStr)
            curStr = ""
        else:
            curStr += lis[i][0]
    return infoLines
