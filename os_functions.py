import os


def searchFolder(search_path: str):
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


def checkInputPathExists(file: str):
    try:
        path = os.path.exists(file)
        if path:
            # print("Update: Input path exists")
            return True
        else:
            print("Error: Input path does not exist")
            return False
    except PermissionError:
        print("Permission error: Unable to access the file.")
        return False
    except OSError as e:
        print("Error: Cannot access input folder: " + e)
        return False
    except ValueError as e:
        print("Error: Cannot access input folder: " + e)
        return False


def checkOutputFileType(file: str, inputPath: str):
    if not file:
        return getLastInputPathParameter(inputPath)
    elif not file.endswith(".ris"):
        return file.split(".")[0] + ".ris"
    else:
        return file


# TODO Update readme to reflect where output file will go
def getLastInputPathParameter(inputPath: str):
    folderName = os.path.basename(os.path.normpath(inputPath))
    fileName = folderName + ".ris"
    return os.path.join(inputPath, fileName)
