#!/bin/bash
# Complete pipeline script for Model B fine-tuning

echo "=========================================="
echo "Model B Fine-tuning Pipeline"
echo "=========================================="

# Step 1: Generate synthetic data
echo ""
echo "Step 1: Generating synthetic data..."
python generate_synthetic_data.py

if [ $? -ne 0 ]; then
    echo "❌ Data generation failed"
    exit 1
fi

# Step 2: Format data
echo ""
echo "Step 2: Formatting data for training..."
python format_data_for_training.py

if [ $? -ne 0 ]; then
    echo "❌ Data formatting failed"
    exit 1
fi

# Step 3: Train model
echo ""
echo "Step 3: Training model with LoRA..."
python train_lora.py --epochs 3 --batch_size 4 --learning_rate 5e-4

if [ $? -ne 0 ]; then
    echo "❌ Training failed"
    exit 1
fi

# Step 4: Test model
echo ""
echo "Step 4: Testing fine-tuned model..."
python test_finetuned_model.py

if [ $? -ne 0 ]; then
    echo "❌ Testing failed"
    exit 1
fi

echo ""
echo "=========================================="
echo "✅ Pipeline complete!"
echo "=========================================="

