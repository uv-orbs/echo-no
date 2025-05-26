#!/usr/bin/env python3
"""
Setup script for Telegram News Monitor
Helps with initial installation and configuration
"""

import os
import sys
import subprocess
from pathlib import Path


def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        print(f"   Current version: {sys.version}")
        return False
    print(f"✅ Python version: {sys.version.split()[0]}")
    return True


def install_dependencies():
    """Install required dependencies"""
    print("\n📦 Installing dependencies...")
    try:
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "-r", "requirements.txt"]
        )
        print("✅ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        return False


def setup_environment():
    """Set up environment configuration"""
    print("\n⚙️  Setting up environment...")

    env_file = Path(".env")
    template_file = Path("config_template.env")

    if env_file.exists():
        print("⚠️  .env file already exists")
        response = input("   Overwrite? (y/N): ").lower().strip()
        if response != "y":
            print("   Keeping existing .env file")
            return True

    if template_file.exists():
        try:
            # Copy template to .env
            with open(template_file, "r") as src, open(env_file, "w") as dst:
                dst.write(src.read())
            print("✅ Created .env file from template")
            print("   Please edit .env with your actual credentials")
            return True
        except Exception as e:
            print(f"❌ Failed to create .env file: {e}")
            return False
    else:
        print("❌ config_template.env not found")
        return False


def run_tests():
    """Run basic tests to verify setup"""
    print("\n🧪 Running basic tests...")
    try:
        subprocess.check_call([sys.executable, "test_monitor.py"])
        print("✅ Basic tests passed")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Tests failed: {e}")
        return False


def print_next_steps():
    """Print next steps for the user"""
    print("\n" + "=" * 60)
    print("🎉 Setup completed!")
    print("=" * 60)
    print("\nNext steps:")
    print("1. 📝 Edit .env file with your credentials:")
    print("   - Get Telegram API credentials from https://my.telegram.org/apps")
    print("   - Get LLM API key (Groq: https://console.groq.com/)")
    print()
    print("2. 📺 Configure channels in telegram_news_monitor.py:")
    print("   - Edit the load_config() function")
    print("   - Add real Telegram channel usernames")
    print("   - Balance right-wing and left-wing channels")
    print()
    print("3. 🚀 Run the monitor:")
    print("   python telegram_news_monitor.py")
    print()
    print("4. 🧪 Test first (optional):")
    print("   python test_monitor.py")
    print()
    print("📚 See README.md for detailed instructions")


def main():
    """Main setup function"""
    print("🚀 Telegram News Monitor Setup")
    print("=" * 40)

    success = True

    # Check Python version
    if not check_python_version():
        success = False

    # Install dependencies
    if success and not install_dependencies():
        success = False

    # Setup environment
    if success and not setup_environment():
        success = False

    # Run tests
    if success:
        run_tests()  # Non-critical, don't fail setup if tests fail

    if success:
        print_next_steps()
    else:
        print("\n❌ Setup failed. Please check the errors above.")
        sys.exit(1)


if __name__ == "__main__":
    main()
