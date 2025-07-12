#!/usr/bin/env python3
"""
Simple validation script to check if the FastAPI application can start without errors.
This helps identify blueprint synchronization issues before deployment.
"""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

def validate_app():
    """Validate that the FastAPI application can be imported and created."""
    try:
        print("🔍 Validating FastAPI application...")
        
        # Test importing the main application
        from src.api.v1.main import app
        
        print("✅ FastAPI application imported successfully")
        
        # Test that the app has the expected attributes
        assert hasattr(app, 'routes'), "App should have routes attribute"
        assert hasattr(app, 'router'), "App should have router attribute"
        
        print(f"✅ Application has {len(app.routes)} routes configured")
        
        # List all routes
        print("\n📍 Configured routes:")
        for route in app.routes:
            if hasattr(route, 'path') and hasattr(route, 'methods'):
                methods = getattr(route, 'methods', ['GET'])
                print(f"  - {route.path} [{', '.join(methods)}]")
        
        # Test that routers are properly included
        expected_paths = ['/health', '/courses', '/recommendations']
        actual_paths = [route.path for route in app.routes if hasattr(route, 'path')]
        
        for expected_path in expected_paths:
            found = any(expected_path in path for path in actual_paths)
            if found:
                print(f"✅ {expected_path} endpoints found")
            else:
                print(f"❌ {expected_path} endpoints NOT found")
                return False
        
        print("\n✅ All validation checks passed!")
        print("🚀 Application is ready for deployment")
        return True
        
    except Exception as e:
        print(f"❌ Validation failed: {e}")
        print(f"Error type: {type(e).__name__}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main function to run validation."""
    print("=" * 60)
    print("  Umbra Educational Data Platform - App Validation")
    print("=" * 60)
    
    if validate_app():
        print("\n🎉 SUCCESS: Application validation completed successfully!")
        sys.exit(0)
    else:
        print("\n💥 FAILURE: Application validation failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()
