#! /usr/bin/env bash

cd ~/www/python/src
source ~/www/python/venv/bin/activate
celery -A isa.celery_app --config isa/config.yaml worker --loglevel DEBUG
