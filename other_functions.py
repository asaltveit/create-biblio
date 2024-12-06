import rispy


def createBiblio(outputFile, risEntries):
    print("Update: Creating RIS file")
    try:
        with open(outputFile, "w") as ris_file:
            rispy.dump(risEntries, ris_file)
    except Exception as e:
        print("Error: Writing to RIS file failed: ", e)
    else:
        print("Update: Successfully wrote to RIS file")
