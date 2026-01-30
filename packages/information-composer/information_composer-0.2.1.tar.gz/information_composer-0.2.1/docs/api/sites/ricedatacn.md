# RiceDataCN Gene Parser API

## RiceGeneParser

Parser for extracting gene information from ricedata.cn.

### Constructor

```python
RiceGeneParser(config: Optional[Dict[str, Any]] = None) -> None
```

Initialize the RiceGeneParser.

**Parameters:**
- `config` (Optional[Dict[str, Any]]): Optional configuration dictionary

**Attributes:**
- `name` (str): The name of the parser ("RiceGeneParser")
- `config` (Dict[str, Any]): Configuration dictionary
- `base_url` (str): Base URL for RiceDataCN gene pages
- `headers` (Dict[str, str]): HTTP headers for requests

### Methods

#### parse_gene_page()

```python
def parse_gene_page(
    self, 
    gene_id: str, 
    output_dir: str = "downloads/genes"
) -> Optional[Dict[str, Any]]
```

Parse gene information from ricedata.cn webpage.

**Parameters:**
- `gene_id` (str): The gene ID to parse
- `output_dir` (str): Directory to save the output file

**Returns:**
- `Optional[Dict[str, Any]]`: Dictionary containing parsed gene information, or None if parsing failed

**Example:**
```python
parser = RiceGeneParser()
gene_info = parser.parse_gene_page("1", "output/genes")
if gene_info:
    print(f"Gene ID: {gene_info['gene_id']}")
    print(f"Basic info: {gene_info['basic_info']}")
```

#### parse_multiple_genes()

```python
def parse_multiple_genes(
    self, 
    gene_ids: List[str], 
    output_dir: str = "downloads/genes"
) -> List[Optional[Dict[str, Any]]]
```

Parse multiple genes and save their information.

**Parameters:**
- `gene_ids` (List[str]): List of gene IDs to parse
- `output_dir` (str): Directory to save the JSON files

**Returns:**
- `List[Optional[Dict[str, Any]]]`: List of parsed gene information dictionaries

**Example:**
```python
parser = RiceGeneParser()
gene_ids = ["1", "2", "3"]
results = parser.parse_multiple_genes(gene_ids, "output/genes")
for i, result in enumerate(results):
    if result:
        print(f"Gene {gene_ids[i]}: Success")
    else:
        print(f"Gene {gene_ids[i]}: Failed")
```

### Data Structure

The parsed gene information contains the following structure:

```python
{
    "gene_id": str,           # Gene ID
    "url": str,              # URL of the gene page
    "basic_info": {          # Basic gene information
        "Gene ID": str,
        "Gene Name": str,
        # ... other fields
    },
    "description": str,      # Gene description
    "ontology": {            # Gene ontology information
        "Molecular Function": [
            {
                "term": str,
                "id": str
            }
        ],
        # ... other ontology categories
    },
    "references": [          # Reference information
        {
            "reference_info": str,
            "reference_url": str,
            "title": str,        # If details were fetched
            "doi": str,          # If available
            "abstract_en": str,  # If available
            "abstract_cn": str   # If available
        }
    ]
}
```

### Error Handling

The parser handles various error conditions:

- **404 Not Found**: Returns `None` for non-existent gene IDs
- **Network Errors**: Returns `None` and logs the error
- **Parsing Errors**: Returns `None` and logs the error

### Example Usage

```python
from information_composer.sites.ricedatacn_gene_parser import RiceGeneParser

# Initialize parser
parser = RiceGeneParser()

# Parse single gene
gene_info = parser.parse_gene_page("LOC_Os01g01010")
if gene_info:
    print(f"Gene: {gene_info['basic_info'].get('Gene Name', 'Unknown')}")
    print(f"Description: {gene_info['description'][:100]}...")
    print(f"References: {len(gene_info['references'])}")

# Parse multiple genes
gene_ids = ["1", "2", "3", "100000"]  # Including non-existent gene
results = parser.parse_multiple_genes(gene_ids, "output/genes")

# Check results
success_count = sum(1 for r in results if r)
print(f"Successfully parsed {success_count} out of {len(gene_ids)} genes")
```

### Configuration

The parser can be configured with the following options:

```python
config = {
    "timeout": 30,        # Request timeout in seconds
    "retries": 3,         # Number of retry attempts
    "encoding": "gb2312"  # Page encoding
}

parser = RiceGeneParser(config)
```

### Dependencies

- `requests`: For HTTP requests
- `beautifulsoup4`: For HTML parsing
- `pathlib`: For file path handling


