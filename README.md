# Create Biblio
Creates a citation for each PDF in a given folder (and all sub-folders) and adds them to an RIS file which can be uploaded to Zotero and/or other programs which accept RIS format.

## Set-up
### Install Prerequisites
1. Clone this repo to your local computer:
   ```bash
   git clone https://github.com/asaltveit/create-biblio.git
   ```
2. Enter the project folder:
   ```bash
   cd create-biblio
   ```
3. If you don't have Python3, install that:
- For Mac users: https://www.python.org/downloads/macos/
- For Windows users: https://www.python.org/downloads/windows/
- For Linux/Unix users: https://www.python.org/downloads/source/
- For other users: https://www.python.org/download/other/
4. pip should be included with Python3, but if it isn't, see here:
- https://pip.pypa.io/en/stable/installation/
5. Create a virtual environment to install the dependencies in:
   ```bash
   python3 -m venv .venv
   ```
6. Start the virtual environment:
   ```bash
   source .venv/bin/activate
   ```
6. Install the package prerequisites for this project:
   ```bash
   pip install -r requirements.txt
   ```
7. If you're setting up for development, you can install both the program and dev requirements with:
   ```bash
   pip install -r dev-requirements.txt
   ```

## Run
```bash
python3 create-biblio.py --inputPath="path/to/folder" --outputPath="optional/path/to/file.ris"
```
Outputs: 
- file.ris
- anomalies.txt

### Notes
- If the output file is not given, or does not exist, default uses the input path like "path/to/folder" -> folder.ris
- If the output file exists and is not empty, you'll be asked whether to (1) write over the file, (2) delete the file contents, or (3) exit the program
- The output file will include citation info for all PDFs that fit the structure from JSTOR, Persee, and the Middlebury Library. If a PDF doesn't fit one of those structures, it will be added to the anomalies.txt file.
- The .ris file won't be written to if there are no citations to write.
- The anomalies.txt file won't be written to if there are no anomalies.

## Further Work
- A full set of unit tests
- Additional PDF format types and output file types


