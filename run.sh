#!/bin/bash
#. venv/bin/activate
export FLASK_APP=./servidor.py
#source $(pipenv --venv)/bin/activate
#export FLASK_ENV="development"
flask run -h 0.0.0.0

