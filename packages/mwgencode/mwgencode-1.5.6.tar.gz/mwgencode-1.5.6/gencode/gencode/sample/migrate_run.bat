#!/usr/bin/env bash
set FLASK_APP=migrate_run.py
flask db init
flask db migrate
flask db upgrade