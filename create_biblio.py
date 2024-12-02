import fitz  # PyMuPDF / fitz # For reading PDF # using PyMuPDF-1.24.13
import rispy  # To create ris file # using rispy-0.9.0
import argparse  # To collect arguments from command line # using argparse-1.4.0
import os  # For finding PDFs in folder

from constants import END_KEYWORDS, KEYWORDS
from parse_info_functions import (
    getInfoFromFileName,
    parseInfoGeneral,
    findInfoPersee,
    findInfoJSTOR,
)

# Added requirements.txt for easier setup
# Added to Github
# Added dev tools
# Added README
# TODO Add tests

# Searches given folder and all sub folders for PDFs
# Collects citation info from JSTOR or Persee formats
# Adds RIS foramt entries to a file

risEntries = []
anomalies = []

# Want any counts for resource type?
numJSTOR = 0
numPersee = 0
numOther = 0
numFileName = 0


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
    global numFileName
    global numJSTOR
    global numPersee

    # page.search_for returns a list of location rectangles

    # JSTOR
    sourceRec = page.search_for("Source")
    # Persee/French
    citeThisDocRec = page.search_for("Citer ce document")  # Persee is always French

    # Converts to RIS format (seems easiest)
    # See https://en.wikipedia.org/wiki/RIS_(file_format)#:~:text=RIS%20is%20a%20standardized%20tag,a%20number%20of%20reference%20managers.

    if sourceRec:
        output, addToJSTORCount = findInfoJSTOR(page, pdf_path)
        if addToJSTORCount == 2:
            numFileName += 1
        else:
            numJSTOR += addToJSTORCount
    elif citeThisDocRec:
        output, addToPerseeCount = findInfoPersee(page, citeThisDocRec[0], pdf_path)
        if addToPerseeCount == 2:
            numFileName += 1
        else:
            numPersee += addToPerseeCount
    else:
        print("Update: Didn't identify a known format (from JSTOR or Persee)")
        output, _ = getInfoFromFileName(pdf_path)
        numFileName += 1
        info = getInfoGeneral(page)
        output = parseInfoGeneral(info, output)

    risEntries.append(output)


def getInfoGeneral(page):
    global numOther
    numOther += 1
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


def searchFolder(search_path):
    numPaths = 0
    print("Update: Searching for PDFs")
    paths = []

    for root, _, files in os.walk(search_path):
        for file in files:
            if file.endswith(".pdf") and not file.startswith("-"):
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
    print("Update: There were ", str(numOther), " PDFs with unknown format")
    print("Update: Searched file names for info for ", str(numOther), " PDFs")

    if risEntries:
        createBiblio(outputFile)
    else:
        print("Update: There are no biblio entries to write")

    print("Updated: Finished")


main()
