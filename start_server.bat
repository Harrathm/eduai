@echo off
cd /d E:\system_educatif_tn\RAG\RAG_APP_new\backend
call .venv\Scripts\activate.bat
python -m uvicorn app.main:app --port 8000 --reload