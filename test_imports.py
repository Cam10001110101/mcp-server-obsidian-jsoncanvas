import sys

def test_import(module_name):
    try:
        __import__(module_name)
        print(f"{module_name}: OK")
        return True
    except ImportError as e:
        print(f"{module_name}: ERROR - {e}")
        return False

modules = ["mcp", "jsonschema", "PIL", "svgwrite"]
all_ok = True

for module in modules:
    if not test_import(module):
        all_ok = False

if all_ok:
    print("\nAll dependencies imported successfully!")
    sys.exit(0)
else:
    print("\nSome dependencies failed to import.")
    sys.exit(1)
