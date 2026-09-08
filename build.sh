#!/usr/bin/env bash
# exit on error
set -o errexit

echo "Installing pip requirements (bypassing uv lock)"
python3 -m pip install -r requirements.txt --break-system-packages

echo "Collecting static files..."
python3 manage.py collectstatic --no-input

echo "Running database migrations..."
python3 manage.py migrate
