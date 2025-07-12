#!/usr/bin/env python3
"""
Lightweight validation script to check if all imports are correctly structured.
This helps identify blueprint synchronization issues before deployment.
"""

import sys
import os
from pathlib import Path

def validate_imports():
    """Validate that all imports are correctly structured."""
    try:
        print("🔍 Validating import structure...")
        
        # Check main files exist
        main_files = [
            "src/api/v1/main.py",
            "src/api/v1/endpoints/courses.py",
            "src/api/v1/endpoints/recommendations.py",
            "src/api/v1/endpoints/users.py",
            "src/api/v1/schemas.py",
            "src/api/v1/crud.py",
            "src/core/config.py",
            "src/data_engineering/db_utils.py",
        ]
        
        for file_path in main_files:
            if not Path(file_path).exists():
                print(f"❌ Missing file: {file_path}")
                return False
            else:
                print(f"✅ Found: {file_path}")
        
        # Check for circular imports by examining import statements
        print("\n🔍 Checking for potential circular imports...")
        
        # Read main.py and check it imports the routers
        with open("src/api/v1/main.py", "r") as f:
            main_content = f.read()
            
        # Check for the actual import pattern used
        import_line = "from src.api.v1.endpoints import courses, recommendations, users"
        if import_line in main_content:
            print(f"✅ Found router imports: {import_line}")
        else:
            # Check for individual imports as fallback
            expected_imports = [
                "courses",
                "recommendations", 
                "users"
            ]
            
            import_section = [line for line in main_content.split('\n') if 'from src.api.v1.endpoints import' in line]
            if import_section:
                import_text = ' '.join(import_section)
                missing_imports = []
                for imp in expected_imports:
                    if imp not in import_text:
                        missing_imports.append(imp)
                
                if missing_imports:
                    print(f"❌ Missing router imports: {missing_imports}")
                    return False
                else:
                    print(f"✅ Found all router imports: {expected_imports}")
            else:
                print(f"❌ No router imports found")
                return False
        
        # Check router includes (handle multiline includes)
        expected_routers = ["courses.router", "recommendations.router", "users.router"]
        
        for router in expected_routers:
            if router in main_content:
                print(f"✅ Found router include: {router}")
            else:
                print(f"❌ Missing router include: {router}")
                return False
        
        print("\n✅ All import structure checks passed!")
        return True
        
    except Exception as e:
        print(f"❌ Validation failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main function to run validation."""
    print("=" * 60)
    print("  Umbra Educational Data Platform - Import Validation")
    print("=" * 60)
    
    if validate_imports():
        print("\n🎉 SUCCESS: Import structure validation completed successfully!")
        sys.exit(0)
    else:
        print("\n💥 FAILURE: Import structure validation failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()
