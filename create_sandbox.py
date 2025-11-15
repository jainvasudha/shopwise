#!/usr/bin/env python3
"""
Script to create a Daytona sandbox for the shopwise project
"""

from daytona import Daytona, DaytonaConfig
import os

# Define the configuration
config = DaytonaConfig(api_key="dtn_480398564e757796382485b3b86e87ea61ca863b7ddc5dc7985d2d0051830dc8")

# Initialize the Daytona client
daytona = Daytona(config)

# Create the Sandbox instance
print("🚀 Creating sandbox...")
sandbox = daytona.create()
print(f"✅ Sandbox created! ID: {sandbox.id}")

# Set up the environment
print("\n📦 Installing dependencies...")
install_cmd = "pip install -r requirements.txt"
response = sandbox.process.code_run(install_cmd)

if response.exit_code != 0:
    print(f"⚠️  Warning: {response.exit_code} {response.result}")
else:
    print("✅ Dependencies installed")

# Check for API keys
print("\n🔑 Checking for API keys...")
anthropic_key = os.getenv("ANTHROPIC_API_KEY")
if anthropic_key:
    print("✅ ANTHROPIC_API_KEY found")
    # Set environment variable in sandbox
    sandbox.process.code_run(f'export ANTHROPIC_API_KEY="{anthropic_key}"')
else:
    print("⚠️  ANTHROPIC_API_KEY not found. Set it before running the app.")

galileo_key = os.getenv("GALILEO_API_KEY")
if galileo_key:
    print("✅ GALILEO_API_KEY found")
    sandbox.process.code_run(f'export GALILEO_API_KEY="{galileo_key}"')
else:
    print("ℹ️  GALILEO_API_KEY not set (optional)")

# Instructions for running the app
print("\n🚀 To run ShopWise in your Daytona workspace:")
print("   1. Connect to your workspace via SSH or web terminal")
print("   2. Set your API keys (if not already set):")
print("      export ANTHROPIC_API_KEY='your-key-here'")
print("   3. Run the Streamlit app:")
print("      streamlit run streamlit_app.py")
print("   4. Access the app via Daytona's port forwarding (usually port 8501)")
print("\n✅ Sandbox is ready!")
print(f"📊 View it in the dashboard: https://app.daytona.io")

