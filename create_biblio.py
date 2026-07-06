import pymupdf

from parse_info_functions import (
    generalInfoCollector,
    getInfoFromFileName,
    findInfoPersee,
    findInfoJSTOR,
    findInfoBrill,
    getStructuredLines,
)
from line_features import structured_lines_to_features
from line_classifier import maybe_apply_ml_fallback
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

use_ml = False


def _maybe_ml_enhance(page, output):
    if not use_ml:
        return output
    structured_lines = getStructuredLines(page)
    feature_dicts = structured_lines_to_features(
        structured_lines, page_height=page.rect.height
    )
    return maybe_apply_ml_fallback(output, structured_lines, feature_dicts, use_ml=True)


# Has tests
def findInfo(pdf_path):
    try:
        doc = pymupdf.open(pdf_path)
    except Exception as e:
        print("Exception opening file: ", e)
        return
    print("doc.metadata " + str(doc.metadata))
    page = doc[0]
    global numFileName
    global numJSTOR
    global numPersee
    global numOther
    global numBrill

    sourceRec = page.search_for("Source")
    citeThisDocRec = page.search_for("Citer ce document")
    abstractRec = page.search_for("Abstract")

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
        print("Update: PDF is from Persee")
        output, addToPerseeCount = findInfoPersee(page, citeThisDocRec[0], pdf_path)
        if addToPerseeCount == 2:
            numFileName += 1
            numOther += 1
        else:
            numPersee += addToPerseeCount
    else:
        print(
            "Update: Didn't identify a known format (from JSTOR or Persee or Brill) - will use a general format"
        )
        fileNameInfo = getInfoFromFileName(pdf_path)[0]
        output = generalInfoCollector(page, fileNameInfo, use_ml=use_ml)

    output = _maybe_ml_enhance(page, output)
    risEntries.append(output)


# Has test
def main():
    global use_ml
    outputFilePath, inputFolderPath, use_ml = getCommandLineArguments()

    if not checkInputPathExists(inputFolderPath):
        print("Update: Exiting program")
        return

    outputFile = checkOutputFileType(outputFilePath, inputFolderPath)

    paths = searchFolder(inputFolderPath)
    if not paths or len(paths) == 0:
        print("Update: No output files created")
        print("Update: Finished")
        return
    for path in paths:
        print("Update: Finding info for - ", path)
        findInfo(path)
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
