import fitz  # PyMuPDF / fitz # For reading PDF # using PyMuPDF-1.24.13
import argparse  # To collect arguments from command line # using argparse-1.4.0

from parse_info_functions import (
    generalInfoCollector,
    findInfoPersee,
    findInfoJSTOR,
    findInfoBrill,
)
from os_functions import (
    searchFolder,
    checkOutputFileType,
    checkInputPathExists,
)

from other_functions import createBiblio

# Searches given folder and all sub folders for PDFs
# Collects citation info from JSTOR or Persee formats
# Adds RIS foramt entries to a file

# Added requirements.txt for easier setup
# Added to Github
# Added dev tools
# Added README

risEntries = []
anomalies = []

# Want any counts for resource type?
numJSTOR = 0
numPersee = 0
numOther = 0
numFileName = 0
numBrill = 0

# Has tests
def findInfo(pdf_path):
    try:
        doc = fitz.open(pdf_path)
    except Exception as e:
        print("Exception opening file: ", e)
        return
    page = doc[0]
    global numFileName
    global numJSTOR
    global numPersee
    global numOther
    global numBrill

    # page.search_for returns a list of location rectangles

    # JSTOR
    sourceRec = page.search_for("Source")
    # Persee/French
    citeThisDocRec = page.search_for("Citer ce document")  # Persee is always French
    # Brill
    abstractRec = page.search_for("Abstract")

    # Converts to RIS format (seems easiest)
    # See https://en.wikipedia.org/wiki/RIS_(file_format)#:~:text=RIS%20is%20a%20standardized%20tag,a%20number%20of%20reference%20managers.

    if abstractRec:
        print("Update: Using Brill format")
        output, addToBrillCount = findInfoBrill(page, abstractRec[0], pdf_path)
        if addToBrillCount == 2:
            numFileName += 1
            numOther += 1
        else:
            numBrill += addToBrillCount
    elif sourceRec:
        print("Update: Using JSTOR format")
        output, addToJSTORCount = findInfoJSTOR(page, pdf_path)
        if addToJSTORCount == 2:
            numFileName += 1
            numOther += 1
        else:
            numJSTOR += addToJSTORCount
    elif citeThisDocRec:
        print("Update: Using Persee format")
        output, addToPerseeCount = findInfoPersee(page, citeThisDocRec[0], pdf_path)
        if addToPerseeCount == 2:
            numFileName += 1
            numOther += 1
        else:
            numPersee += addToPerseeCount
    else:
        print(
            "Update: Didn't identify a known format (from JSTOR or Persee) - will use a general format"
        )
        output = generalInfoCollector(pdf_path, {})
        numFileName += 1
        numOther += 1

    risEntries.append(output)


# Does this need a test?
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


# Does this function need a test?
def main():
    outputFilePath, inputFolderPath = getCommandLineArguments()

    # If no input path, there's nothing left to run
    if not checkInputPathExists(inputFolderPath):
        print("Update: Exiting program")
        return

    outputFile = checkOutputFileType(outputFilePath, inputFolderPath)

    paths = searchFolder(inputFolderPath)
    if not paths or len(paths) == 0:
        # print("Update: No PDFs found")
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
    print("Update: Searched file names for info for ", str(numFileName), " PDFs")

    if risEntries:
        createBiblio(outputFile, risEntries)
    else:
        print("Update: There are no biblio entries to write")

    print("Updated: Finished")


if __name__ == "__main__":
    main()
