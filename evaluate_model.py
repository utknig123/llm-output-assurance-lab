"""
Comprehensive Evaluation Script
Compares fine-tuned vs non-fine-tuned Model B performance
"""
import os
import sys
import json
import time
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from peft import PeftModel

# Add parent directory to path for app imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

def load_base_model():
    """Load base distilgpt2 model (non-fine-tuned)"""
    print("Loading base distilgpt2 model...")
    tokenizer = AutoTokenizer.from_pretrained("distilgpt2")
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    
    model = AutoModelForCausalLM.from_pretrained(
        "distilgpt2",
        torch_dtype=torch.float32,
        low_cpu_mem_usage=True
    )
    model = model.to('cpu')
    model.eval()
    print("✅ Base model loaded")
    return model, tokenizer

def load_finetuned_model():
    """Load fine-tuned distilgpt2 model"""
    model_path = os.path.join(os.path.dirname(__file__), "models", "distilgpt2-critique-lora", "final")
    
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Fine-tuned model not found at {model_path}")
    
    print("Loading fine-tuned model...")
    base_model = AutoModelForCausalLM.from_pretrained(
        "distilgpt2",
        torch_dtype=torch.float32,
        low_cpu_mem_usage=True
    )
    
    model = PeftModel.from_pretrained(base_model, model_path)
    model = model.merge_and_unload()
    
    tokenizer = AutoTokenizer.from_pretrained(model_path)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    
    model = model.to('cpu')
    model.eval()
    print("✅ Fine-tuned model loaded")
    return model, tokenizer

def generate_critique(model, tokenizer, question: str, answer: str, max_new_tokens=150):
    """Generate critique using model - EXACT SAME PROMPT AS APP.PY"""
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
    
    start_time = time.time()
    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=max_new_tokens,
            temperature=0.7,
            do_sample=True,
            pad_token_id=tokenizer.eos_token_id,
            num_beams=1,
            early_stopping=True,
            repetition_penalty=1.2,  # Prevent repetition
            no_repeat_ngram_size=3  # Prevent 3-gram repetition
        )
    
    generation_time = time.time() - start_time
    critique = tokenizer.decode(outputs[0], skip_special_tokens=True)
    
    # Remove prompt from output
    if prompt in critique:
        critique = critique.split(prompt)[-1].strip()
    
    return critique, generation_time

def evaluate_critique_quality(critique: str) -> dict:
    """Evaluate critique quality metrics"""
    metrics = {
        "length": len(critique),
        "has_8_categories": False,
        "category_count": 0,
        "mentions_errors": False,
        "structured": False
    }
    
    # Check for 8 categories - look for category numbers or names
    category_keywords = [
        "factual", "logical", "terminology", "completeness",
        "compliance", "structural", "contextual", "practical"
    ]
    
    # Also check for category numbers (Category 1, Category 2, etc.)
    import re
    category_pattern = re.compile(r'category\s*[1-8]|category\s*[1-8]:', re.IGNORECASE)
    category_numbers = len(category_pattern.findall(critique))
    
    critique_lower = critique.lower()
    found_keywords = sum(1 for keyword in category_keywords if keyword in critique_lower)
    
    # Count categories: either by keyword or by number
    found_categories = max(found_keywords, category_numbers)
    metrics["category_count"] = found_categories
    metrics["has_8_categories"] = found_categories >= 6  # At least 6 categories
    
    # Check for error mentions - more comprehensive
    error_keywords = ["error", "issue", "problem", "incorrect", "wrong", "missing", "incomplete", 
                     "flaw", "mistake", "inaccurate", "violates", "lacks", "fails"]
    metrics["mentions_errors"] = any(keyword in critique_lower for keyword in error_keywords)
    
    # Check structure - look for proper category format
    # Must have dashes AND category references
    has_dashes = "-" in critique or "•" in critique
    has_category_ref = bool(category_pattern.search(critique)) or any(kw in critique_lower for kw in ["category 1", "category 2", "category 3"])
    metrics["structured"] = has_dashes and (has_category_ref or found_categories > 0)
    
    return metrics

def run_evaluation():
    """Run comprehensive evaluation"""
    print("=" * 80)
    print("MODEL B EVALUATION: Fine-tuned vs Non-fine-tuned")
    print("=" * 80)
    
    # Test cases with known issues
    test_cases = [
        {
            "question": "What are my rights if my employer fires me without notice?",
            "answer": "In India, employers can fire employees anytime without any notice. There are no laws protecting workers. You have no rights and should just accept it.",
            "expected_issues": ["factual", "completeness", "compliance"]
        },
        {
            "question": "Can I sue someone for defamation on social media?",
            "answer": "Yes, defamation is a serious crime in India. You can file a criminal case and the person will go to jail immediately. The process is very simple and takes only a few days.",
            "expected_issues": ["factual", "logical", "practical"]
        },
        {
            "question": "What is the difference between a contract and an agreement?",
            "answer": "A contract and an agreement are exactly the same thing. There is no difference. Both mean the same and have the same legal effect.",
            "expected_issues": ["factual", "terminology"]
        },
        {
            "question": "How do I file for divorce in India?",
            "answer": "To file for divorce, you just need to go to any court and tell them you want a divorce. They will give it to you the same day. No documents needed.",
            "expected_issues": ["factual", "completeness", "practical"]
        },
        {
            "question": "What happens if I don't pay my loan EMI?",
            "answer": "If you don't pay your EMI, the bank will immediately take your house and all your property. You will also go to jail for 10 years. There is no way to avoid this.",
            "expected_issues": ["factual", "compliance", "logical"]
        }
    ]
    
    # Load models
    print("\n" + "=" * 80)
    print("Loading Models...")
    print("=" * 80)
    
    try:
        base_model, base_tokenizer = load_base_model()
    except Exception as e:
        print(f"❌ Failed to load base model: {e}")
        return
    
    try:
        finetuned_model, finetuned_tokenizer = load_finetuned_model()
    except FileNotFoundError:
        print("⚠️ Fine-tuned model not found. Please train the model first.")
        return
    except Exception as e:
        print(f"❌ Failed to load fine-tuned model: {e}")
        return
    
    # Run evaluations
    print("\n" + "=" * 80)
    print("Running Evaluations...")
    print("=" * 80)
    
    base_results = []
    finetuned_results = []
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n📝 Test Case {i}: {test_case['question'][:50]}...")
        
        # Base model
        print("  Testing base model...")
        base_critique, base_time = generate_critique(
            base_model, base_tokenizer,
            test_case['question'], test_case['answer']
        )
        base_metrics = evaluate_critique_quality(base_critique)
        base_metrics['time'] = base_time
        base_results.append({
            'test_case': i,
            'critique': base_critique,
            'metrics': base_metrics
        })
        
        # Fine-tuned model
        print("  Testing fine-tuned model...")
        finetuned_critique, finetuned_time = generate_critique(
            finetuned_model, finetuned_tokenizer,
            test_case['question'], test_case['answer']
        )
        finetuned_metrics = evaluate_critique_quality(finetuned_critique)
        finetuned_metrics['time'] = finetuned_time
        finetuned_results.append({
            'test_case': i,
            'critique': finetuned_critique,
            'metrics': finetuned_metrics
        })
    
    # Calculate aggregate metrics
    print("\n" + "=" * 80)
    print("AGGREGATE METRICS")
    print("=" * 80)
    
    base_avg_time = sum(r['metrics']['time'] for r in base_results) / len(base_results)
    finetuned_avg_time = sum(r['metrics']['time'] for r in finetuned_results) / len(finetuned_results)
    
    base_avg_categories = sum(r['metrics']['category_count'] for r in base_results) / len(base_results)
    finetuned_avg_categories = sum(r['metrics']['category_count'] for r in finetuned_results) / len(finetuned_results)
    
    base_structured_pct = sum(1 for r in base_results if r['metrics']['structured']) / len(base_results) * 100
    finetuned_structured_pct = sum(1 for r in finetuned_results if r['metrics']['structured']) / len(finetuned_results) * 100
    
    base_error_detection = sum(1 for r in base_results if r['metrics']['mentions_errors']) / len(base_results) * 100
    finetuned_error_detection = sum(1 for r in finetuned_results if r['metrics']['mentions_errors']) / len(finetuned_results) * 100
    
    print(f"\n📊 Performance Metrics:")
    print(f"  Average Generation Time:")
    print(f"    Base Model:        {base_avg_time:.3f}s")
    print(f"    Fine-tuned Model:  {finetuned_avg_time:.3f}s")
    print(f"    Difference:        {abs(finetuned_avg_time - base_avg_time):.3f}s ({'+' if finetuned_avg_time > base_avg_time else '-'})")
    
    print(f"\n  Category Coverage:")
    print(f"    Base Model:        {base_avg_categories:.1f}/8 categories")
    print(f"    Fine-tuned Model:  {finetuned_avg_categories:.1f}/8 categories")
    print(f"    Improvement:       {finetuned_avg_categories - base_avg_categories:+.1f} categories")
    
    print(f"\n  Structure Quality:")
    print(f"    Base Model:        {base_structured_pct:.1f}% structured")
    print(f"    Fine-tuned Model:  {finetuned_structured_pct:.1f}% structured")
    print(f"    Improvement:       {finetuned_structured_pct - base_structured_pct:+.1f}%")
    
    print(f"\n  Error Detection:")
    print(f"    Base Model:        {base_error_detection:.1f}% detected errors")
    print(f"    Fine-tuned Model:  {finetuned_error_detection:.1f}% detected errors")
    print(f"    Improvement:       {finetuned_error_detection - base_error_detection:+.1f}%")
    
    # Save detailed results
    results = {
        'base_model': {
            'avg_time': base_avg_time,
            'avg_categories': base_avg_categories,
            'structured_pct': base_structured_pct,
            'error_detection_pct': base_error_detection,
            'detailed_results': base_results
        },
        'finetuned_model': {
            'avg_time': finetuned_avg_time,
            'avg_categories': finetuned_avg_categories,
            'structured_pct': finetuned_structured_pct,
            'error_detection_pct': finetuned_error_detection,
            'detailed_results': finetuned_results
        },
        'improvements': {
            'time_change': finetuned_avg_time - base_avg_time,
            'categories_improvement': finetuned_avg_categories - base_avg_categories,
            'structure_improvement': finetuned_structured_pct - base_structured_pct,
            'error_detection_improvement': finetuned_error_detection - base_error_detection
        }
    }
    
    results_path = os.path.join(os.path.dirname(__file__), "evaluation_results.json")
    with open(results_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ Detailed results saved to: {results_path}")
    print("\n" + "=" * 80)
    print("EVALUATION COMPLETE")
    print("=" * 80)

if __name__ == "__main__":
    run_evaluation()

