from subprocess import run as run_subprocess
import sys


def run(command, cwd=None):
    print("\033[0;34m> {}\033[00m".format(command))
    process = run_subprocess(command, shell=True, cwd=cwd)
    if process.returncode:
        print("\033[0;31mError while running command, see above.\033[00m", file=sys.stderr)
        sys.exit(1)
