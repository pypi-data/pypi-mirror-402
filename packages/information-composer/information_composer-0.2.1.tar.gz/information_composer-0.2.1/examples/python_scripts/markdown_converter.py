import json
from pathlib import Path
from typing import Optional, Union

from information_composer.markdown import jsonify


def convert_markdown_to_json(
    markdown_file_path: str | Path,
    json_output_path: str | Path | None = None,
) -> str:
    """
    Convert markdown file to JSON format

    Args:
        markdown_file_path: Path to markdown file
        json_output_path: Optional path to save JSON output

    Returns:
        str: JSON string of parsed markdown content
    """
    # Convert to Path objects
    md_path = Path(markdown_file_path)

    # Verify markdown file exists
    if not md_path.exists():
        raise FileNotFoundError(f"Markdown file not found: {markdown_file_path}")

    # Read markdown file
    with open(md_path, encoding="utf-8") as f:
        markdown_content = f.read()

    # Convert to JSON
    json_content = jsonify(markdown_content)

    # Save JSON if output path specified
    if json_output_path:
        json_path = Path(json_output_path)

        # Create parent directories if they don't exist
        json_path.parent.mkdir(parents=True, exist_ok=True)

        with open(json_path, "w", encoding="utf-8") as f:
            # Parse and re-dump to get pretty formatting
            parsed = json.loads(json_content)
            json.dump(parsed, f, indent=2, ensure_ascii=False)

    return json_content


def main():
    # Example usage
    try:
        # Convert doi_downloader.md to JSON
        markdown_path = "docs/doi_downloader.md"
        json_path = "docs/doi_downloader.json"

        result = convert_markdown_to_json(markdown_path, json_path)
        print(f"Successfully converted {markdown_path} to JSON")
        print(f"Output saved to: {json_path}")

        # Print first 100 characters of JSON
        print("\nPreview of JSON output:")
        print(result[:100] + "...")

    except Exception as e:
        print(f"Error converting markdown to JSON: {str(e)}")


if __name__ == "__main__":
    main()
