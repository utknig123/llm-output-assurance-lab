"""
Install all required dependencies for Model B fine-tuning
"""
import subprocess
import sys

def install_package(package):
    """Install a package using pip"""
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        print(f"✅ {package} installed successfully")
        return True
    except subprocess.CalledProcessError:
        print(f"❌ Failed to install {package}")
        return False

def main():
    print("="*60)
    print("Installing Model B Fine-tuning Dependencies")
    print("="*60)
    
    # Read requirements
    requirements_file = "requirements.txt"
    try:
        with open(requirements_file, 'r') as f:
            packages = []
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    packages.append(line)
    except FileNotFoundError:
        print(f"❌ {requirements_file} not found")
        return
    
    print(f"\nInstalling {len(packages)} packages...\n")
    
    failed = []
    for package in packages:
        print(f"Installing {package}...")
        if not install_package(package):
            failed.append(package)
    
    print("\n" + "="*60)
    if failed:
        print(f"⚠️ Failed to install {len(failed)} packages:")
        for pkg in failed:
            print(f"  - {pkg}")
    else:
        print("✅ All dependencies installed successfully!")
    print("="*60)

if __name__ == "__main__":
    main()

