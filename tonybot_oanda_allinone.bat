@echo off
title Tonybot OANDA v180 - All in One
echo ===============================
echo   TONYBOT OANDA v180 - START
echo ===============================
echo.

REM === 1. Stažení svíček z OANDY ===
echo [1/6] Stahuju svíčky z OANDY...
python download_candles.py
if %errorlevel% neq 0 (
    echo CHYBA: Nepodarilo se stahnout data!
    pause
    exit /b
)

REM === 2. Generování indikátorů ===
echo [2/6] Generuju indikátory...
python generate_indicators_full_v180.py
if %errorlevel% neq 0 (
    echo CHYBA: Nepodarilo se vygenerovat indikatory!
    pause
    exit /b
)

REM === 3. Generování trénovacích dat ===
echo [3/6] Připravuju trénovací data...
python generate_training_data_v180.py
if %errorlevel% neq 0 (
    echo CHYBA: Trénovací data selhala!
    pause
    exit /b
)

REM === 4. Trénování modelu ===
echo [4/6] Trénuju model...
python train_model_oanda_v180_time_split.py
if %errorlevel% neq 0 (
    echo CHYBA: Trénink selhal!
    pause
    exit /b
)

REM === 5. Vytvoření ensemble modelu ===
echo [5/6] Tvořím ensemble model...
python create_ensemble_model_v180.py
if %errorlevel% neq 0 (
    echo CHYBA: Ensemble model selhal!
    pause
    exit /b
)

REM === 6. Spuštění bota ===
echo [6/6] Spouštím obchodního bota...
python tonybot_oanda_v180_loop.py
