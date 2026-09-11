"""
Test the fine-tuned critique model
"""
import os
import sys
import subprocess

# Auto-install missing dependencies
def install_if_missing(module_name, package_name=None):
    if package_name is None:
        package_name = module_name
    try:
        __import__(module_name)
    except ImportError:
        print(f"⚠️ {module_name} not found. Installing {package_name}...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", package_name])
        print(f"✅ {package_name} installed successfully")

# Check and install dependencies
install_if_missing("torch")
install_if_missing("transformers")
install_if_missing("peft")

import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from peft import PeftModel

def load_finetuned_model(model_path="models/distilgpt2-critique-lora/final"):
    """Load fine-tuned model"""
    model_path = os.path.join(os.path.dirname(__file__), model_path)
    
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Model not found: {model_path}")
    
    print(f"Loading fine-tuned model from {model_path}")
    
    # Load base model
    base_model = AutoModelForCausalLM.from_pretrained(
        "distilgpt2",
        torch_dtype=torch.float32
    )
    
    # Load LoRA weights
    model = PeftModel.from_pretrained(base_model, model_path)
    model = model.merge_and_unload()  # Merge LoRA weights for faster inference
    
    tokenizer = AutoTokenizer.from_pretrained(model_path)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    
    model.eval()
    model = model.to('cpu')
    
    print("✅ Model loaded successfully")
    return model, tokenizer

def generate_critique(model, tokenizer, question: str, answer: str, max_new_tokens=150):
    """Generate critique using fine-tuned model"""
    prompt = f"""Analyze this legal answer for errors in 8 categories:

1. Factual accuracy errors
2. Logical and reasoning errors  
3. Legal terminology errors
4. Completeness gaps
5. Compliance issues
6. Structural problems
7. Contextual relevance
8. Practical applicability

Question: {question[:200]}

Answer: {answer[:1000]}

Provide critique in this format:
- Category 1: [issue or "OK"]
- Category 2: [issue or "OK"]
... (one line per category, be concise)"""
    
    inputs = tokenizer(
        prompt,
        return_tensors="pt",
        truncation=True,
        max_length=512
    )
    
    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=max_new_tokens,
            temperature=0.7,
            do_sample=True,
            pad_token_id=tokenizer.eos_token_id,
            num_beams=1,
            early_stopping=True
        )
    
    critique = tokenizer.decode(outputs[0], skip_special_tokens=True)
    
    # Remove prompt from output
    if prompt in critique:
        critique = critique.split(prompt)[-1].strip()
    
    return critique

def test_model():
    """Test the fine-tuned model with sample inputs"""
    print("=" * 60)
    print("Testing Fine-tuned Critique Model")
    print("=" * 60)
    
    try:
        model, tokenizer = load_finetuned_model()
    except FileNotFoundError as e:
        print(f"❌ Error: {e}")
        print("\nPlease train the model first using train_lora.py")
        return
    
    # Test cases
    test_cases = [
        {
            "question": "What are my rights if my employer fires me without notice?",
            "answer": "In India, employers can fire employees anytime without any notice. There are no laws protecting workers. You have no rights and should just accept it."
        },
        {
            "question": "Can I sue someone for defamation on social media?",
            "answer": "Yes, defamation is a serious crime in India. You can file a criminal case and the person will go to jail immediately. The process is very simple and takes only a few days."
        }
    ]
    
    print("\n" + "=" * 60)
    print("Running Test Cases")
    print("=" * 60)
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n📝 Test Case {i}:")
        print(f"Question: {test_case['question']}")
        print(f"\nAnswer: {test_case['answer']}")
        
        critique = generate_critique(
            model,
            tokenizer,
            test_case['question'],
            test_case['answer']
        )
        
        print(f"\n🔍 Critique:")
        print(critique)
        print("-" * 60)
    
    print("\n✅ Testing complete!")

if __name__ == "__main__":
    test_model()

