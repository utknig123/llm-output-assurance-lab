"""
Format synthetic critique data for LoRA fine-tuning
Converts question-answer-critique pairs into training format
"""
import json
import os

try:
    from datasets import Dataset
except ImportError:
    print("⚠️ datasets module not found. Installing...")
    import subprocess
    import sys
    subprocess.check_call([sys.executable, "-m", "pip", "install", "datasets>=2.14.0"])
    from datasets import Dataset

def format_critique_prompt(question: str, answer: str) -> str:
    """Format input prompt for critique generation"""
    return f"""Analyze this legal answer for errors in 8 categories:

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

def load_and_format_data(input_file="data/synthetic_critique_data.json"):
    """Load and format data for training"""
    input_path = os.path.join(os.path.dirname(__file__), input_file)
    
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Data file not found: {input_path}")
    
    with open(input_path, 'r', encoding='utf-8') as f:
        examples = json.load(f)
    
    formatted_data = []
    
    for example in examples:
        question = example.get('question', '')
        answer = example.get('answer', '')
        critique = example.get('critique', '')
        
        # Handle critique if it's a dict (convert to string)
        if isinstance(critique, dict):
            # Convert dict to formatted string
            critique_lines = []
            for key, value in critique.items():
                if isinstance(value, str):
                    critique_lines.append(f"- {key}: {value}")
                else:
                    critique_lines.append(f"- {key}: {str(value)}")
            critique = "\n".join(critique_lines)
        elif not isinstance(critique, str):
            # Convert any other type to string
            critique = str(critique)
        
        # Ensure all fields are strings and not empty
        question = str(question).strip() if question else ''
        answer = str(answer).strip() if answer else ''
        critique = str(critique).strip() if critique else ''
        
        if not all([question, answer, critique]):
            print(f"⚠️ Skipping example with missing fields: question={bool(question)}, answer={bool(answer)}, critique={bool(critique)}")
            continue
        
        # Format input prompt
        input_text = format_critique_prompt(question, answer)
        
        # Format output (critique)
        output_text = critique.strip()
        
        formatted_data.append({
            'input': input_text,
            'output': output_text,
            'question': question,
            'answer': answer
        })
    
    print(f"Formatted {len(formatted_data)} examples for training")
    return formatted_data

def create_dataset(formatted_data, train_split=0.9):
    """Create train/validation split"""
    dataset = Dataset.from_list(formatted_data)
    
    # Split into train and validation
    split_dataset = dataset.train_test_split(test_size=1-train_split, seed=42)
    
    print(f"Train examples: {len(split_dataset['train'])}")
    print(f"Validation examples: {len(split_dataset['test'])}")
    
    return split_dataset

def save_formatted_data(formatted_data, output_file="data/formatted_training_data.json"):
    """Save formatted data"""
    output_path = os.path.join(os.path.dirname(__file__), output_file)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(formatted_data, f, indent=2, ensure_ascii=False)
    
    print(f"Saved formatted data to {output_path}")

if __name__ == "__main__":
    print("Loading and formatting data...")
    formatted_data = load_and_format_data()
    
    print("\nCreating dataset splits...")
    dataset = create_dataset(formatted_data)
    
    print("\nSaving formatted data...")
    save_formatted_data(formatted_data)
    
    print("\n✅ Data formatting complete!")
    print(f"\nDataset ready for training:")
    print(f"  - Train: {len(dataset['train'])} examples")
    print(f"  - Validation: {len(dataset['test'])} examples")

