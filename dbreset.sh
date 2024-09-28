#!/usr/bin/env bash

python3 manage.py makemigrations chess
python3 manage.py migrate
python3 manage.py createsuperuser

python3 manage.py import_data github/volunteers2024.csv github/classes2024.csv github/players2024.csv