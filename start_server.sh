#!/bin/bash
# Quick start script for ShopWise API server

# Set API key
export ANTHROPIC_API_KEY="bb91df24-662e-4638-af75-e9e637f2e034"

# Optional: Set Galileo key if you have it
# export GALILEO_API_KEY="your-galileo-key"

# Start the server
echo "🚀 Starting ShopWise API server..."
echo "📍 Server will be available at:"
echo "   - Local: http://localhost:8000"
echo "   - API Docs: http://localhost:8000/docs"
echo ""
echo "Press CTRL+C to stop the server"
echo ""

uvicorn api_server:app --reload --host 0.0.0.0 --port 8000

