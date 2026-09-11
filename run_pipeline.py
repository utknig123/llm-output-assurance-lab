"""
Complete pipeline script for Model B fine-tuning
Run this with: python run_pipeline.py
"""
import subprocess
import sys
import os

def run_command(command, description):
    """Run a command and handle errors"""
    print(f"\n{'='*60}")
    print(f"{description}")
    print(f"{'='*60}")
    print(f"Running: {command}")
    
    result = subprocess.run(command, shell=True)
    
    if result.returncode != 0:
        print(f"\n❌ {description} failed with exit code {result.returncode}")
        sys.exit(1)
    
    print(f"✅ {description} completed successfully")
    return result

def main():
    print("="*60)
    print("Model B Fine-tuning Pipeline")
    print("="*60)
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    
    # Step 1: Generate synthetic data (SKIPPED - data already generated)
    print("\n" + "="*60)
    print("Step 1: Generating synthetic data - SKIPPED")
    print("="*60)
    print("✅ Using existing data from data/synthetic_critique_data.json")
    
    # Step 2: Format data
    run_command(
        "python format_data_for_training.py",
        "Step 2: Formatting data for training"
    )
    
    # Step 3: Train model
    run_command(
        "python train_lora.py --epochs 3 --batch_size 4 --learning_rate 5e-4",
        "Step 3: Training model with LoRA"
    )
    
    # Step 4: Test model
    run_command(
        "python test_finetuned_model.py",
        "Step 4: Testing fine-tuned model"
    )
    
    print("\n" + "="*60)
    print("✅ Pipeline complete!")
    print("="*60)

if __name__ == "__main__":
    main()
