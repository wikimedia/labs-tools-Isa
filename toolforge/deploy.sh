#! /usr/bin/env bash

run() {
    preview "$*"
    read -r -p "Run this command? [Y/n] "
    if [[ $REPLY =~ ^[Nn]$ ]]
    then
        exit 1
    fi

    if ! eval "$*"
    then
        warn "The previous command didn't exit properly. Check the output above and make sure that things are fine before proceeding."
    fi
}

info() {
    echo -e "\e[1;44m$*\e[0m"
}

warn() {
    echo -e "\e[1;43mWARNING: $*\e[0m"
}

error() {
    echo -e "\e[1;41mERROR: $*\e[0m"
}

preview() {
    echo -e "\e[1;36m$*\e[0m"
}

pip() {
    webservice python3.11 shell -- ~/www/python/venv/bin/pip "$@"
}

if [ ! $DATABASE ]
then
    error The environment variable DATABASE must be set to the ISA database.
    exit 1
fi

info "This script will go through the steps to deploy ISA as a tool on
Toolforge. You will be prompted before each step to make sure that the
command in question should be run. If a command fails there will be a
warning message, but you can still continue with the deployment. On
the other hand some commands may give warnings, but not exit with an
error. Always check the output before running the next command."

timestamp=$(date -I -u)
src=~/www/python/src/

cd $src || exit 1

# When adding new steps, take care if redirection is used. Quote those
# commands when sent to `run` to make them display and run properly.

# Stop webservice
run webservice stop

# Stop Celery worker
run 'toolforge jobs delete celery-worker'

# Backup database
mask=$(umask)
umask o-r
run "mysqldump --defaults-file=$HOME/replica.my.cnf -h tools.db.svc.wikimedia.cloud $DATABASE > $timestamp.sql"
umask $mask

# Tag current repo state
run git tag --force $timestamp

# Pull repo
run git pull

# Clear Python packages
if [[ $(pip freeze) ]]
then
    # Make this a non expanded string to not have the whole list in
    # the prompt.
    run 'pip uninstall -y $(pip freeze)'
fi

# Install Python packages
run pip install -r $src/requirements.txt

# Clean install node packages
# `npm ci` fails on Toolforge, so we have to remove things ourselves.
run rm -rf node_modules
run npm i

# Build javascripts
run rm -r isa/static/js/
run npm run build

# Start Celery worker
run 'toolforge-jobs run --continuous --image python3.11 --command "~/www/python/src/toolforge/start-celery.sh" celery-worker'

# Start webservice
run webservice start
