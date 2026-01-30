#!/usr/bin/env python3
"""
Create sample test data for examples.
"""

from pathlib import Path


def create_sample_pdf():
    """Create a sample PDF file for testing."""
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.pdfgen import canvas

        sample_pdf = Path(__file__).parent / "test_data" / "sample.pdf"
        sample_pdf.parent.mkdir(parents=True, exist_ok=True)

        c = canvas.Canvas(str(sample_pdf), pagesize=letter)
        c.drawString(100, 750, "Sample PDF for Testing")
        c.drawString(100, 700, "This is a test PDF file for pdf-validator example.")
        c.drawString(
            100, 650, "It contains basic content to verify the validator works."
        )
        c.save()

        print(f"Created sample PDF: {sample_pdf}")
        return True

    except ImportError:
        print("Warning: reportlab not installed, skipping PDF creation")
        return False


def create_sample_rss_feed():
    """Create a sample RSS feed file for testing."""
    sample_rss = Path(__file__).parent / "test_data" / "sample_feed.xml"

    rss_content = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>Test Feed</title>
    <description>A sample RSS feed for testing</description>
    <link>https://example.com</link>
    <item>
      <title>Test Article 1</title>
      <description>A test article description</description>
      <link>https://example.com/article1</link>
      <guid isPermaLink="false">article1</guid>
      <pubDate>Wed, 01 Jan 2024 00:00:00 +0000</pubDate>
    </item>
    <item>
      <title>Test Article 2</title>
      <description>Another test article</description>
      <link>https://example.com/article2</link>
      <guid isPermaLink="false">article2</guid>
      <pubDate>Thu, 02 Jan 2024 00:00:00 +0000</pubDate>
    </item>
  </channel>
</rss>
"""

    sample_rss.parent.mkdir(parents=True, exist_ok=True)
    sample_rss.write_text(rss_content)
    print(f"Created sample RSS feed: {sample_rss}")


def create_sample_markdown():
    """Create a sample Markdown file for testing."""
    sample_md = Path(__file__).parent / "test_data" / "sample.md"

    md_content = """# Sample Markdown Document

## Abstract

This is a sample markdown document for testing the markdown processing features.

## Introduction

This document contains various markdown elements to test parsing and conversion.

## Methods

We used the following methods:
1. Data collection
2. Data analysis
3. Result validation

## Results

The results show significant improvements in all metrics.

## Conclusion

This sample document demonstrates basic markdown structure.
"""

    sample_md.parent.mkdir(parents=True, exist_ok=True)
    sample_md.write_text(md_content)
    print(f"Created sample Markdown: {sample_md}")


if __name__ == "__main__":
    create_sample_pdf()
    create_sample_rss_feed()
    create_sample_markdown()
    print("\nTest data creation complete!")
