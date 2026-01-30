"""
Package validation script for TCBS SDK
Run this before publishing to PyPI
"""

import os
import sys


def check_file_exists(filepath, required=True):
    """Check if a file exists"""
    exists = os.path.exists(filepath)
    status = "✓" if exists else ("✗" if required else "○")
    req_text = "(required)" if required else "(optional)"
    print(f"{status} {filepath} {req_text}")
    return exists


def check_no_sensitive_data():
    """Check for potential sensitive data"""
    print("\n🔍 Checking for sensitive data...")
    
    sensitive_patterns = [".key", "test_api_key.py", ".tcbs_token.json"]
    issues = []
    
    for pattern in sensitive_patterns:
        if os.path.exists(pattern):
            issues.append(pattern)
    
    if issues:
        print("✗ Found sensitive files that should be in .gitignore:")
        for issue in issues:
            print(f"  - {issue}")
        return False
    else:
        print("✓ No sensitive files found")
        return True


def main():
    print("=" * 60)
    print("TCBS Package Validation")
    print("=" * 60)
    
    print("\n📦 Checking required files...")
    required_files = [
        "setup.py",
        "pyproject.toml",
        "README.md",
        "LICENSE",
        "MANIFEST.in",
        "requirements.txt",
        "tcbs/__init__.py",
        "tcbs/client.py",
        "tcbs/auth.py",
        "tcbs/exceptions.py",
    ]
    
    all_required_exist = all(check_file_exists(f, True) for f in required_files)
    
    print("\n📄 Checking optional files...")
    optional_files = [
        "CHANGELOG.md",
        "CONTRIBUTING.md",
        "PUBLISHING.md",
        ".gitignore",
    ]
    
    for f in optional_files:
        check_file_exists(f, False)
    
    # Check for sensitive data
    no_sensitive = check_no_sensitive_data()
    
    # Check version consistency
    print("\n🔢 Checking version...")
    try:
        import tcbs
        print(f"✓ Package version: {tcbs.__version__}")
    except Exception as e:
        print(f"✗ Could not import package: {e}")
        all_required_exist = False
    
    # Final verdict
    print("\n" + "=" * 60)
    if all_required_exist and no_sensitive:
        print("✅ Package is ready for publishing!")
        print("\nNext steps:")
        print("1. python -m build")
        print("2. python -m twine upload --repository testpypi dist/*")
        print("3. Test installation from Test PyPI")
        print("4. python -m twine upload dist/*")
        return 0
    else:
        print("❌ Package has issues that need to be fixed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
