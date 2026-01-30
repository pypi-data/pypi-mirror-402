# RiceDataCN Integration Guide

This guide explains how to use the RiceDataCN gene parser to extract gene information from the RiceDataCN website.

## Overview

The RiceDataCN gene parser allows you to:
- Parse individual gene pages for detailed information
- Batch process multiple genes
- Extract basic gene information, descriptions, ontology data, and references
- Save results in JSON format

## Installation

The RiceDataCN parser requires the following dependencies:

```bash
pip install requests beautifulsoup4
```

## Basic Usage

### Single Gene Parsing

```python
from information_composer.sites.ricedatacn_gene_parser import RiceGeneParser

# Initialize parser
parser = RiceGeneParser()

# Parse a single gene
gene_info = parser.parse_gene_page("1", "output/genes")

if gene_info:
    print(f"Gene ID: {gene_info['gene_id']}")
    print(f"Basic Info: {gene_info['basic_info']}")
    print(f"Description: {gene_info['description'][:200]}...")
    print(f"References: {len(gene_info['references'])}")
else:
    print("Failed to parse gene")
```

### Batch Gene Parsing

```python
# Parse multiple genes
gene_ids = ["1", "2", "3", "100000"]  # Including non-existent gene
results = parser.parse_multiple_genes(gene_ids, "output/genes")

# Check results
for i, result in enumerate(results):
    gene_id = gene_ids[i]
    if result:
        print(f"Gene {gene_id}: Success")
        print(f"  - Basic info fields: {len(result['basic_info'])}")
        print(f"  - References: {len(result['references'])}")
    else:
        print(f"Gene {gene_id}: Failed (404 Not Found)")
```

## Configuration

You can configure the parser with custom settings:

```python
config = {
    "timeout": 60,        # Request timeout in seconds
    "retries": 5,         # Number of retry attempts
    "encoding": "gb2312"  # Page encoding
}

parser = RiceGeneParser(config)
```

## Data Structure

The parsed gene information contains:

### Basic Information
- Gene ID and name
- Chromosome location
- Gene type and function
- Expression data

### Description
- Detailed gene description
- Functional annotations
- Expression patterns

### Ontology Data
- Gene Ontology (GO) terms
- Molecular function
- Biological process
- Cellular component

### References
- Literature references
- DOI information (if available)
- Abstracts (English and Chinese)

## Error Handling

The parser handles various error conditions gracefully:

```python
try:
    gene_info = parser.parse_gene_page("nonexistent_gene")
    if gene_info is None:
        print("Gene not found (404 error)")
except Exception as e:
    print(f"Parsing error: {e}")
```

## Advanced Usage

### Custom Output Directory

```python
import os
from pathlib import Path

# Create custom output directory
output_dir = Path("data/rice_genes")
output_dir.mkdir(parents=True, exist_ok=True)

# Parse genes to custom directory
results = parser.parse_multiple_genes(
    ["1", "2", "3"], 
    str(output_dir)
)
```

### Processing Results

```python
def process_gene_results(results):
    """Process and analyze gene parsing results."""
    successful = [r for r in results if r is not None]
    failed = [r for r in results if r is None]
    
    print(f"Successfully parsed: {len(successful)} genes")
    print(f"Failed to parse: {len(failed)} genes")
    
    # Analyze successful results
    for result in successful:
        gene_id = result['gene_id']
        basic_info = result['basic_info']
        
        # Check for specific information
        if 'Gene Name' in basic_info:
            print(f"Gene {gene_id}: {basic_info['Gene Name']}")
        
        # Check ontology data
        ontology = result.get('ontology', {})
        if ontology:
            print(f"  Ontology categories: {list(ontology.keys())}")
        
        # Check references
        references = result.get('references', [])
        if references:
            print(f"  References: {len(references)}")

# Process results
process_gene_results(results)
```

### Filtering and Validation

```python
def validate_gene_info(gene_info):
    """Validate gene information completeness."""
    if not gene_info:
        return False
    
    required_fields = ['gene_id', 'basic_info', 'description']
    for field in required_fields:
        if field not in gene_info:
            return False
    
    # Check basic info completeness
    basic_info = gene_info['basic_info']
    if not basic_info or len(basic_info) < 3:
        return False
    
    return True

# Filter valid results
valid_results = [r for r in results if validate_gene_info(r)]
print(f"Valid results: {len(valid_results)}")
```

## Best Practices

### 1. Rate Limiting
Be respectful to the RiceDataCN server:

```python
import time

def parse_genes_with_delay(parser, gene_ids, delay=1.0):
    """Parse genes with delay between requests."""
    results = []
    for gene_id in gene_ids:
        result = parser.parse_gene_page(gene_id)
        results.append(result)
        time.sleep(delay)  # Delay between requests
    return results
```

### 2. Error Logging
Implement proper error logging:

```python
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def parse_gene_with_logging(parser, gene_id):
    """Parse gene with logging."""
    try:
        result = parser.parse_gene_page(gene_id)
        if result:
            logger.info(f"Successfully parsed gene {gene_id}")
        else:
            logger.warning(f"Failed to parse gene {gene_id}")
        return result
    except Exception as e:
        logger.error(f"Error parsing gene {gene_id}: {e}")
        return None
```

### 3. Data Persistence
Save results for later analysis:

```python
import json
from datetime import datetime

def save_parsing_session(gene_ids, results, output_dir):
    """Save parsing session results."""
    session_data = {
        "timestamp": datetime.now().isoformat(),
        "gene_ids": gene_ids,
        "results": results,
        "summary": {
            "total": len(gene_ids),
            "successful": len([r for r in results if r]),
            "failed": len([r for r in results if r is None])
        }
    }
    
    session_file = Path(output_dir) / "parsing_session.json"
    with open(session_file, 'w', encoding='utf-8') as f:
        json.dump(session_data, f, ensure_ascii=False, indent=2)
    
    print(f"Session saved to {session_file}")
```

## Troubleshooting

### Common Issues

1. **404 Not Found**: Gene ID doesn't exist
   - Check gene ID format
   - Verify gene exists on RiceDataCN

2. **Encoding Issues**: Chinese characters not displaying correctly
   - Ensure proper encoding (GB2312)
   - Check terminal/console encoding

3. **Network Timeouts**: Slow or failed requests
   - Increase timeout value
   - Add retry logic
   - Check network connection

### Debug Mode

Enable debug mode for detailed logging:

```python
import logging

# Enable debug logging
logging.basicConfig(level=logging.DEBUG)

# Parse with debug information
parser = RiceGeneParser()
gene_info = parser.parse_gene_page("1")
```

## Example Script

Here's a complete example script:

```python
#!/usr/bin/env python3
"""
RiceDataCN Gene Parser Example
"""

import os
import json
from pathlib import Path
from information_composer.sites.ricedatacn_gene_parser import RiceGeneParser

def main():
    # Initialize parser
    parser = RiceGeneParser()
    
    # Set output directory
    output_dir = Path("downloads/genes")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Gene IDs to parse
    gene_ids = ["1", "2", "3", "100000"]  # Including non-existent gene
    
    print("Parsing genes from RiceDataCN...")
    print(f"Gene IDs: {gene_ids}")
    print(f"Output directory: {output_dir}")
    print()
    
    # Parse genes
    results = parser.parse_multiple_genes(gene_ids, str(output_dir))
    
    # Process results
    successful = []
    failed = []
    
    for i, result in enumerate(results):
        gene_id = gene_ids[i]
        if result:
            successful.append((gene_id, result))
            print(f"✅ Gene {gene_id}: Success")
        else:
            failed.append(gene_id)
            print(f"❌ Gene {gene_id}: Failed")
    
    # Summary
    print()
    print("=" * 50)
    print("PARSING SUMMARY")
    print("=" * 50)
    print(f"Total genes: {len(gene_ids)}")
    print(f"Successful: {len(successful)}")
    print(f"Failed: {len(failed)}")
    
    if successful:
        print()
        print("Successful genes:")
        for gene_id, result in successful:
            basic_info = result.get('basic_info', {})
            gene_name = basic_info.get('Gene Name', 'Unknown')
            print(f"  - {gene_id}: {gene_name}")
    
    if failed:
        print()
        print("Failed genes:")
        for gene_id in failed:
            print(f"  - {gene_id}")

if __name__ == "__main__":
    main()
```

This guide provides comprehensive information for using the RiceDataCN gene parser effectively. The parser is designed to be robust and handle various error conditions while providing detailed gene information for further analysis.


