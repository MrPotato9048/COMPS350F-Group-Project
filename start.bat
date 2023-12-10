@echo off
py -m venv venv
CALL venv\Scripts\activate.bat
pip install -r requirements.txt
set FLASK_APP=__init__.py
flask run