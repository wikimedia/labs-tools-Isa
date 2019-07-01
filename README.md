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
The above script attempts to check system requirements and tell informs user on next steps.

## Quickstart the app
```bash
export FLASK_APP=app.py # add --reload parameter to enable Flask auto-compilation feature
flask run
```

## Adding Translations

To add translations, the following steps should be followed

- Mark the string to be translated ( _('<string>') for templates ) and ( gettext('<string>') ) for python strings

- run ```pybabel extract -F babel.cfg -o messages.pot --input-dirs=.``` from the *isa* module to extract the strings

- run ```pybabel init (update in case you are modifying) -i messages.pot -d translations -l <lang_code>``` to generate translations in a new language with code <lang_code>

- Enter the strings corresponding translations in 'translations/<lang_code>/LC_MESSAGES/messages.po'

- run ``` pybabel compile -d translations ``` to compile the translations