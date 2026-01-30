#!/usr/bin/env python3
"""
Validate Cite-Finance API code structure
Checks that all required files exist and have correct structure
"""

import os
import ast
import sys


def check_file_exists(path, description):
    """Check if file exists"""
    if os.path.exists(path):
        print(f"  ✅ {description}: {path}")
        return True
    else:
        print(f"  ❌ {description} MISSING: {path}")
        return False


def check_python_syntax(path):
    """Check if Python file has valid syntax"""
    try:
        with open(path, 'r') as f:
            ast.parse(f.read())
        return True
    except SyntaxError as e:
        print(f"    ⚠️  Syntax error in {path}: {e}")
        return False


def count_functions_in_file(path):
    """Count functions/classes in Python file"""
    try:
        with open(path, 'r') as f:
            tree = ast.parse(f.read())

        functions = [node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]
        classes = [node for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]

        return len(functions), len(classes)
    except:
        return 0, 0


print("🔍 Validating Cite-Finance API Structure...")
print()

all_passed = True

# Core infrastructure files
print("✓ Core Infrastructure:")
files = [
    ("src/main.py", "FastAPI main application"),
    ("src/__init__.py", "Source package init"),
    ("config/database_schema.sql", "Database schema"),
    ("Dockerfile", "Docker image config"),
    ("docker-compose.yml", "Docker Compose config"),
    ("requirements.txt", "Python dependencies"),
    (".env.example", "Environment variables example"),
]

for path, desc in files:
    if not check_file_exists(path, desc):
        all_passed = False

# Models
print()
print("✓ Data Models:")
model_files = [
    "src/models/__init__.py",
    "src/models/user.py",
]
for path in model_files:
    if check_file_exists(path, os.path.basename(path)):
        if check_python_syntax(path):
            funcs, classes = count_functions_in_file(path)
            print(f"    📊 {classes} classes, {funcs} functions")
    else:
        all_passed = False

# Auth & Billing
print()
print("✓ Authentication & Billing:")
auth_files = [
    "src/auth/__init__.py",
    "src/auth/api_keys.py",
    "src/billing/__init__.py",
    "src/billing/stripe_integration.py",
]
for path in auth_files:
    if check_file_exists(path, os.path.basename(path)):
        if check_python_syntax(path):
            funcs, classes = count_functions_in_file(path)
            print(f"    📊 {classes} classes, {funcs} functions")
    else:
        all_passed = False

# Data Sources
print()
print("✓ Data Sources:")
ds_files = [
    "src/data_sources/__init__.py",
    "src/data_sources/base.py",
    "src/data_sources/sec_edgar.py",
]
for path in ds_files:
    if check_file_exists(path, os.path.basename(path)):
        if check_python_syntax(path):
            funcs, classes = count_functions_in_file(path)
            print(f"    📊 {classes} classes, {funcs} functions")
    else:
        all_passed = False

# Middleware
print()
print("✓ Middleware:")
mw_files = [
    "src/middleware/__init__.py",
    "src/middleware/auth.py",
    "src/middleware/rate_limiter.py",
]
for path in mw_files:
    if check_file_exists(path, os.path.basename(path)):
        if check_python_syntax(path):
            funcs, classes = count_functions_in_file(path)
            print(f"    📊 {classes} classes, {funcs} functions")
    else:
        all_passed = False

# API Routes
print()
print("✓ API Routes:")
api_files = [
    "src/api/__init__.py",
    "src/api/auth.py",
    "src/api/metrics.py",
    "src/api/companies.py",
    "src/api/subscriptions.py",
]
for path in api_files:
    if check_file_exists(path, os.path.basename(path)):
        if check_python_syntax(path):
            funcs, classes = count_functions_in_file(path)
            print(f"    📊 {classes} classes, {funcs} functions")
    else:
        all_passed = False

# Tests
print()
print("✓ Tests:")
test_files = [
    "tests/__init__.py",
    "tests/conftest.py",
    "tests/test_api.py",
]
for path in test_files:
    if check_file_exists(path, os.path.basename(path)):
        if check_python_syntax(path):
            funcs, classes = count_functions_in_file(path)
            print(f"    📊 {classes} classes, {funcs} test functions")
    else:
        all_passed = False

# Documentation
print()
print("✓ Documentation:")
doc_files = [
    ("README.md", "Main README"),
    ("QUICKSTART.md", "Quick start guide"),
    ("DEPLOYMENT.md", "Deployment guide"),
    ("STATUS.md", "Project status"),
]
for path, desc in doc_files:
    if not check_file_exists(path, desc):
        all_passed = False

# Check main.py has routers wired
print()
print("✓ Validating main.py configuration...")
try:
    with open("src/main.py", "r") as f:
        main_content = f.read()

    checks = [
        ("app.include_router(auth.router", "Auth routes registered"),
        ("app.include_router(metrics.router", "Metrics routes registered"),
        ("app.include_router(companies.router", "Companies routes registered"),
        ("app.include_router(subscriptions.router", "Subscriptions routes registered"),
        ("AuthMiddleware", "Auth middleware imported"),
        ("RateLimitMiddleware", "Rate limit middleware imported"),
    ]

    for check_str, desc in checks:
        if check_str in main_content:
            print(f"  ✅ {desc}")
        else:
            print(f"  ❌ {desc} NOT FOUND")
            all_passed = False

except Exception as e:
    print(f"  ❌ Failed to validate main.py: {e}")
    all_passed = False

print()
print("=" * 60)
if all_passed:
    print("🎉 All structure validations passed!")
    print("=" * 60)
    print()
    print("Project structure is complete. Ready for:")
    print("  • pip install -r requirements.txt")
    print("  • docker-compose up -d")
    print("  • pytest tests/")
    sys.exit(0)
else:
    print("❌ Some validations failed!")
    print("=" * 60)
    sys.exit(1)
