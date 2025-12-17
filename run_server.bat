@echo off
cd /d "d:\My Own Learning\Prompt Engineer\Project Files\JuniorDebug\backend"
call venv\Scripts\activate.bat
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000