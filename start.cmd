@echo off
chcp 65001
setlocal

if not exist .venv (
    echo .venv not found. creating...
    python -m venv .venv
)


call .venv\Scripts\activate

echo .venv activate check...
where python
python -m pip --version

echo install dependencies from file requirements.txt...
pip install -r requirements.txt

echo launch...
python main.py

pause

endlocal
