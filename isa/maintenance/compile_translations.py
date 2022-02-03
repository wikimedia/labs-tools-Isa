"""Compile translation files

Pulls git updates and preprocesses and compiles all .po files in the
translation directory.

"""

import argparse
import glob
from subprocess import run as run_subprocess
import sys

from babel.messages import pofile


PO_PATH = "isa/translations/*/LC_MESSAGES/messages.po"


def update_repo():
    run("git pull")


def run(command):
    print("\033[0;34m> {}\033[00m".format(command))
    process = run_subprocess(command, shell=True)
    if process.returncode:
        print("\033[0;31mError while running command, see above.\033[00m", file=sys.stderr)
        sys.exit(1)


def preprocess_files():
    # Turn lines like
    # "PO-Revision-Date: 2022-01-13 12:14:49+0000\n"
    # into
    # "PO-Revision-Date: 2022-01-13 12:14+0000\n"
    # This is needed since Babel gets an error if minutes are included
    # in the date on those lines.
    replace = r"s/(PO-Revision-Date:.+[0-9]{2}:[0-9]{2}):[0-9]{2}(\+[0-9]{4})/\1\2/g"
    command = 'sed -i -r "{}" {}' .format(replace, PO_PATH)
    run(command)


def compile_translations():
    catalogs = [pofile.read_po(open(f)) for f in glob.glob(PO_PATH)]
    command = "pybabel compile -d isa/translations/ -l"
    for catalog in catalogs:
        if not catalog.locale:
            # Skip if not a proper locale, e.g. "qqq".
            continue

        translated = []
        for message in catalog:
            if message.string and message.id:
                # This message has a translation.
                translated.append(message)

        # Exclude empty messages from total.
        all_messages = [m for m in catalog if m.id]
        progress = len(translated) / len(all_messages)
        print("Progress for {}: {:.2f}% = ({} / {})".format(
            catalog.locale.language,
            progress * 100,
            len(translated),
            len(all_messages)
        ))
        if not args.threshold or progress >= args.threshold / 100:
            run(command + " {}".format(catalog.locale.language))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--threshold",
        "-t",
        type=int,
        help=(
            "Compile only languages that have at least this much of "
            "the messages translated, in percent."
        )
    )
    args = parser.parse_args()

    update_repo()
    preprocess_files()
    compile_translations()
