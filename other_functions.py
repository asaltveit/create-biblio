import rispy
import argparse  # To collect arguments from command line # using argparse-1.4.0


def createBiblio(outputFile, risEntries):
    print("Update: Creating RIS file")
    try:
        with open(outputFile, "w") as ris_file:
            rispy.dump(risEntries, ris_file)
    except Exception as e:
        print("Error: Writing to RIS file failed: ", e)
    else:
        print("Update: Successfully wrote to RIS file")


# Has tests
def getCommandLineArguments(args=None):
    parser = argparse.ArgumentParser(description="Creates ris file from PDF")
    # Takes input path from command line
    parser.add_argument(
        "--inputPath", required=True, type=str, help="Enter path of input folder"
    )
    # Also takes optional output path from command line
    parser.add_argument(
        "--outputPath",
        required=False,
        type=str,
        default="",
        help="Enter path of output RIS file",
    )
    arguments = parser.parse_args(args)
    return arguments.outputPath, arguments.inputPath
