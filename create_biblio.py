import fitz  # PyMuPDF / fitz # For reading PDF # using PyMuPDF-1.24.13
import rispy  # To create ris file # using rispy-0.9.0
import argparse  # To collect arguments from command line # using argparse-1.4.0
import os  # For finding PDFs in folder
import re  # For regex replacement

# requirements.txt for easier setup - "pipreqs ." and "pip3 install -r requirements.txt"
# Added to Github
# Added dev tools
# Added README
# TODO Add tests

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
        findInfoJSTOR(page, pdf_path)
    elif citeThisDocRec:
        print("Update: PDF is from Persee")
        findInfoPersee(page, citeThisDocRec[0], pdf_path)
    elif journalTitleRec:
        print("Update: PDF is from Middlebury Library")
        findInfoMiddleburyBook(page, pdf_path)
    else:
        print(
            "Error: Can't identify which collection (JSTOR, Persee, Middlebury Library) PDF is from: ",
            pdf_path,
        )
        findAnyInfo(page, pdf_path)


def findAnyInfo(page, pdf_path):
    anomalies.append({"path": pdf_path, "info": page.get_text()})


def createAnomaliesFile():
    print("Update: Creating anomalies.txt file")
    try:
        # TODO: warn with response if anomalies.txt isn't empty?
        with open("anomalies.txt", "w") as text_file:
            text_file.write(str(anomalies))
    except Exception as e:
        print("Error: Writing to anomalies.txt file failed: ", e)
    else:
        print("Update: Successfully wrote to anomalies.txt file")


# Assumes all sections are present, whether they have info or not
def findInfoJSTOR(page, pdf_path):
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
            print(" ")
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
        print("Update: Didn't find title, adding to anomalies")
        findAnyInfo(page, pdf_path)
        numJSTOR -= 1
        return

    output["title"] = infoLines[0]
    for line in infoLines[1:]:
        if line.startswith("Author(s):"):
            output["authors"] = line[11:].split(", ")
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
    numPersee += 1

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
        numPersee -= 1
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
def findInfoMiddleburyBook(page, pdf_path):
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
            print("")
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
                print("Update: Didn't find title, adding to anomalies")
                findAnyInfo(page, pdf_path)
                numMiddlebury -= 1
                return
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
            output["authors"] = line.replace("Artide Author:", "", 1).strip().split(",")
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
                "Warn: Output path does not exist - default (last parameter of input path) will be used instead"
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
            "Warn: Output file must be .ris - default (last parameter of input path) will be used instead"
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
