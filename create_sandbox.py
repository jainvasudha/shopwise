#!/usr/bin/env python3
"""
Script to create a Daytona sandbox for the ShopWise project.
This sets up both the Python API backend and React frontend.
"""

from daytona import Daytona, DaytonaConfig
import os

# Define the configuration
# You can get your API key from: https://app.daytona.io/settings/api-keys
config = DaytonaConfig(api_key="dtn_480398564e757796382485b3b86e87ea61ca863b7ddc5dc7985d2d0051830dc8")

# Initialize the Daytona client
daytona = Daytona(config)

# Create the Sandbox instance
print("🚀 Creating Daytona sandbox...")
sandbox = daytona.create()
print(f"✅ Sandbox created! ID: {sandbox.id}")

# Set up Python environment
print("\n📦 Installing Python dependencies...")
install_cmd = "pip install -r requirements.txt"
response = sandbox.process.code_run(install_cmd)

if response.exit_code != 0:
    print(f"⚠️  Warning: {response.exit_code} {response.result}")
else:
    print("✅ Python dependencies installed")

# Set up Node.js and React frontend
print("\n📦 Setting up Node.js frontend...")
node_commands = [
    "cd frontend",
    "npm install"
]
for cmd in node_commands:
    response = sandbox.process.code_run(cmd)
    if response.exit_code != 0:
        print(f"⚠️  Warning running '{cmd}': {response.exit_code} {response.result}")
    else:
        print(f"✅ Completed: {cmd}")

# Check for API keys
print("\n🔑 Checking for API keys...")
anthropic_key = os.getenv("ANTHROPIC_API_KEY")
if anthropic_key:
    print("✅ ANTHROPIC_API_KEY found")
    # Set environment variable in sandbox
    sandbox.process.code_run(f'export ANTHROPIC_API_KEY="{anthropic_key}"')
    # Also add to shell profile for persistence
    sandbox.process.code_run(f'echo \'export ANTHROPIC_API_KEY="{anthropic_key}"\' >> ~/.bashrc')
else:
    print("⚠️  ANTHROPIC_API_KEY not found. Set it before running the app:")
    print("   export ANTHROPIC_API_KEY='your-key-here'")

galileo_key = os.getenv("GALILEO_API_KEY")
if galileo_key:
    print("✅ GALILEO_API_KEY found")
    sandbox.process.code_run(f'export GALILEO_API_KEY="{galileo_key}"')
    sandbox.process.code_run(f'echo \'export GALILEO_API_KEY="{galileo_key}"\' >> ~/.bashrc')
else:
    print("ℹ️  GALILEO_API_KEY not set (optional)")

# Instructions for running the app
print("\n" + "="*60)
print("🚀 To run ShopWise in your Daytona workspace:")
print("="*60)
print("\n1. Connect to your workspace:")
print(f"   - Web terminal: https://app.daytona.io")
print(f"   - Or SSH if configured")
print("\n2. Set your API key (if not already set):")
print("   export ANTHROPIC_API_KEY='your-key-here'")
print("\n3. Start the Python API server (Terminal 1):")
print("   uvicorn api_server:app --reload --host 0.0.0.0 --port 8000")
print("   → Daytona will forward to: https://<workspace-id>-8000.app.daytona.io")
print("\n4. Start the React frontend (Terminal 2):")
print("   cd frontend")
print("   npm run dev")
print("   → Daytona will forward to: https://<workspace-id>-3000.app.daytona.io")
print("\n5. Access the app:")
print("   Open the React frontend URL in your browser")
print("   The frontend will automatically connect to the API on port 8000")
print("\n" + "="*60)
print("✅ Sandbox is ready!")
print(f"📊 View it in the dashboard: https://app.daytona.io")
print(f"🔗 Sandbox ID: {sandbox.id}")

