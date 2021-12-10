# Isa

This tool helps to describe the images contributed to Wiki Loves competitions.

Isa is not only an acronym for information structured additions, but is also a [chiShona](https://sn.wikipedia.org/wiki/ChiShona) language word for ‘put’.

# Requirements

* [Python 3.x+](https://www.python.org/downloads/)
* [PIP (Python Dependency Manager)](https://pip.pypa.io/en/stable/installing/)

## Installing dependencies

Install application dependencies using the `get-deps.sh` script:
```bash 
./get-deps.sh
```
The above script attempts to check system requirements and informs user on next steps.

## Quickstart the app
```bash
export FLASK_APP=app.py # add --reload parameter to enable Flask auto-compilation feature
flask run
```

## Managing Translations

Steps 1 to 3a below show how to extract and generate translation files from the
source code.

Start from step 3b if you are *only* adding a new supported language for the app.

Start from step 4 if you are *only* adding translated text for already supported
languages.

Skip directly to step 5 if you have pulled changes which include updated
translations (edited .po files).

*All commands should be run from the /isa subfolder.*

### 1. Add or edit translatable text in source code
Mark new strings to be translated using formats shown below:
 * Templates: _('<string>')
 * Python: gettext('<string>')

### 2. Extract strings to .pot file
run ```pybabel extract -F babel.cfg -o messages.pot --input-dirs=.```
This step is only needed after changes have been made to translatable text
in the source code in step 1.

### 3a. Update .po files
run ```pybabel update -i messages.pot -d translations -l <lang_code>``` 
Use this command to *update* .po files for each supported language. 

It will merge in any new strings found in the .pot file generated in step 2.
Any strings that are no longer found are placed at the bottom of the file, using
commented out lines beginning with #~

### 3b. Create new .po file
run ```pybabel init -i messages.pot -d translations -l <lang_code>```
Use this command to create a *new* .po file.

This step is only needed when adding a new supported language.
Commit the new .po file to source control.

### 4. Add new translations
Add the actual translated text for each language to the corresponding .po file
located at isa/translations/<lang_code>/LC_MESSAGES/messages.po

This step should be completed by translators, so can happen at any time.
Commit any changes to .po files to source control.

### 5. Compile final .mo file
run ``` pybabel compile -d translations ```
Once translations are ready from step 4 (or from pulling changes with
updated .po files), you need run the compile command before seeing the new
translations in the app.

# Testing the application

- To run tests from the applications root directory, use the command `nose2 -v tests.<test_module_name>`

- To get a blueprint's coverage, run following commands:

    - From the applications root directory, run `coverage run -m unittest discover`
    - Then run `coverage report -m isa/<blueprint_name>/*.py>`

# Maintenance scripts
Maintenance scripts are found in isa/maintenance. Run them as modules in the root directory, e.g. `python -m isa.maintenance.update_store_images`.