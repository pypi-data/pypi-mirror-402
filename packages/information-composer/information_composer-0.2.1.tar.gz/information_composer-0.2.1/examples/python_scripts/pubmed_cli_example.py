#!/usr/bin/env python3
"""
PubMed CLI Tool Usage Example

This example demonstrates how to use the PubMed CLI tool through various
command-line operations. It shows the different subcommands available and
their help information, providing a comprehensive overview of CLI functionality.

The example covers:
- Displaying help information for all CLI commands
- Understanding command syntax and parameters
- Error handling and output interpretation
- Best practices for CLI usage

Requirements:
    - information_composer package installed
    - PubMed CLI tool available in PATH
    - Valid email address for actual searches

Usage:
    python pubmed_cli_example.py

Note:
    This example only shows help information and command syntax.
    For actual searches, replace placeholder email with a real address.
"""

import subprocess


# import sys  # Unused import


def run_command(cmd):
    """
    Execute a command and display its output with error handling.

    This function demonstrates how to run CLI commands programmatically
    and handle both successful execution and errors gracefully.

    Args:
        cmd (list): Command and arguments as a list of strings

    Returns:
        None

    Raises:
        None (errors are caught and displayed)

    Example:
        >>> run_command(["pubmed-cli", "search", "--help"])
        Running: pubmed-cli search --help
        Output:
        Usage: pubmed-cli search [OPTIONS] QUERY
        ...
    """
    print(f"Running: {' '.join(cmd)}")
    try:
        # Execute the command and capture both stdout and stderr
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        print("Output:")
        print(result.stdout)

        # Display stderr if present (warnings, etc.)
        if result.stderr:
            print("Errors:")
            print(result.stderr)

    except subprocess.CalledProcessError as e:
        # Handle command execution errors
        print(f"Command failed with return code {e.returncode}")
        print("Output:")
        print(e.stdout)
        print("Error:")
        print(e.stderr)
    except FileNotFoundError:
        # Handle case where command is not found
        print(
            "Error: Command not found. Make sure pubmed-cli is installed and in PATH."
        )
    except Exception as e:
        # Handle other unexpected errors
        print(f"Unexpected error: {e}")

    print("-" * 50)


def main():
    """
    Demonstrate PubMed CLI tool usage through help command examples.

    This function shows how to access help information for all available
    CLI commands, providing users with a comprehensive understanding of
    the tool's capabilities and usage patterns.

    The function demonstrates:
    - Help command syntax
    - Command parameter discovery
    - Error handling for missing commands
    - Best practices for CLI usage

    Args:
        None

    Returns:
        None

    Raises:
        None (all errors are handled gracefully)

    Example:
        >>> main()
        PubMed CLI Tool Examples
        ==================================================
        Example 1: Help for search command
        Running: pubmed-cli search --help
        ...
    """
    print("PubMed CLI Tool Examples")
    print("=" * 50)

    # Example 1: Search command help
    # This shows how to search for publications using the CLI
    print("Example 1: Help for search command")
    run_command(["pubmed-cli", "search", "--help"])

    # Example 2: Details command help
    # This shows how to fetch detailed information for specific PMIDs
    print("Example 2: Help for details command")
    run_command(["pubmed-cli", "details", "--help"])

    # Example 3: Batch command help
    # This shows how to process multiple operations in batch
    print("Example 3: Help for batch command")
    run_command(["pubmed-cli", "batch", "--help"])

    # Example 4: Cache command help
    # This shows how to manage cached data
    print("Example 4: Help for cache command")
    run_command(["pubmed-cli", "cache", "--help"])

    # Display usage instructions for actual searches
    print("Examples completed. To run actual searches, use a valid email address.")
    print("Example: pubmed-cli search 'cancer research' -e your.email@example.com")
    print(
        "\nFor more information, visit the documentation or use --help "
        "with any command."
    )


if __name__ == "__main__":
    # Entry point for the script
    # This ensures the demo only runs when the script is executed directly,
    # not when imported as a module
    main()
