#!/usr/bin/env python3
"""
Setup script for the Causal Memory Core
Handles installation and initial configuration
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        print(f"Current version: {sys.version}")
        return False
    print(f"✅ Python version {sys.version_info.major}.{sys.version_info.minor} is compatible")
    return True

def install_dependencies():
    """Install required Python packages"""
    print("\n📦 Installing dependencies...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Dependencies installed successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error installing dependencies: {e}")
        return False

def setup_environment():
    """Set up environment configuration"""
    print("\n🔧 Setting up environment configuration...")
    
    env_file = Path(".env")
    env_template = Path(".env.template")
    
    if env_file.exists():
        print("⚠️  .env file already exists. Skipping environment setup.")
        return True
    
    if not env_template.exists():
        print("❌ .env.template file not found")
        return False
    
    # Copy template to .env
    shutil.copy(env_template, env_file)
    print("✅ Created .env file from template")
    
    print("\n⚠️  IMPORTANT: You need to edit the .env file and add your OpenAI API key!")
    print("   1. Get an API key from: https://platform.openai.com/api-keys")
    print("   2. Edit .env file and replace 'your_openai_api_key_here' with your actual key")
    
    return True

def create_directories():
    """Create necessary directories"""
    print("\n📁 Creating directories...")
    
    directories = [
        "data",
        "logs",
        "tests/__pycache__",
        "src/__pycache__"
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
    
    print("✅ Directories created successfully!")
    return True

def run_tests():
    """Run the test suite to verify installation"""
    print("\n🧪 Running tests to verify installation...")
    
    # Check if we have an API key set up
    from dotenv import load_dotenv
    load_dotenv()
    
    if not os.getenv('OPENAI_API_KEY') or os.getenv('OPENAI_API_KEY') == 'your_openai_api_key_here':
        print("⚠️  Skipping tests - OpenAI API key not configured")
        print("   Configure your API key in .env file and run: python -m pytest tests/")
        return True
    
    try:
        subprocess.check_call([sys.executable, "-m", "pytest", "tests/test_memory_core.py", "-v"])
        print("✅ All tests passed!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Some tests failed: {e}")
        print("   This might be due to API configuration issues")
        return False

def main():
    """Main setup function"""
    print("🧠 Causal Memory Core - Setup Script")
    print("=" * 50)
    
    # Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Install dependencies
    if not install_dependencies():
        print("\n❌ Setup failed during dependency installation")
        sys.exit(1)
    
    # Set up environment
    if not setup_environment():
        print("\n❌ Setup failed during environment configuration")
        sys.exit(1)
    
    # Create directories
    if not create_directories():
        print("\n❌ Setup failed during directory creation")
        sys.exit(1)
    
    # Run tests (optional, may skip if no API key)
    run_tests()
    
    print("\n🎉 Setup completed successfully!")
    print("\nNext steps:")
    print("1. Edit .env file and add your OpenAI API key")
    print("2. Run the example: python example_usage.py")
    print("3. Or start the MCP server: python src/mcp_server.py")
    print("4. Run tests: python -m pytest tests/ -v")
    
    print("\nFor more information, see README.md")

if __name__ == "__main__":
    main()
