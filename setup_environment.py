"""
Setup environment with all correct dependencies - FIXES ALL CONFLICTS
Run this ONCE before training: python setup_environment.py
"""
import subprocess
import sys
import os

def run_cmd(cmd_list, description=""):
    """Run a command (as list) and return success"""
    if description:
        print(f"{description}...")
    try:
        result = subprocess.run(cmd_list, check=False, capture_output=True, text=True)
        if result.returncode != 0 and result.stderr:
            # Only print errors if they're meaningful
            if "WARNING" not in result.stderr and "already satisfied" not in result.stdout:
                print(f"   ⚠️ {result.stderr[:100]}")
        return result.returncode == 0
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

print("="*60)
print("FIXING ALL DEPENDENCY CONFLICTS")
print("="*60)

# Step 1: Uninstall ALL conflicting packages first
print("\n1. Uninstalling ALL conflicting packages...")
packages_to_remove = [
    "torch", "torchvision", "transformers", "peft", "accelerate", 
    "datasets", "numpy", "httpx", "fsspec", "tokenizers", "pyarrow"
]
for pkg in packages_to_remove:
    run_cmd([sys.executable, "-m", "pip", "uninstall", pkg, "-y"], f"  Removing {pkg}")

# Step 2: Install NumPy FIRST (critical - must be <2.0)
print("\n2. Installing NumPy 1.24.3 (MUST be <2.0 for torch 2.2.0)...")
run_cmd([sys.executable, "-m", "pip", "install", "numpy==1.24.3", "--no-deps"])
run_cmd([sys.executable, "-m", "pip", "install", "numpy==1.24.3"])

# Step 3: Install torch and torchvision together (must match)
print("\n3. Installing torch 2.2.0 and torchvision 0.17.0...")
run_cmd([sys.executable, "-m", "pip", "install", "torch==2.2.0", "torchvision==0.17.0", "--no-deps"])
run_cmd([sys.executable, "-m", "pip", "install", "torch==2.2.0", "torchvision==0.17.0"])

# Step 4: Install tokenizers first (required by transformers)
print("\n4. Installing tokenizers 0.20.3...")
run_cmd([sys.executable, "-m", "pip", "install", "tokenizers==0.20.3"])

# Step 5: Install transformers
print("\n5. Installing transformers 4.45.0...")
run_cmd([sys.executable, "-m", "pip", "install", "transformers==4.45.0", "--no-deps"])
run_cmd([sys.executable, "-m", "pip", "install", "transformers==4.45.0"])

# Step 6: Install accelerate
print("\n6. Installing accelerate 0.29.0...")
run_cmd([sys.executable, "-m", "pip", "install", "accelerate==0.29.0"])

# Step 7: Install peft
print("\n7. Installing peft 0.10.0...")
run_cmd([sys.executable, "-m", "pip", "install", "peft==0.10.0"])

# Step 8: Install datasets (with compatible fsspec and pyarrow)
print("\n8. Installing pyarrow 12.0.1 (for datasets compatibility)...")
run_cmd([sys.executable, "-m", "pip", "install", "pyarrow==12.0.1"])
print("   Installing fsspec 2024.6.1 (for datasets compatibility)...")
run_cmd([sys.executable, "-m", "pip", "install", "fsspec==2024.6.1"])
print("   Installing datasets 2.14.0...")
run_cmd([sys.executable, "-m", "pip", "install", "datasets==2.14.0"])

# Step 9: Fix httpx for backend compatibility
print("\n9. Fixing httpx 0.23.3 (for backend compatibility)...")
run_cmd([sys.executable, "-m", "pip", "install", "httpx==0.23.3", "--force-reinstall"])

# Step 10: Install utilities
print("\n10. Installing utilities...")
run_cmd([sys.executable, "-m", "pip", "install", "requests==2.31.0", "python-dotenv==1.0.0", "packaging>=20.0"])

print("\n" + "="*60)
print("✅ Environment setup complete!")
print("="*60)
print("\nVerifying installations...")

# Verify critical packages
try:
    import numpy
    import torch
    import transformers
    import peft
    import accelerate
    import datasets
    
    print(f"✅ NumPy: {numpy.__version__}")
    print(f"✅ PyTorch: {torch.__version__}")
    print(f"✅ Transformers: {transformers.__version__}")
    print(f"✅ PEFT: {peft.__version__}")
    print(f"✅ Accelerate: {accelerate.__version__}")
    print(f"✅ Datasets: {datasets.__version__}")
    
    # Check for conflicts
    issues = []
    if numpy.__version__.startswith("2."):
        issues.append("NumPy 2.x (needs 1.24.3)")
    if torch.__version__ != "2.2.0":
        issues.append(f"PyTorch {torch.__version__} (needs 2.2.0)")
    if transformers.__version__ != "4.45.0":
        issues.append(f"Transformers {transformers.__version__} (needs 4.45.0)")
    
    if issues:
        print(f"\n⚠️ WARNINGS:")
        for issue in issues:
            print(f"   - {issue}")
    else:
        print("\n✅ All packages verified successfully!")
        print("\nYou can now run: python run_pipeline.py")
        
except ImportError as e:
    print(f"\n❌ Import error: {e}")
    print("   Some packages may not be installed correctly.")
