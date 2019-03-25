#!/bin/bash

# Author: Egbe Eugene
# Description: Check system and install deps

# Checks if Python 3 and pip is installed before executing
if command -v python3 &>/dev/null; then
	echo -e "\n\033[1;32mChecking your system for Python 3..."
	echo -e "\033[1;32m[OK] Python 3 is installed\n"
	if command -v pip &>/dev/null || command -v pip3 &>/dev/null; then
		echo -e "\033[1;32mChecking if pip (Python Dependency Manager) is installed...\033[0m"
		echo -e "\033[1;32m[OK] pip is installed, now installing dependencies...\n\033[0m"
	else
		echo -e "\033[1;32mpip is not installed, aborting...\033[0m"
		exit 1 
	fi
else
	echo -e "\033[1;32mPython 3 is not installed, aborting...\033[0m"
	exit 1
fi

pip3 install -r requirements.txt

echo -e "\n\033[1;32mYou may now run the application now!\033[0m"