from collections import Counter
import csv
from glob import glob
import json
from os import path

from information_composer.markdown import dictify, markdownify  # jsonify unused


def main():
    markdown_files = glob("./data/markdown/file/*.md")

    output_dir = "./data/markdown/filtered/"

    # Define multiple filter terms
    filters = [
        "reference",
        "acknowledgments",
        "funding",
        "license",
        "author contributions",
    ]

    csv_path = "./data/key_counts.csv"

    key_dict = Counter()

    for markdown_file in markdown_files:
        with open(markdown_file, encoding="utf-8") as f:
            markdown_content = f.read()

        dict_content = dictify(markdown_content)

        # Count all keys in the current file
        for key in dict_content:
            key_dict[key] += 1

        # Create a list of keys to delete (modified to check against any filter term)
        keys_to_delete = [
            key for key in dict_content if any(f in key.lower() for f in filters)
        ]

        # Print what we're going to delete
        for key in keys_to_delete:
            print(f"Found in {markdown_file}:")
            print(f"Removing: {key}")

        # Delete the keys after iteration
        for key in keys_to_delete:
            del dict_content[key]

        json_content = json.dumps(dict_content)

        markdown_content = markdownify(json_content)

        output_file = path.join(
            output_dir, path.basename(markdown_file).replace(".md", "_filtered.md")
        )
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(markdown_content)

    # Export key counts to CSV

    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Key", "Count"])  # Header
        # Sort by count in descending order
        for key, count in sorted(key_dict.items(), key=lambda x: x[1], reverse=True):
            writer.writerow([key, count])

    print(f"Key counts exported to: {csv_path}")


if __name__ == "__main__":
    main()
