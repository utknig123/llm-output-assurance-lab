"""
LoRA Fine-tuning script for distilgpt2 critique model
"""
import os
import sys
import subprocess
import json

# Disable distributed training
os.environ["CUDA_VISIBLE_DEVICES"] = ""
os.environ["WORLD_SIZE"] = "1"
os.environ["RANK"] = "0"
os.environ["LOCAL_RANK"] = "-1"

import torch
from transformers import (
    AutoTokenizer,
    AutoModelForCausalLM,
    TrainingArguments,
    Trainer,
    DataCollatorForLanguageModeling
)
from peft import LoraConfig, get_peft_model, TaskType
from datasets import Dataset

def load_formatted_data(data_file="data/formatted_training_data.json"):
    """Load formatted training data"""
    data_path = os.path.join(os.path.dirname(__file__), data_file)
    
    with open(data_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    return data

def tokenize_function(examples, tokenizer, max_length=512):
    """Tokenize input-output pairs"""
    texts = []
    inputs = examples['input'] if isinstance(examples['input'], list) else [examples['input']]
    outputs = examples['output'] if isinstance(examples['output'], list) else [examples['output']]
    
    for i in range(len(inputs)):
        combined = inputs[i] + "\n\nCritique:\n" + outputs[i] + tokenizer.eos_token
        texts.append(combined)
    
    tokenized = tokenizer(
        texts,
        truncation=True,
        max_length=max_length,
        padding="max_length",
        return_tensors=None
    )
    
    tokenized["labels"] = tokenized["input_ids"].copy()
    return tokenized

def setup_model_and_tokenizer(model_name="distilgpt2"):
    """Setup model and tokenizer with LoRA"""
    print(f"Loading base model: {model_name}")
    
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    
    model = AutoModelForCausalLM.from_pretrained(
        model_name,
        torch_dtype=torch.float32
    )
    model = model.to('cpu')
    
    lora_config = LoraConfig(
        r=16,
        lora_alpha=32,
        target_modules=["c_attn"],
        lora_dropout=0.05,
        bias="none",
        task_type=TaskType.CAUSAL_LM
    )
    
    model = get_peft_model(model, lora_config)
    model.print_trainable_parameters()
    
    return model, tokenizer

def train_model(
    model,
    tokenizer,
    train_dataset,
    val_dataset,
    output_dir="models/distilgpt2-critique-lora",
    num_epochs=3,
    batch_size=4,
    learning_rate=5e-4
):
    """Train the model with LoRA"""
    
    training_args = TrainingArguments(
        output_dir=output_dir,
        num_train_epochs=num_epochs,
        per_device_train_batch_size=batch_size,
        per_device_eval_batch_size=batch_size,
        learning_rate=learning_rate,
        warmup_steps=100,
        logging_steps=50,
        eval_steps=200,
        save_steps=200,
        eval_strategy="steps",
        save_strategy="steps",
        load_best_model_at_end=True,
        metric_for_best_model="eval_loss",
        greater_is_better=False,
        fp16=False,
        dataloader_pin_memory=False,
        report_to="none",
        use_cpu=True
    )
    
    data_collator = DataCollatorForLanguageModeling(
        tokenizer=tokenizer,
        mlm=False
    )
    
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=val_dataset,
        data_collator=data_collator,
    )
    
    print("\n🚀 Starting training...")
    trainer.train()
    
    final_output = os.path.join(output_dir, "final")
    model.save_pretrained(final_output)
    tokenizer.save_pretrained(final_output)
    print(f"\n✅ Model saved to {final_output}")
    
    return trainer

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser()
    parser.add_argument("--epochs", type=int, default=3)
    parser.add_argument("--batch_size", type=int, default=4)
    parser.add_argument("--learning_rate", type=float, default=5e-4)
    parser.add_argument("--data_file", type=str, default="data/formatted_training_data.json")
    args = parser.parse_args()
    
    print("=" * 60)
    print("LoRA Fine-tuning for distilgpt2 Critique Model")
    print("=" * 60)
    
    print("\n📂 Loading training data...")
    data = load_formatted_data(args.data_file)
    
    dataset = Dataset.from_list(data)
    split_dataset = dataset.train_test_split(test_size=0.1, seed=42)
    
    print("\n🤖 Setting up model and tokenizer...")
    model, tokenizer = setup_model_and_tokenizer()
    
    print("\n🔤 Tokenizing datasets...")
    train_dataset = split_dataset['train'].map(
        lambda x: tokenize_function(x, tokenizer),
        batched=True,
        remove_columns=split_dataset['train'].column_names
    )
    val_dataset = split_dataset['test'].map(
        lambda x: tokenize_function(x, tokenizer),
        batched=True,
        remove_columns=split_dataset['test'].column_names
    )
    
    trainer = train_model(
        model,
        tokenizer,
        train_dataset,
        val_dataset,
        num_epochs=args.epochs,
        batch_size=args.batch_size,
        learning_rate=args.learning_rate
    )
    
    print("\n🎉 Training complete!")
