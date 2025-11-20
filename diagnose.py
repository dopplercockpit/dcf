#!/usr/bin/env python3
"""
Diagnostic script to verify all DCF Model connections
"""

import os
import sys

def diagnose():
    print("=" * 60)
    print("DCF Model Connection Diagnostics")
    print("=" * 60)
    print()

    errors = []
    warnings = []

    # Check 1: Files exist
    print("1. Checking file structure...")
    required_files = {
        'dcf_model.py': 'Main Flask application',
        'templates/index_input.html': 'Web interface',
        'requirements.txt': 'Dependencies list',
    }

    for filepath, description in required_files.items():
        full_path = os.path.join(os.getcwd(), filepath)
        if os.path.exists(full_path):
            print(f"   [OK] {filepath} - {description}")
        else:
            print(f"   [ERROR] {filepath} missing - {description}")
            errors.append(f"Missing file: {filepath}")
    print()

    # Check 2: No old index.html in root
    print("2. Checking for conflicting files...")
    old_index = os.path.join(os.getcwd(), 'index.html')
    if os.path.exists(old_index):
        print("   [WARNING] Old index.html found in root directory")
        print("   This may cause conflicts. Delete it or rename it.")
        warnings.append("Old index.html exists in root")
    else:
        print("   [OK] No conflicting index.html in root")
    print()

    # Check 3: Import dcf_model
    print("3. Checking Python imports...")
    try:
        import dcf_model
        print("   [OK] dcf_model.py imports successfully")
    except Exception as e:
        print(f"   [ERROR] Failed to import dcf_model: {e}")
        errors.append(f"Import error: {e}")
        return False
    print()

    # Check 4: Flask routes
    print("4. Checking Flask routes...")
    app = dcf_model.app
    routes = {r.rule: [m for m in r.methods if m not in ['HEAD', 'OPTIONS']]
              for r in app.url_map.iter_rules() if not r.rule.startswith('/static')}

    expected_routes = {
        '/': ['GET'],
        '/api/calculate': ['POST'],
        '/api/analyze': ['POST'],
        '/api/alpha_vantage': ['GET'],
        '/api/defaults': ['GET'],
    }

    for route, methods in expected_routes.items():
        if route in routes:
            if set(methods) == set(routes[route]):
                print(f"   [OK] {route} {methods}")
            else:
                print(f"   [WARNING] {route} has methods {routes[route]}, expected {methods}")
                warnings.append(f"Route {route} method mismatch")
        else:
            print(f"   [ERROR] {route} not registered")
            errors.append(f"Missing route: {route}")
    print()

    # Check 5: API Key
    print("5. Checking Alpha Vantage API key...")
    api_key = os.environ.get('ALPHAVANTAGE_API_KEY')
    if api_key:
        print(f"   [OK] API key is set: {api_key[:10]}...")
    else:
        print("   [ERROR] ALPHAVANTAGE_API_KEY not set")
        errors.append("API key not configured")
    print()

    # Check 6: Template file content
    print("6. Checking template file...")
    template_path = os.path.join(os.getcwd(), 'templates', 'index_input.html')
    try:
        with open(template_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Check for key functions
        required_functions = ['analyzeStock', 'resetAnalysis', 'displayResults']
        for func in required_functions:
            if f'function {func}' in content:
                print(f"   [OK] Function {func}() found")
            else:
                print(f"   [ERROR] Function {func}() missing")
                errors.append(f"Missing function: {func}()")

        # Check for correct endpoint
        if '/api/analyze' in content:
            print("   [OK] Uses /api/analyze endpoint")
        else:
            print("   [ERROR] /api/analyze endpoint not referenced")
            errors.append("Template doesn't use /api/analyze")

    except Exception as e:
        print(f"   [ERROR] Failed to read template: {e}")
        errors.append(f"Template read error: {e}")
    print()

    # Summary
    print("=" * 60)
    print("DIAGNOSTIC SUMMARY")
    print("=" * 60)

    if warnings:
        print(f"\n[WARNINGS] ({len(warnings)} issues):")
        for w in warnings:
            print(f"  - {w}")

    if errors:
        print(f"\n[ERRORS] ({len(errors)} issues):")
        for e in errors:
            print(f"  - {e}")
        print("\n[RESULT] Diagnostics FAILED. Please fix the errors above.")
        print()
        print("Common fixes:")
        print("1. Set API key: $env:ALPHAVANTAGE_API_KEY=\"your_key\"")
        print("2. Install dependencies: pip install -r requirements.txt")
        print("3. Make sure you're running Flask: python dcf_model.py")
        print("4. Access via http://localhost:5000 (NOT by opening HTML directly)")
        return False
    else:
        print("\n[RESULT] All diagnostics PASSED!")
        print()
        print("To start the application:")
        print("1. Run: python dcf_model.py")
        print("2. Open browser to: http://localhost:5000")
        print("3. Enter a ticker symbol and click 'Analyze Stock'")
        print()
        print("IMPORTANT: Do NOT open the HTML file directly!")
        print("You must access it through the Flask server at localhost:5000")
        return True

if __name__ == '__main__':
    success = diagnose()
    sys.exit(0 if success else 1)
