import os

from information_composer.sites.ricedatacn_gene_parser import RiceGeneParser


def main():
    # Initialize parser
    parser = RiceGeneParser()

    # Set output directory
    output_dir = os.path.join(os.getcwd(), "downloads", "genes")

    # Single gene example
    print("Parsing single gene...")
    # gene_info = parser.parse_gene_page("1", output_dir)  # Unused variable

    # Multiple genes example with a non-existent gene ID
    print("\nParsing multiple genes (including non-existent gene)...")
    gene_ids = ["1", "2", "3", "100000"]  # 添加了不存在的基因 ID 100000
    results = parser.parse_multiple_genes(gene_ids, output_dir)

    # Print detailed summary
    print("\nSummary:")
    success_count = len([r for r in results if r])
    print(f"Successfully parsed {success_count} out of {len(gene_ids)} genes")
    print(f"Failed to parse {len(gene_ids) - success_count} genes")

    # Print which genes were successful and which failed
    print("\nDetailed results:")
    for gene_id, result in zip(gene_ids, results, strict=False):
        status = "Success" if result else "Failed (404 Not Found)"
        print(f"Gene {gene_id}: {status}")


if __name__ == "__main__":
    main()
