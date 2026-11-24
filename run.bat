@echo off
if exist .venv\Scripts\python.exe (
    .\.venv\Scripts\python.exe app\main.py %*
) else (
    python app\main.py %*
)
