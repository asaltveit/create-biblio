import pymupdf

from parse_info_functions import (
    generalInfoCollector,
    getInfoFromFileName,
    findInfoPersee,
    findInfoJSTOR,
    findInfoBrill,
)
from os_functions import (
    searchFolder,
    checkOutputFileType,
    checkInputPathExists,
)

from other_functions import createBiblio, getCommandLineArguments, handlePlurals

# Searches given folder and all sub folders for PDFs
# Collects citation info from JSTOR or Persee formats
# Adds RIS foramt entries to a file


risEntries = []
anomalies = []

numJSTOR = 0
numPersee = 0
numOther = 0
numFileName = 0
numBrill = 0

# Has tests
def findInfo(pdf_path):
    try:
        doc = pymupdf.open(pdf_path)
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
        # print(
        #    "Update: Didn't identify a known format (from JSTOR or Persee or Brill) - will use a general format"
        # )
        # getInfoFromFileName returns (dict, num)
        fileNameInfo = getInfoFromFileName(pdf_path)[0]
        output = generalInfoCollector(page, fileNameInfo)
        numFileName += 1
        numOther += 1

    risEntries.append(output)


# Has test
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
    print(handlePlurals(numJSTOR, "JSTOR"))
    print(handlePlurals(numPersee, "Persee"))
    print(handlePlurals(numOther, "an unknown format"))
    print("Update: Searched file names for info for ", str(numFileName), " PDFs")

    if risEntries:
        createBiblio(outputFile, risEntries)
    else:
        print("Update: There are no biblio entries to write")

    print("Updated: Finished")


if __name__ == "__main__":
    main()
