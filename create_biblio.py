import fitz  # PyMuPDF / fitz # For reading PDF # using PyMuPDF-1.24.13
import rispy  # To create ris file # using rispy-0.9.0
import argparse  # To collect arguments from command line # using argparse-1.4.0
import os  # For finding PDFs in folder
import re  # For regex replacement

from constants import END_KEYWORDS, KEYWORDS

# Added requirements.txt for easier setup
# Added to Github
# Added dev tools
# Added README
# TODO Add tests

# Searches given folder and all sub folders for PDFs
# Collects citation info from JSTOR, Persee, or Middlebury Library formats
# Adds RIS foramt entries to a file

risEntries = []

# Want any counts for resource type?
numJSTOR = 0
numPersee = 0
numMiddlebury = 0
numOther = 0


def createBiblio(outputFile):
    print("Update: Creating RIS file")
    try:
        with open(outputFile, "w") as ris_file:
            rispy.dump(risEntries, ris_file)
    except Exception as e:
        print("Error: Writing to RIS file failed: ", e)
    else:
        print("Update: Successfully wrote to RIS file")


def findInfo(pdf_path):
    doc = fitz.open(pdf_path)
    page = doc[0]

    # page.search_for returns a list of location rectangles

    # JSTOR
    sourceRec = page.search_for("Source")
    # Persee/French
    citeThisDocRec = page.search_for("Citer ce document")  # Persee is always French
    # Middlebury books
    # journalTitleRec = page.search_for("Journal Title")

    # Converts to RIS format (seems easiest)
    # See https://en.wikipedia.org/wiki/RIS_(file_format)#:~:text=RIS%20is%20a%20standardized%20tag,a%20number%20of%20reference%20managers.

    if sourceRec:
        findInfoJSTOR(page, pdf_path)
    elif citeThisDocRec:
        findInfoPersee(page, citeThisDocRec[0], pdf_path)
    # elif journalTitleRec:
    # print("Update: PDF is from Middlebury Library")
    # findInfoMiddleburyBook(page, pdf_path)
    else:
        print(
            "Update: Didn't identify a known format (JSTOR, Persee, or Middlebury Library)"
        )
        output = getInfoFromFileName(pdf_path)
        print("output: ", output)
        info = getInfoGeneral(page)
        moreOutput = parseInfo(info, output)
        print("moreOutput: ", moreOutput)
        risEntries.append(moreOutput)


# Go to here if the 3 known formats don't work
def getInfoFromFileName(file_path):
    print("Update: Collecting info from file name")
    output = {}
    file_name = os.path.basename(os.path.normpath(file_path))
    # Remove .pdf
    file_name = file_name.split(".")[0]
    # Split on year
    textSections = re.split(r"(?<!\d)\d{4}(?!\d)", file_name)
    if len(textSections) == 2 and textSections[1]:
        author, title = textSections
        output["author"] = author.strip()
        output["title"] = title.strip()
        print("Update: author found")
        print("Update: article title found")
    # If there was only text and year, nothing after
    elif len(textSections) == 2:
        title = textSections[0]
        output["title"] = title.strip()
    elif len(textSections) > 2:
        author = textSections[0]
        title = textSections[1]
        output["author"] = author.strip()
        output["title"] = title.strip()
        print("Update: author found")
        print("Update: article title found")
    else:
        # Strip is unlikely to do anything here, just to be safe?
        output["title"] = file_name.strip()
        print("Update: article title found")

    year = re.findall(r"[0-9]{4}", file_name)
    if len(year) >= 1:
        output["year"] = year[0]
        print("Update: year published found")

    return output


def getInfoGeneral(page):
    global numOther
    numOther += 1
    # Get list of lines of text, with fonts and line size
    lis = []
    for i in page.get_text("dict")["blocks"]:
        try:
            lines = i["lines"]
            for line in range(len(lines)):
                li = list(
                    (
                        lines[line]["spans"][0]["text"],
                        i["lines"][line]["spans"][0]["font"],
                        round(i["lines"][line]["spans"][0]["size"]),
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


def parseInfo(infoLines, output):
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
                    output["type_of_reference"] = "BOOK"
                else:
                    output["type_of_reference"] = "JOUR"
                if (
                    line.startswith("Author(s):")
                    or line.startswith("Artide Author:")
                    or line.startswith("ARTICLE AUTHOR:")
                    or line.startswith("Article Author:")
                ):
                    # TODO Add to README - authors split by ','
                    # some formats have last, first or first, last names
                    print("authors: ", noLabelLine)
                    authors = noLabelLine.split(", ")
                    output["authors"] = [author.strip(" ") for author in authors]
                # TODO Is this needed?
                # JSTOR
                if line.startswith("Source: "):
                    text = noLabelLine.split(", ")
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
                            startPage, endPage = item.strip("pp. ").split("-")
                            output["start_page"] = startPage
                            output["end_page"] = endPage
                    # TODO return here?
                if (
                    line.startswith("Vol.")
                    or line.startswith("VOLUME:")
                    or line.startswith("Volume:")
                ):
                    output["volume"] = noLabelLine
                elif line.startswith("tome"):
                    output["volume"] = line.strip("tome ")
                if (
                    line.startswith("Published By:")
                    or line.startswith("Journal Name:")
                    or line.startswith("Journal Title:")
                    or line.startswith("JOURNAL TITLE:")
                    or line.startswith("Journal:")
                    or line.startswith("In:")
                ):
                    output["journal_name"] = noLabelLine
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
                    print("issue: ", noLabelLine)
                    if noLabelLine:
                        output["issue"] = noLabelLine
        else:
            if line.startswith("tome"):
                output["volume"] = line.strip("tome ")

    return output


# Assumes all sections are present, whether they have info or not
def findInfoJSTOR(page, pdf_path):
    # Keeping counts of types, just in case
    global numJSTOR

    # Reminder: Any field may be missing

    ISBN = page.search_for("ISBN")
    if ISBN:
        print("Info: " + pdf_path + " has ISBN")
        output = {"type_of_reference": "BOOK"}
    else:
        output = {"type_of_reference": "JOUR"}

    # Get list of lines of text, with fonts and line size
    lis = []
    for i in page.get_text("dict")["blocks"]:
        try:
            lines = i["lines"]
            for line in range(len(lines)):
                li = list(
                    (
                        lines[line]["spans"][0]["text"],
                        i["lines"][line]["spans"][0]["font"],
                        round(i["lines"][line]["spans"][0]["size"]),
                    )
                )
                lis.append(li)
        except KeyError:
            pass
    # Get list of only relevant lines of text
    keywords = ["Author(s):", "Source:", "Published"]
    j = 0
    curStr = ""
    infoLines = []
    for i in range(len(lis)):
        if j >= len(keywords):
            break
        if lis[i][0].startswith(keywords[j]):
            infoLines.append(curStr)
            curStr = lis[i][0]
            j += 1
        else:
            curStr += lis[i][0]

    if not infoLines:
        print("Update: Didn't find title, searching file name")
        getInfoFromFileName(pdf_path)
        return
    else:
        print("Update: PDF is from JSTOR")
        numJSTOR += 1

    output["title"] = infoLines[0]
    for line in infoLines[1:]:
        if line.startswith("Author(s):"):
            authors = line[10:].split(", ")
            output["authors"] = [author.strip(" ") for author in authors]
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

    risEntries.append(output)


# Assumes all sections are present, whether they have info or not
def findInfoPersee(page, citeThisDocRec, pdf_path):
    # Keeping counts of types, just in case
    global numPersee

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
        clip=fitz.Rect(citeThisDocRec.x0, citeThisDocRec.y0, page.rect.x1, end),
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
        getInfoFromFileName(pdf_path)
        return
    else:
        print("Update: PDF is from Persee")
        numPersee += 1

    output["title"] = title

    for index in range(2, len(citation)):
        item = citation[index]
        if item.startswith("In: "):
            output["journal_name"] = item.strip("In: ")
        if citation[index - 1].startswith("pp"):
            pages = item
            startPage, endPage = re.sub("\n", "", pages).split(
                "-"
            )  # 'startPage-\nendPage;'
            output["start_page"] = startPage.strip()
            output["end_page"] = endPage.strip(";")
        elif item.startswith("1") or item.startswith("2"):
            parts = item.split(", ")
            for part in parts:
                if part.startswith("tome"):
                    output["volume"] = part.strip("tome ")
                else:
                    output["year"] = part.strip(")")

    risEntries.append(output)


# Assumes all sections are present, whether they have info or not
def findInfoMiddleburyBook(page, pdf_path):
    # Keeping counts of types, just in case
    global numMiddlebury

    # Reminder: Any field may be missing
    ISBN = page.search_for("ISBN")
    if ISBN:
        print("Info: " + pdf_path + " has ISBN")
        output = {"type_of_reference": "BOOK"}
    else:
        output = {"type_of_reference": "JOUR"}

    lis = []
    for i in page.get_text("dict")["blocks"]:
        try:
            lines = i["lines"]
            for line in range(len(lines)):
                for s in range(len(lines[line]["spans"])):
                    li = list(
                        (
                            lines[line]["spans"][s]["text"],
                            lines[line]["spans"][s]["font"],
                            round(lines[line]["spans"][s]["size"]),
                        )
                    )
                    lis.append(li[0])
        except KeyError:
            pass
    # Get list of only relevant lines of text
    keywords = [
        "Volume:",
        "Issue:",
        "Month/Year:",
        "Pages:",
        "Artide Author:",
        "Artide Title:",
        "B o o k s ta c k s",
    ]
    j = 0
    curStr = ""
    infoLines = []
    for i in range(len(lis)):
        if j >= len(keywords):
            break
        if lis[i].startswith(keywords[j]):
            infoLines.append(curStr)
            curStr = lis[i]
            j += 1
        else:
            curStr += lis[i]

    for line in infoLines:
        # Blank sections will be added
        if line.startswith("Artide Title:"):
            title = line.replace("Artide Title:", "", 1).strip()
            if not title:
                print("Update: Didn't find title, searching file name")
                getInfoFromFileName(pdf_path)
                return
            else:
                print("Update: PDF is from Middlebury Library")
                numMiddlebury += 1
            output["title"] = line.replace("Artide Title:", "", 1).strip()
        if (
            line.startswith("Journal Title:")
            and line.replace("Journal Title:", "", 1).strip()
        ):
            output["journal_name"] = line.replace("Journal Title:", "", 1).strip()
        if line.startswith("Volume:") and line.replace("Volume:", "", 1).strip():
            output["volume"] = line.replace("Volume:", "", 1).strip()
        if line.startswith("Issue:") and line.replace("Issue:", "", 1).strip():
            output["issue"] = line.replace("Issue:", "", 1).strip()
        if (
            line.startswith("Artide Author:")
            and line.replace("Artide Author:", "", 1).strip()
        ):
            authors = line.replace("Artide Author:", "", 1).strip().split(",")
            output["authors"] = [author.strip(" ") for author in authors]
        if (
            line.startswith("Month/Year:")
            and line.replace("Month/Year:", "", 1).strip()
        ):
            monthYear = line.replace("Month/Year:", "", 1).strip().split("/")
            if len(monthYear) > 1:
                year = monthYear[1]
            else:
                year = monthYear[0]
            output["volume"] = year
        if line.startswith("Pages:") and line.replace("Pages:", "", 1).strip():
            startPage, endPage = line.replace("Pages:", "", 1).strip().split("-")
            output["start_page"] = startPage
            output["end_page"] = endPage

    risEntries.append(output)


def searchFolder(search_path):
    numPaths = 0
    print("Update: Searching for PDFs")
    paths = []

    for root, _, files in os.walk(search_path):
        for file in files:
            if file.endswith(".pdf"):
                numPaths += 1
                paths.append(os.path.join(root, file))

    print("Update: Found " + str(numPaths) + " paths")
    return paths


def checkOutputFileType(file, inputPath):
    if not file:
        file = getLastInputPathParameter(inputPath)
    if not file.endswith(".ris"):
        return file.split(".")[0] + ".ris"
    else:
        return file


# TODO Update readme to reflect where output file will go
def getLastInputPathParameter(inputPath):
    folderName = os.path.basename(os.path.normpath(inputPath))
    fileName = folderName + ".ris"
    return os.path.join(inputPath, fileName)


def checkInputPathExists(file):
    try:
        path = os.path.exists(file)
        if path:
            print("Update: Input path exists")
            return True
        else:
            print("Error: Input path does not exist")
            return False
    except Exception as e:
        print("Error: Cannot access input folder: " + e)
        return False


def getCommandLineArguments():
    parser = argparse.ArgumentParser(description="Creates ris file from PDF")
    # Take input path from command line
    parser.add_argument(
        "--inputPath", required=True, type=str, help="Enter path of folder"
    )
    # Also take optional output path (which has to be .ris) from command line
    parser.add_argument(
        "--outputPath",
        required=False,
        type=str,
        default="",
        help="Enter path of RIS file (.ris)",
    )
    args = parser.parse_args()
    return args.outputPath, args.inputPath


def main():
    outputFilePath, inputFolderPath = getCommandLineArguments()

    # If no input path, there's nothing left to run
    if not checkInputPathExists(inputFolderPath):
        print("Update: Exiting program")
        return

    outputFile = checkOutputFileType(outputFilePath, inputFolderPath)

    paths = searchFolder(inputFolderPath)
    if not paths or len(paths) == 0:
        print("Update: No PDFs found")
        print("Update: No output files created")
        print("Update: Finished")
        return
    for path in paths:
        print("Update: Finding info for - ", path)
        findInfo(path)

    # Keeping counts of types, just in case
    print("Update: There were ", str(numJSTOR), " PDFs from JSTOR")
    print("Update: There were ", str(numPersee), " PDFs from Persee")
    print("Update: There were ", str(numMiddlebury), " PDFs from Middlebury Library")
    print("Update: There were ", str(numOther), " PDFs with unknown format")

    if risEntries:
        createBiblio(outputFile)
    else:
        print("Update: There are no biblio entries to write")

    print("Updated: Finished")


main()
