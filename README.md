# Create Biblio
Creates a citation for each PDF in a given folder (and all sub-folders) and adds them to an RIS file which can be uploaded to Zotero and/or other programs which accept RIS format.

Any output file may need to be cleaned up by the user.

## Set-up
1. If you don't have git, you'll need to install it:
- https://git-scm.com/book/en/v2/Getting-Started-Installing-Git
2. Clone this repo to your local computer:
   ```bash
   git clone https://github.com/asaltveit/create-biblio.git
   ```
3. Enter the project folder:
   ```bash
   cd create-biblio
   ```
4. If you don't have Python3, install that:
- For Mac users: https://www.python.org/downloads/macos/
- For Windows users: https://www.python.org/downloads/windows/
- For Linux/Unix users: https://www.python.org/downloads/source/
- For other users: https://www.python.org/download/other/
5. pip should be included with Python3, but if it isn't, see here:
- https://pip.pypa.io/en/stable/installation/

### For Windows
6. Create a virtual environment to install the dependencies in:
   ```bash
   python -m venv .venv
   ```
7. Start the virtual environment:
   ```bash
   .venv\Scripts\activate.bat
   ```

### For every other operating system
6. Create a virtual environment to install the dependencies in:
   ```bash
   python3 -m venv .venv
   ```
7. Start the virtual environment:
   ```bash
   source .venv/bin/activate
   ```

### Continuing for everyone
8. Install the package prerequisites for this project:
   ```bash
   pip install -r requirements.txt
   ```
9. If you're setting up for development, you can install both the program and dev requirements with:
   ```bash
   pip install -r requirements-dev.txt
   ```

## Run
```bash
python3 create_biblio.py --inputPath="path/to/folder" --outputPath="optional/path/to/file.ris"
```
If you get a python error, try:
```bash
python create_biblio.py --inputPath="path/to/folder" --outputPath="optional/path/to/file.ris"
```


Outputs: 
- file.ris

### Notes
- If the output file name is not given, default creates the file name from the input path like "path/to/folder" -> folder.ris
- The output file will be placed in the input folder
- The output file will include citation info for all PDFs.
- The .ris file won't be written to if there are no citations to write.


## Further Work
- A full set of unit tests
- Additional output file types


