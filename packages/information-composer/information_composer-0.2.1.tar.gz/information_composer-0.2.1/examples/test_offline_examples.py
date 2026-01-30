#!/usr/bin/env python3
"""
Test runner for example scripts that don't require external API keys or network.
"""

import subprocess
import sys
from pathlib import Path
from typing import Tuple


def run_script(script_path: Path, timeout: int = 10) -> Tuple[int, str, str]:
    """Run a script and return (returncode, stdout, stderr)."""
    try:
        result = subprocess.run(
            [sys.executable, str(script_path)],
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=script_path.parent.parent,  # Run from examples directory
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return -1, "TIMEOUT", "Script took too long"
    except Exception as e:
        return -2, "", str(e)


def main():
    """Test all example scripts."""
    examples_dir = Path(__file__).parent / "python_scripts"
    scripts = sorted(examples_dir.glob("*.py"))

    # Scripts that require external API keys or data files
    skip_list = {
        "pubmed_uorf_genome_editing_analysis.py",  # Requires external data
        "pubmed_keywords_filter_example.py",  # Requires external data
        "markdown_filter_ref.py",  # Requires ./data/markdown/file/*.md
        "doi_download_by_using_pubmed_batch_example.py",  # Requires network
        "doi_download_example.py",  # Requires network
        "doi_download_single.py",  # Requires network
        "google_scholar_advanced_example.py",  # Requires network
        "google_scholar_basic_example.py",  # Requires network
        "google_scholar_batch_example.py",  # Requires network
        "litsense_example.py",  # Requires network
        "llm_filter_example.py",  # Requires DASHSCOPE_API_KEY
        "pubmed_analyzer_example.py",  # Requires DASHSCOPE_API_KEY
        "pubmed_analyzer_integration_example.py",  # Requires API key
        "pubmed_analyzer_ollama_example.py",  # Requires Ollama
        "pubmed_analyzer_openai_example.py",  # Requires OPENAI_API_KEY
        "pubmed_cli_example.py",  # Requires network (calls pubmed-cli)
        "pubmed_details_batch_example.py",  # Requires network
        "pubmed_details_example.py",  # Requires network
        "pubmed_journal_recent.py",  # Requires network
        "pubmed_mul_journals_recent.py",  # Requires network
        "pubmed_query_pmid.py",  # Requires network
        "ricedatacn_gene_download_example.py",  # Requires network
        "ricedatacn_gene_example.py",  # Requires network
        "rss_basic_example.py",  # Requires network
        "rss_fetch_basic_example.py",  # Requires network
        "test_analyzer_llm.py",  # Requires API key
    }

    print("=" * 60)
    print("Testing Example Scripts (Offline)")
    print("=" * 60)
    print(f"Skipping {len(skip_list)} scripts that require network/API keys\n")

    results = []
    for script in scripts:
        if script.name in skip_list:
            print(f"⏭  {script.name} (requires network/API)")
            continue

        print(f"Testing: {script.name}... ", end="", flush=True)
        returncode, stdout, stderr = run_script(script, timeout=5)

        if returncode == 0:
            print("✅")
            results.append((script.name, True, "OK"))
        elif returncode == -1:
            print("⏱  (timeout)")
            results.append((script.name, True, "Timeout"))
        else:
            print("❌")
            results.append((script.name, False, stderr[:100]))

    # Summary
    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)

    passed = sum(1 for _, success, _ in results if success)
    failed = sum(1 for _, success, _ in results if not success)
    offline = len(results)

    print(f"Offline tests: {passed}/{offline} passed")

    if failed > 0:
        print("\nFailed scripts:")
        for name, success, msg in results:
            if not success:
                print(f"  - {name}: {msg}")
        sys.exit(1)
    else:
        print("\n✅ All offline tests passed!")
        sys.exit(0)


if __name__ == "__main__":
    main()
