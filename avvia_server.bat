@echo off
rem Porta 8130 — la stessa del server (struttura_server_ubuntu/server/servizi.txt):
rem la 8120 era gia' presa da Listino Rivenditori nel frattempo, vedi
rem struttura_server_ubuntu issue #2. Va tenuta allineata a
rem .claude/launch.json e ad AVVIA OPERX.bat: cambiarla in un posto solo
rem spegne il modulo (stessa nota di richiesta_fattibilita_api).
cd /d "%~dp0"
rem NIENTE --reload: vedi richiesta_bozzetti_api/avvia_server.bat per il
rem motivo (due processi uvicorn, la X chiude solo il sorvegliante — la
rem porta resta occupata e il riavvio fallisce con "Errno 10048").
venv\Scripts\uvicorn.exe app.main:app --port 8130 --host 0.0.0.0
