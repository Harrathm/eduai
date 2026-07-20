@echo off
cd /d "E:\system_educatif_tn\RAG\RAG_APP_new\backend"
python -m uvicorn app.main:app --port 8000
