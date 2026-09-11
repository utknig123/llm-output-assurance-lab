@echo off
REM Complete pipeline script for Model B fine-tuning (Windows)

echo ==========================================
echo Model B Fine-tuning Pipeline
echo ==========================================

REM Step 1: Generate synthetic data
echo.
echo Step 1: Generating synthetic data...
python generate_synthetic_data.py
if errorlevel 1 (
    echo [ERROR] Data generation failed
    exit /b 1
)

REM Step 2: Format data
echo.
echo Step 2: Formatting data for training...
python format_data_for_training.py
if errorlevel 1 (
    echo [ERROR] Data formatting failed
    exit /b 1
)

REM Step 3: Train model
echo.
echo Step 3: Training model with LoRA...
python train_lora.py --epochs 3 --batch_size 4 --learning_rate 5e-4
if errorlevel 1 (
    echo [ERROR] Training failed
    exit /b 1
)

REM Step 4: Test model
echo.
echo Step 4: Testing fine-tuned model...
python test_finetuned_model.py
if errorlevel 1 (
    echo [ERROR] Testing failed
    exit /b 1
)

echo.
echo ==========================================
echo Pipeline complete!
echo ==========================================

