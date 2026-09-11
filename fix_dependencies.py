"""
Fix all dependencies to conflict-free versions
Run this before training: python fix_dependencies.py
"""
import subprocess
import sys
import os

def run_command(cmd):
    """Run a command and show output"""
    print(f"Running: {cmd}")
    result = subprocess.run(cmd, shell=True)
    if result.returncode != 0:
        print(f"⚠️ Command failed: {cmd}")
    return result.returncode == 0

print("="*60)
print("Fixing All Dependencies - Conflict-Free Versions")
print("="*60)

# Step 1: Fix NumPy FIRST (critical for torch)
print("\n1. Fixing NumPy (must be <2.0 for torch 2.2.0)...")
run_command(f"{sys.executable} -m pip install numpy==1.24.3 --force-reinstall")

# Step 2: Fix transformers to exact version
print("\n2. Fixing transformers to 4.45.0...")
run_command(f"{sys.executable} -m pip uninstall transformers -y")
run_command(f"{sys.executable} -m pip install transformers==4.45.0 tokenizers==0.15.0")

# Step 3: Fix peft
print("\n3. Fixing peft to 0.10.0...")
run_command(f"{sys.executable} -m pip install peft==0.10.0 --force-reinstall")

# Step 4: Fix accelerate
print("\n4. Fixing accelerate to 0.29.0...")
run_command(f"{sys.executable} -m pip install accelerate==0.29.0 --force-reinstall")

# Step 5: Fix datasets
print("\n5. Fixing datasets to 2.14.0...")
run_command(f"{sys.executable} -m pip install datasets==2.14.0 --force-reinstall")

# Step 6: Fix fsspec and httpx (for backend compatibility)
print("\n6. Fixing fsspec and httpx for backend compatibility...")
run_command(f"{sys.executable} -m pip install fsspec==2024.6.1 httpx==0.23.3 --force-reinstall")

print("\n" + "="*60)
print("✅ Dependency fixing complete!")
print("="*60)
print("\nNow run: python run_pipeline.py")

