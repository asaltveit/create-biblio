import fitz  # PyMuPDF / fitz # For reading PDF # using PyMuPDF-1.24.13
import rispy  # To create ris file # using rispy-0.9.0
import argparse  # To collect arguments from command line # using argparse-1.4.0
import os  # For finding PDFs in folder
import re  # For regex replacement

# requirements.txt for easier setup - "pipreqs ." and "pip3 install -r requirements.txt"
# TODO An error appears when the above is run "ERROR: ERROR: Failed to build installable wheels for some pyproject.toml based projects (traits)"
# Added to Github
# Added dev tools
# TODO Add tests
# TODO Add README

# Searches given folder and all sub folders for PDFs
# Collects citation info from JSTOR, Persee, or Middlebury Library formats
# Adds RIS foramt entries to a file

anomalies = []
risEntries = []

# Want any counts for resource type?
numJSTOR = 0
numPersee = 0
numMiddlebury = 0


def createBiblio(outputFile=""):
    print("Update: Creating RIS file")
    # TODO Will a default ever be needed here?
    file = outputFile or "biblio_data.ris"
    try:
        with open(file, "w") as ris_file:
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
    journalTitleRec = page.search_for("Journal Title")

    # Converts to RIS format (seems easiest)
    # See https://en.wikipedia.org/wiki/RIS_(file_format)#:~:text=RIS%20is%20a%20standardized%20tag,a%20number%20of%20reference%20managers.

    if sourceRec:
        print("Update: PDF is from JSTOR")
        findInfoJSTOR(page, sourceRec[0], pdf_path)
    elif citeThisDocRec:
        print("Update: PDF is from Persee")
        findInfoPersee(page, citeThisDocRec[0], pdf_path)
    elif journalTitleRec:
        print("Update: PDF is from Middlebury Library")
        findInfoMiddleburyBook(page, journalTitleRec[0], pdf_path)
    else:
        print(
            "Error: Can't identify which collection (JSTOR, Persee, Middlebury Library) PDF is from: ",
            pdf_path,
        )
        findAnyInfo(page)


def findAnyInfo(page, pdf_path):
    anomalies.append({"path": pdf_path, "info": page.get_text()})


def createAnomaliesFile():
    print("Update: Creating anomalies.txt file")
    try:
        # TODO: warn with response if anomalies.txt isn't empty?
        with open("anomalies.txt", "w") as text_file:
            text_file.write(anomalies)
    except Exception as e:
        print("Error: Writing to anomalies.txt file failed: ", e)
    else:
        print("Update: Successfully wrote to anomalies.txt file")


# Assumes all sections are present, whether they have info or not
def findInfoJSTOR(page, sourceRec, pdf_path):
    # Keeping counts of types, just in case
    global numJSTOR
    numJSTOR += 1

    # Reminder: Any field may be missing

    ISBN = page.search_for("ISBN")
    if ISBN:
        print("Info: " + pdf_path + " has ISBN")
        output = {"type_of_reference": "BOOK"}
    else:
        output = {"type_of_reference": "JOUR"}

    # Rectangles containing the searched for strings
    publishedByRec = page.search_for("Published by")[0]
    authorRec = page.search_for("Author(s):")[0]

    # starting from the coordinates of top of page, stopping before "Author"
    title = page.get_text(
        "text", clip=fitz.Rect(page.rect.x0, page.rect.y0, page.rect.x1, authorRec.y0)
    ).strip()

    # if no title, it'll break the ris file - put in anomalies instead
    if not title:
        print("Update: Didn't find title, adding to anomalies")
        findAnyInfo(page, pdf_path)
        return

    output["title"] = title

    # Extract text from the page, starting from the coordinates of "Source", stopping before "Published by"
    text = page.get_text(
        "text",
        clip=fitz.Rect(sourceRec.x0, sourceRec.y0, page.rect.x1, publishedByRec.y0),
    )
    # Remove the search string itself from the extracted text
    text = text.replace("Source:", "", 1).strip().split(", ")

    # Parse text
    journal = text[0].split("(")[0].strip()  # remove '(year)'
    output["journal_name"] = journal
    for item in text[1:]:
        if item.startswith("Vol."):
            volume = item.replace("Vol.", "", 1).strip()
            volume = re.sub(" \n", "", volume).split("(")[0]
            output["volume"] = volume
        if item.startswith("pp."):
            pages = item
            startPage, endPage = pages.strip("pp. ").split("-")
            output["start_page"] = startPage
            output["end_page"] = endPage
        if item.startswith("1") or item.startswith("2"):
            year = item
            year = year.strip(")")
            output["year"] = year

    # starting from the coordinates of "Author", stopping before "Source"
    author = page.get_text(
        "text", clip=fitz.Rect(authorRec.x0, authorRec.y0, page.rect.x1, sourceRec.y0)
    )
    author = author.replace("Author(s):", "", 1).strip().split(",")
    output["authors"] = author

    risEntries.append(output)


# Assumes all sections are present, whether they have info or not
def findInfoPersee(page, citeThisDocRec, pdf_path):
    # Keeping counts of types, just in case
    global numPersee
    numPersee += 1

    # Reminder: Any field may be missing
    ISBN = page.search_for("ISBN")
    if ISBN:
        print("Info: " + pdf_path + " has ISBN")
        output = {"type_of_reference": "BOOK"}
    else:
        output = {"type_of_reference": "JOUR"}

    # If the string is shorter like 'http', doi will be missing
    httpRec = page.search_for("https://www")[0]
    # Extract text from the page, starting from the coordinates of "Source", stopping before "Published by"
    section = page.get_text(
        "text",
        clip=fitz.Rect(citeThisDocRec.x0, citeThisDocRec.y0, page.rect.x1, httpRec.y0),
    )
    # Remove the search string itself from the extracted text
    section = section.replace("Citer ce document / Cite this document :", "", 1).strip()
    citation, doi = section.split(";")
    citation = citation.split(". ")

    # Parse text

    doi = doi.strip("\ndoi : ")
    output["doi"] = doi

    authors = citation[0].split(", ")
    reversedAuthors = []
    for author in authors:
        author = author.split(" ")
        author.reverse()  # author is backwards 'lastname firstname'
        author = " ".join(author)
        reversedAuthors.append(author)
    output["authors"] = reversedAuthors

    title = citation[1]  # Title will be strange if authors are missing

    # This is unlikely to happen
    # if no title, it'll break the ris file - put in anomalies instead
    if not title:
        print("Update: Didn't find title, adding to anomalies")
        findAnyInfo(page, pdf_path)
        return

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
                    output["volume"] = part
                else:
                    output["year"] = part.strip(")")

    risEntries.append(output)


# Assumes all sections are present, whether they have info or not
def findInfoMiddleburyBook(page, journalTitleRec, pdf_path):
    # Keeping counts of types, just in case
    global numMiddlebury
    numMiddlebury += 1

    # Reminder: Any field may be missing
    ISBN = page.search_for("ISBN")
    if ISBN:
        print("Info: " + pdf_path + " has ISBN")
        output = {"type_of_reference": "BOOK"}
    else:
        output = {"type_of_reference": "JOUR"}

    # For vertical limits
    volumeRec = page.search_for("Volume")[0]
    issueRec = page.search_for("Issue")[0]
    monthYearRec = page.search_for("Month/Year")[0]
    pagesRec = page.search_for("Pages")[0]
    # Fitz misreading test files' Article as Artide
    articleAuthorList = page.search_for("Artide Author") or page.search_for(
        "Article Author"
    )
    authorRec = articleAuthorList[0]
    titleList = page.search_for("Artide Title") or page.search_for("Article Title")
    titleRec = titleList[0]
    # For horizontal right limit
    sentRec = page.search_for("SENT")[0]

    # Parse text

    title = page.get_text(
        "text", clip=fitz.Rect(titleRec.x0, titleRec.y0, sentRec.x1, page.rect.y1)
    )

    # if no title, it'll break the ris file - put in anomalies instead
    if not title:
        print("Update: Didn't find title, adding to anomalies")
        findAnyInfo(page, pdf_path)
        return

    # Will only remove if present
    title = (
        title.replace("Artide Title:", "", 1)
        .replace("Article Title:", "", 1)
        .replace("SENT", "", 1)
        .strip()
    )
    title = re.sub("\n", "", title)
    if not title:
        print("Error: title is missing from " + pdf_path)
        print("Error: title is required for RIS file, ignoring")
        return
    else:
        output["title"] = title

    # Extract text from the page, starting from the coordinates of "Journal Title", stopping before "Volume"
    journal = page.get_text(
        "text",
        clip=fitz.Rect(
            journalTitleRec.x0, journalTitleRec.y0, sentRec.x1, volumeRec.y0
        ),
    )
    # Remove the search string itself from the extracted text
    journal = journal.replace("Journal Title:", "", 1).split("\n")[0].strip()

    volume = page.get_text(
        "text", clip=fitz.Rect(volumeRec.x0, volumeRec.y0, sentRec.x1, issueRec.y0)
    )
    volume = volume.replace("Volume:", "", 1).split("\n")[0].strip()

    issue = page.get_text(
        "text", clip=fitz.Rect(issueRec.x0, issueRec.y0, sentRec.x1, monthYearRec.y0)
    )
    issue = issue.replace("Issue:", "", 1).split("\n")[0].strip()

    monthYear = page.get_text(
        "text",
        clip=fitz.Rect(monthYearRec.x0, monthYearRec.y0, sentRec.x1, pagesRec.y0),
    )
    monthYear = monthYear.replace("Month/Year: ", "", 1).split("\n")[0].strip()

    pages = page.get_text(
        "text", clip=fitz.Rect(pagesRec.x0, pagesRec.y0, sentRec.x1, authorRec.y0)
    )
    pages = pages.replace("Pages:", "", 1).split("\n")[0].strip()

    author = page.get_text(
        "text", clip=fitz.Rect(authorRec.x0, authorRec.y0, sentRec.x1, titleRec.y0)
    )
    # replace() will only remove if present
    author = (
        author.replace("Artide Author:", "", 1)
        .replace("Article Author:", "", 1)
        .split("\n")[0]
        .strip()
    )
    author = author.split(", ")

    if journal:
        output["journal_name"] = journal
    if volume:
        output["volume"] = volume
    if issue:
        output["issue"] = issue
    if monthYear:
        monthYear = monthYear.split("/")
        if len(monthYear) > 1:
            year = monthYear[1]
        else:
            year = monthYear[0]
        output["year"] = year
    if pages:
        startPage, endPage = pages.split("-")
        output["start_page"] = startPage
        output["end_page"] = endPage
    if author:
        output["authors"] = author

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


# TODO Can this be zipped? - to include tests and test folders, perhaps an output folder?


# TODO Can this and checkInputPathExists be made more reuseable?
def checkOutputFileExists(file):
    try:
        path = os.path.exists(file)
        if path:
            print("Update: Output path exists")
            return True
        else:
            print(
                "Error: Output path does not exist - default (last parameter of input path) will be used instead"
            )
            return False
    except Exception as e:
        print(
            "Error: "
            + e
            + " - default (last parameter of input path) will be used instead"
        )
        return False


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


def checkOutputFileContents(file):
    if not os.stat(file).st_size == 0:
        print("Warning: Output file is not empty")
        text = input(
            "Should the file contents be (1) written over? Or (2) deleted? Or (3) do you want to exit the program?\n"
        )
        while True:
            # If (1), just continue like normal, dumping will rewrite
            if text == "1":
                print("Update: Will rewrite file contents")
                break
            elif text == "3":
                break
            elif text == "2":
                with open(file, "w") as ris_file:
                    # Clears file contents
                    ris_file.truncate(0)
                print("Update: Deleted file content")
                break
            else:
                print("Error: Response is not recognized")
                text = input(
                    "Should the file contents be (1) written over? Or (2) deleted? Or (3) do you want to exit the program?\n"
                )
                print(text)
                print(isinstance(text, str))

        # Exit program if text == "3"
        return False if text == "3" else True
    else:
        print("Update: Output file exists and is empty")
        return True


def getLastInputPathParameter(inputPath):
    # Using current folder because program goes through all sub folders
    folderName = os.path.basename(os.path.normpath(inputPath))
    fileName = folderName + ".ris"
    return fileName


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

    if args.outputPath and not args.outputPath.endswith(".ris"):
        print(
            "Error: Output file must be .ris - default (last parameter of input path) will be used instead"
        )

    if args.outputPath and args.outputPath.endswith(".ris"):
        folderName = args.outputPath
    else:
        folderName = getLastInputPathParameter(args.inputPath)

    print("Update: Using output file: ", folderName)
    return folderName, args.inputPath


def main():
    outputFileName, inputFolderPath = getCommandLineArguments()

    # If no input path, there's nothing left to run
    if not checkInputPathExists(inputFolderPath):
        print("Update: Exiting program")
        return

    # If no output path, a default is used instead
    if not checkOutputFileExists(outputFileName):
        outputFileName = getLastInputPathParameter(inputFolderPath)
    else:
        # Allows user to exit program if output file isn't empty and
        # they don't want the contents to change
        if not checkOutputFileContents(outputFileName):
            print("Update: Exiting program")
            return

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

    if risEntries:
        createBiblio(outputFileName)
    else:
        print("Update: There are no biblio entries to write")

    if anomalies:
        createAnomaliesFile()
    else:
        print("Update: There are no anomaly entries to write")

    print("Updated: Finished")


main()
