# ricedatacn_gene_parser

A Python toolkit for collecting and composing information from various web resources.

## Features

- Extract gene information from ricedata.cn
- Parse and structure reference data
- Support for both English and Chinese content
- Automatic encoding detection (UTF-8, GB2312)
- JSON output format

## Installation

### Install dependencies

```bash
pip install -r requirements.txt
```

### Clone the repository

```bash
git clone https://github.com/yourusername/information-composer.git
```

### Navigate to the project directory

```bash
cd information-composer
pip install -e . 
```

## Usage

### Basic Example

```python    
from information_composer.core.rice_gene_parser import RiceGeneParser
```

Initialize parser

```python
parser = RiceGeneParser()
```

Parse single gene

```python    
gene_info = parser.parse_gene_page("1", "downloads/genes")
```

Parse multiple genes

```python
gene_ids = ["1", "2", "3"]
results = parser.parse_multiple_genes(gene_ids, "downloads/genes")
```

### Output Format

The parsed data is saved in JSON format with the following structure:

```json
{
  "gene_id": "1",
  "url": "https://www.ricedata.cn/gene/list/1.htm",
  "basic_info": {
    // Basic information about the gene
    ...
  },
  "description": "...",
  "ontology": {
    // Ontology information related to the gene
    ...
  },
  "references": [
    {
      "reference_info": "...",
      "reference_url": "...",
      "title": "...",
      "doi": "...",
      "abstract_en": "...",
      "abstract_cn": "..."
    }
  ]
}
```

## Dependencies

- requests
- beautifulsoup4
- urllib3

## Project Structure

```
information-composer/
├── src/
│   └── information_composer/
│       └── core/
│           └── rice_gene_parser.py
├── examples/
│   └── rice_gene_example.py
├── downloads/
│   └── genes/
├── README.md
├── README_zh.md
└── requirements.txt
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.