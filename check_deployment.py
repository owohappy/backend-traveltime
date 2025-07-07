import sys
import importlib
import traceback

def check_import(module_name):
    """Check if a module can be imported successfully"""
    try:
        importlib.import_module(module_name)
        print(f"{module_name} - OK")
        return True
    except Exception as e:
        print(f"{module_name} - ERROR: {str(e)}")
        return False

def main():
    print("tt API v0.0.3 ")
    print("=" * 50)
    
    # Check core dependencies
    modules_to_check = [
        "fastapi",
        "uvicorn",
        "sqlmodel", 
        "passlib",
        "jose",
        "pyotp",
        "shapely",
        "pydantic",
        "misc.config",
        "misc.models",
        "misc.db",
        "misc.schemas",
        "routes.auth",
        "routes.account", 
        "routes.travel",
        "routes.misc",
        "routes.gamling",
        "routes.levels",
        "routes.admin"
    ]
    
    failed = 0
    for module in modules_to_check:
        if not check_import(module):
            failed += 1
    
    print("\n" + "=" * 50)
    if failed == 0:
        print("All checks passed! API is ready for deployment.")
        return 0
    else:
        print(f"{failed} issues found. Please resolve before deployment.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
