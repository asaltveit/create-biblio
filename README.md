# Create Biblio
Creates a citation for each PDF in a given folder (and all sub-folders) and adds them to an RIS file which can be uploaded to Zotero and/or other programs which accept RIS format.

Any output file may need to be cleaned up by the user.

## First Time Set-up
1. If you don't have git, you'll need to install it:
- https://git-scm.com/book/en/v2/Getting-Started-Installing-Git
2. If you don't have Python3, install that:
- For Mac users: https://www.python.org/downloads/macos/
- For Windows users: https://www.python.org/downloads/windows/
- For Linux/Unix users: https://www.python.org/downloads/source/
- For other users: https://www.python.org/download/other/
3. pip should be included with Python3, but if it isn't, see here:
- https://pip.pypa.io/en/stable/installation/
4. Clone this repo to your local computer:
   ```bash
   git clone https://github.com/asaltveit/create-biblio.git
   ```
5. Enter the project folder:
   ```bash
   cd create-biblio
   ```
6. Create a virtual environment to install the dependencies in:
   ```bash
   python -m venv .venv
   ```
7. Start the virtual environment:
- For windows:
   ```bash
   .venv\Scripts\activate.bat
   ```
- For MacOS:
   ```bash
   source .venv/bin/activate
   ```
8. Install the package prerequisites for this project:
   ```bash
   pip install -r requirements.txt
   ```
9. If you're setting up for development, you can install both the program and dev requirements with:
   ```bash
   pip install -r requirements-dev.txt
   ```

## Returning Set-up
1. Enter the project folder:
   ```bash
   cd create-biblio
   ```
2. Start the virtual environment:
- For windows:
   ```bash
   .venv\Scripts\activate.bat
   ```
- For MacOS:
   ```bash
   source .venv/bin/activate
   ```

### To fetch updates:
Follow the instructions for Returning Set-up, then use: 
   ```  git pull origin main  ```

## Run
```bash
python create_biblio.py --inputPath="path/to/folder" --outputPath="optional/path/to/file.ris"
```
If you get a python error, try:
```bash
python3 create_biblio.py --inputPath="path/to/folder" --outputPath="optional/path/to/file.ris"
```

Program outputs: 
- file.ris

## Trouble Shooting
If you end up with multiple python virtual environments, here are the commands to find and delete them.
1. Make sure you're not currently in a venv with:
   ```bash
   deactivate
   ```
2. To find all venvs:
- Windows' CMD: ```  dir activate /A /s  ```
  - Searches in the current directory
- MacOS Terminal: ``` find path/to/directory/to/search -name activate ```
3. Delete venvs (one at a time):
- Windows' CMD: ```  rd /s /q "path/to/.venv/directory/to/delete"  ```
- MacOS Terminal: ``` rm -r "path/to/.venv/directory/to/delete" ```


### Notes
- If the output file name is not given, default creates the file name from the input path like "path/to/folder" -> folder.ris
- The output file will be placed in the input folder
- The output file will include citation info for all PDFs.
- The .ris file won't be written to if there are no citations to write.


## Further Work
- A full set of unit tests
- Additional output file types
- Possibly incorporate computer vision


