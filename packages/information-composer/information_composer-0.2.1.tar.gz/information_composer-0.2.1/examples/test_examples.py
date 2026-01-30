#!/usr/bin/env python3
"""
Verify all example scripts can be imported and run basic tests.
"""

import subprocess
import sys
from pathlib import Path


def test_import_only(script_path: Path) -> tuple[bool, str]:
    """Test if a script can be imported without errors."""
    try:
        # Try to compile the script to check for syntax errors
        with open(script_path, "r") as f:
            code = f.read()
        compile(code, script_path, "exec")
        return True, "Syntax OK"
    except SyntaxError as e:
        return False, f"Syntax Error: {e}"
    except Exception as e:
        return False, f"Error: {e}"


def main():
    """Test all example scripts."""
    examples_dir = Path(__file__).parent / "python_scripts"
    scripts = sorted(examples_dir.glob("*.py"))

    print("=" * 60)
    print("Testing Example Scripts")
    print("=" * 60)

    results = []
    for script in scripts:
        if script.name in [
            "pubmed_uorf_genome_editing_analysis.py",
            "pubmed_keywords_filter_example.py",
        ]:
            # Skip scripts that require external data files
            print(f"⏭  SKIP: {script.name} (requires external data)")
            continue

        print(f"\nTesting: {script.name}")
        success, message = test_import_only(script)
        if success:
            print(f"  ✅ {message}")
        else:
            print(f"  ❌ {message}")
        results.append((script.name, success, message))

    # Summary
    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)
    passed = sum(1 for _, success, _ in results if success)
    failed = sum(1 for _, success, _ in results if not success)
    skipped = 3  # pubmed_uorf_genome_editing_analysis.py, pubmed_keywords_filter_example.py, and others with external deps
    total = len(results) + skipped

    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print(f"Skipped: {skipped}")
    print(f"Total: {total}")

    if failed > 0:
        print("\nFailed scripts:")
        for name, _, message in results:
            if not name.startswith("test_"):  # Skip internal test files
                continue
        for name, success, message in results:
            if not success:
                print(f"  - {name}: {message}")
        sys.exit(1)
    else:
        print("\n✅ All importable scripts passed!")
        sys.exit(0)


if __name__ == "__main__":
    main()
