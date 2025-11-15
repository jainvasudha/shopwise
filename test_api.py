#!/usr/bin/env python3
"""Simple script to test the ShopWise API endpoints."""

import requests
import json
import sys

def test_health(base_url: str):
    """Test the health check endpoint."""
    print(f"Testing health endpoint: {base_url}/api/health")
    try:
        response = requests.get(f"{base_url}/api/health", timeout=5)
        response.raise_for_status()
        print(f"✅ Health check passed: {response.json()}")
        return True
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False

def test_search(base_url: str, query: str = "wireless headphones", limit: int = 2):
    """Test the search endpoint."""
    print(f"\nTesting search endpoint: {base_url}/api/search")
    print(f"Query: '{query}', Limit: {limit}")
    
    payload = {
        "query": query,
        "limit": limit
    }
    
    try:
        response = requests.post(
            f"{base_url}/api/search",
            json=payload,
            timeout=30  # Search can take a while
        )
        response.raise_for_status()
        data = response.json()
        
        print(f"✅ Search successful!")
        print(f"   Found {len(data.get('results', []))} results")
        print(f"   Summary preview: {data.get('summary', '')[:100]}...")
        
        if data.get('results'):
            print(f"\n   First result:")
            first = data['results'][0]
            print(f"   - {first['name']}")
            print(f"   - Store: {first['store']}")
            print(f"   - Price: ${first['price']:.2f}")
            print(f"   - Carbon: {first['carbon']['label']} ({first['carbon']['kg_co2e']} kg CO₂e)")
        
        return True
    except Exception as e:
        print(f"❌ Search failed: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"   Response: {e.response.text}")
        return False

def main():
    # Determine base URL
    if len(sys.argv) > 1:
        base_url = sys.argv[1].rstrip('/')
    else:
        # Default to localhost, but check for Daytona environment
        import os
        daytona_ws_id = os.getenv('DAYTONA_WS_ID')
        if daytona_ws_id:
            base_url = f"https://{daytona_ws_id}-8000.app.daytona.io"
            print(f"🌐 Detected Daytona workspace: {daytona_ws_id}")
        else:
            base_url = "http://localhost:8000"
            print("🏠 Using localhost (not in Daytona)")
    
    print(f"\n🔍 Testing API at: {base_url}\n")
    
    # Test health endpoint
    health_ok = test_health(base_url)
    
    if not health_ok:
        print("\n❌ Server is not responding. Make sure the API server is running:")
        print("   uvicorn api_server:app --reload --host 0.0.0.0 --port 8000")
        sys.exit(1)
    
    # Test search endpoint (only if ANTHROPIC_API_KEY is set)
    import os
    if os.getenv('ANTHROPIC_API_KEY'):
        test_search(base_url)
    else:
        print("\n⚠️  Skipping search test (ANTHROPIC_API_KEY not set)")
        print("   Set it with: export ANTHROPIC_API_KEY='your-key'")
    
    print("\n✅ API testing complete!")

if __name__ == "__main__":
    main()


