"""
PubMed UTR/uORF 基因组编辑分析示例

功能流程：
1. 在 PubMed 搜索 ((Plant) AND (uORF OR UTR)) 相关论文
2. 获取论文详细信息并保存到 CSV
3. 使用 LLM (qwen3-max) 分析论文摘要，识别是否涉及 UTR/uORF 的基因组编辑
"""

import asyncio
import csv
import json
import logging
import os
from pathlib import Path
import time
from typing import Any

from information_composer.pubmed import fetch_pubmed_details_batch, query_pmid


# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def load_analysis_cache(cache_file: Path) -> dict[str, dict[str, Any]]:
    """
    Load cached analysis results from JSON file

    Args:
        cache_file: Path to cache file

    Returns:
        Dictionary mapping PMID to analysis results
    """
    if cache_file.exists():
        try:
            with open(cache_file, encoding="utf-8") as f:
                cached_data = json.load(f)
                logger.info(f"Loaded {len(cached_data)} cached analysis results")
                return {item.get("pmid", ""): item for item in cached_data}
        except Exception as e:
            logger.warning(f"Failed to load cache file: {e}")
    return {}


def save_analysis_cache(cache_file: Path, results: list[dict[str, Any]]) -> None:
    """
    Save analysis results to cache file

    Args:
        cache_file: Path to cache file
        results: List of analysis results
    """
    try:
        cache_file.parent.mkdir(parents=True, exist_ok=True)
        with open(cache_file, "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        logger.info(f"Saved {len(results)} analysis results to cache")
    except Exception as e:
        logger.error(f"Failed to save cache file: {e}")


async def analyze_paper_with_retry(
    analysis_chain: Any,
    paper: dict[str, Any],
    max_retries: int = 3,
) -> dict[str, Any]:
    """
    Analyze a single paper with retry mechanism

    Args:
        analysis_chain: LangChain analysis chain
        paper: Paper data
        max_retries: Maximum number of retries

    Returns:
        Analysis result dictionary
    """
    import re

    # Extract year from pubdate
    pubdate = paper.get("pubdate", "")
    year = ""
    if pubdate:
        year_match = re.search(r"\b(\d{4})\b", pubdate)
        if year_match:
            year = year_match.group(1)

    for attempt in range(max_retries):
        try:
            # Call LLM analysis
            result = await analysis_chain.ainvoke(
                {
                    "title": paper.get("title", ""),
                    "abstract": paper.get("abstract", ""),
                }
            )

            # Add paper basic information
            result["pmid"] = paper.get("pmid", "")
            result["title"] = paper.get("title", "")
            result["abstract"] = paper.get("abstract", "")
            result["journal"] = paper.get("journal", "")
            result["year"] = year
            result["doi"] = paper.get("doi", "")
            result["authors"] = "; ".join(paper.get("authors", []))

            # Ensure required fields exist
            if "phenotype_description" not in result:
                result["phenotype_description"] = "No phenotype information extracted"
            if "abstract_chinese" not in result:
                result["abstract_chinese"] = "Translation failed"

            return result

        except Exception as e:
            if attempt < max_retries - 1:
                wait_time = 2**attempt  # Exponential backoff
                logger.warning(
                    f"Analysis failed for PMID {paper.get('pmid', 'N/A')} "
                    f"(attempt {attempt + 1}/{max_retries}): {e}. "
                    f"Retrying in {wait_time}s..."
                )
                await asyncio.sleep(wait_time)
            else:
                logger.error(
                    f"Analysis failed for PMID {paper.get('pmid', 'N/A')} "
                    f"after {max_retries} attempts: {e}"
                )

    # Return failure result
    return {
        "pmid": paper.get("pmid", ""),
        "title": paper.get("title", ""),
        "abstract": paper.get("abstract", ""),
        "journal": paper.get("journal", ""),
        "year": year,
        "doi": paper.get("doi", ""),
        "authors": "; ".join(paper.get("authors", [])),
        "is_genome_editing": False,
        "editing_targets": [],
        "editing_methods": [],
        "plant_species": [],
        "phenotype_description": "Analysis failed",
        "abstract_chinese": "Translation failed",
        "confidence": 0.0,
        "reasoning": "Analysis failed after multiple retries",
    }


convert_pubmed_to_dict = lambda x: x  # Not used anymore


async def main():
    """主函数"""
    # ==================== 配置参数 ====================
    # PubMed 搜索参数
    search_query = "((Plant) AND (uORF OR UTR))"
    email = "your_email@example.com"  # 请替换为您的邮箱
    max_results = 2000  # 限制结果数量，可根据需要调整

    # 输出目录
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)

    # CSV 输出文件
    csv_file = output_dir / "pubmed_uorf_utr_papers.csv"

    # Final output files
    analysis_json_file = output_dir / "uorf_genome_editing_analysis.json"
    final_csv_file = output_dir / "pubmed_uorf_final_results.csv"
    editing_papers_csv_file = (
        output_dir / "pubmed_uorf_editing_papers_only.csv"
    )  # Only papers with genome editing
    detailed_csv_file = output_dir / "uorf_genome_editing_detailed_analysis.csv"
    llm_analysis_cache_file = output_dir / "llm_analysis_cache.json"

    # 缓存目录
    cache_dir = output_dir / "pubmed_cache"

    # 从环境变量获取 OpenAI 配置
    openai_base_url = os.getenv("OPENAI_BASE_URL")
    openai_api_key = os.getenv("OPENAI_API_KEY")

    if not openai_base_url or not openai_api_key:
        logger.error("请设置环境变量 OPENAI_BASE_URL 和 OPENAI_API_KEY")
        logger.info("示例：")
        logger.info(
            "  export OPENAI_BASE_URL='https://dashscope.aliyuncs.com/compatible-mode/v1'"
        )
        logger.info("  export OPENAI_API_KEY='your-api-key'")
        return

    # ==================== 步骤 1: 搜索 PubMed ====================
    logger.info("=" * 80)
    logger.info(f"步骤 1: 搜索 PubMed - 查询: {search_query}")
    logger.info("=" * 80)

    pmids = query_pmid(search_query, email=email, retmax=max_results)
    logger.info(f"找到 {len(pmids)} 篇相关论文")

    if not pmids:
        logger.warning("未找到相关论文，程序退出")
        return

    # ==================== 步骤 2: 获取论文详情 ====================
    logger.info("\n" + "=" * 80)
    logger.info("步骤 2: 获取论文详细信息")
    logger.info("=" * 80)

    papers = await fetch_pubmed_details_batch(
        pmids=pmids,
        email=email,
        cache_dir=str(cache_dir),
        chunk_size=100,
        delay_between_chunks=0.5,
    )

    logger.info(f"成功获取 {len(papers)} 篇论文的详细信息")

    # ==================== 步骤 3: 保存到 CSV ====================
    logger.info("\n" + "=" * 80)
    logger.info(f"步骤 3: 保存论文信息到 CSV - {csv_file}")
    logger.info("=" * 80)

    # 定义 CSV 字段
    csv_fields = [
        "pmid",
        "title",
        "abstract",
        "journal",
        "pubdate",
        "authors",
        "doi",
        "mesh_terms",
        "keywords",
    ]

    with open(csv_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=csv_fields)
        writer.writeheader()

        for paper in papers:
            # 处理列表类型的字段
            row = {
                "pmid": paper.get("pmid", ""),
                "title": paper.get("title", ""),
                "abstract": paper.get("abstract", ""),
                "journal": paper.get("journal", ""),
                "pubdate": paper.get("pubdate", ""),
                "authors": "; ".join(paper.get("authors", [])),
                "doi": paper.get("doi", ""),
                "mesh_terms": "; ".join(paper.get("mesh_terms", [])),
                "keywords": "; ".join(paper.get("keywords", [])),
            }
            writer.writerow(row)

    logger.info(f"论文信息已保存到: {csv_file}")

    # ==================== 步骤 4: LLM 分析 - 识别基因组编辑相关论文 ====================
    logger.info("\n" + "=" * 80)
    logger.info("步骤 4: 使用 LLM 分析论文 - 识别 UTR/uORF 基因组编辑")
    logger.info("=" * 80)

    # 使用 LangChain 直接进行自定义分析
    from langchain_core.output_parsers import JsonOutputParser
    from langchain_core.prompts import ChatPromptTemplate
    from langchain_openai import ChatOpenAI

    # Create LLM instance
    from pydantic import SecretStr

    llm = ChatOpenAI(
        model="qwen-max",
        api_key=SecretStr(openai_api_key) if openai_api_key else None,  # type: ignore
        base_url=openai_base_url,
        temperature=0.1,
        timeout=120,  # Increase timeout for long abstracts
        max_retries=2,
    )

    # Custom analysis prompt - Identify genome editing and extract phenotype information with Chinese translation
    custom_prompt_template = """Please analyze the following research paper abstract and complete three tasks:
1. Determine whether this paper involves genome editing of UTR (Untranslated Region) or uORF (upstream Open Reading Frame)
2. If editing is involved, extract the phenotypic changes observed after editing from the abstract
3. Translate the English abstract into Chinese

Paper Information:
Title: {title}
Abstract: {abstract}

Please return the analysis results in the following JSON format:
{{
    "is_genome_editing": true/false,
    "editing_targets": ["UTR", "uORF", "5'UTR", "3'UTR"],  // If genome editing is involved, list the editing targets
    "editing_methods": ["CRISPR/Cas9", "TALEN", "ZFN", "Other"],  // If genome editing is involved, list the editing technologies used
    "plant_species": ["Arabidopsis", "Rice", "Wheat"],  // Plant species involved (in Chinese)
    "phenotype_description": "Phenotype description extracted from abstract",  // IMPORTANT: If uORF/UTR editing is involved, describe in detail the phenotypic changes observed after editing, including morphology, physiology, yield, resistance, etc.; if not involved, fill in "No genome editing involved"
    "abstract_chinese": "Chinese translation of the abstract",  // Accurately translate the English abstract into fluent Chinese, maintaining the accuracy of scientific terminology
    "confidence": 0.0-1.0,  // Confidence level of the judgment
    "reasoning": "Brief explanation of the judgment basis"
}}

Important Notes:
1. is_genome_editing determination: Only papers that explicitly mention genome editing of UTR or uORF (such as CRISPR, TALEN, ZFN, etc.) should be judged as true
2. phenotype_description field:
   - If genome editing is involved: Extract phenotypic changes after editing from the abstract, including but not limited to:
     * Morphological trait changes (e.g., plant height, leaf morphology, root development, etc.)
     * Physiological and biochemical properties (e.g., protein expression, metabolic changes, etc.)
     * Agronomic traits (e.g., yield, quality, growth rate, etc.)
     * Resistance changes (e.g., disease resistance, insect resistance, stress tolerance, etc.)
   - If not involved in editing: Fill in "No genome editing involved"
3. abstract_chinese field: Please accurately translate the English abstract into fluent Chinese, maintaining the accuracy of scientific terminology
4. plant_species field: Please provide plant species names in Chinese (e.g., "拟南芥", "水稻", "小麦")
5. If the abstract information is insufficient, set confidence to a lower value

Please return the analysis results directly in JSON format without any other text description.
"""

    # Create prompt template and chain
    prompt = ChatPromptTemplate.from_template(custom_prompt_template)
    json_parser = JsonOutputParser()
    analysis_chain = prompt | llm | json_parser

    # ==================== Load cached analysis results ====================
    logger.info(f"Loading cached analysis results from: {llm_analysis_cache_file}")
    cached_results = load_analysis_cache(llm_analysis_cache_file)
    logger.info(f"Found {len(cached_results)} cached analysis results")

    # ==================== Batch analyze papers with async and caching ====================
    logger.info(f"Starting analysis of {len(papers)} papers...")
    analysis_results = []
    papers_to_analyze = []

    # Separate cached and uncached papers
    for paper in papers:
        pmid = paper.get("pmid", "")
        if pmid in cached_results:
            logger.info(f"Using cached result for PMID: {pmid}")
            analysis_results.append(cached_results[pmid])
        else:
            papers_to_analyze.append(paper)

    logger.info(
        f"Papers status: {len(analysis_results)} cached, "
        f"{len(papers_to_analyze)} to analyze"
    )

    # Async batch processing with concurrency control
    if papers_to_analyze:
        # Process in batches to control concurrency and save progress
        batch_size = 20  # Process 10 papers at a time
        max_concurrent = 20  # Maximum 3 concurrent requests

        # Track timing for ETA calculation
        total_batches = (len(papers_to_analyze) + batch_size - 1) // batch_size
        batch_start_time = time.time()
        completed_batches = 0

        for batch_start in range(0, len(papers_to_analyze), batch_size):
            batch_end = min(batch_start + batch_size, len(papers_to_analyze))
            batch = papers_to_analyze[batch_start:batch_end]

            logger.info(
                f"\nProcessing batch {batch_start // batch_size + 1}/"
                f"{(len(papers_to_analyze) + batch_size - 1) // batch_size}: "
                f"papers {batch_start + 1}-{batch_end}/{len(papers_to_analyze)}"
            )

            # Create semaphore for concurrency control
            semaphore = asyncio.Semaphore(max_concurrent)

            async def analyze_with_semaphore(paper: dict[str, Any]) -> dict[str, Any]:
                async with semaphore:
                    logger.info(
                        f"  Analyzing: {paper.get('title', 'N/A')[:60]}... "
                        f"(PMID: {paper.get('pmid', 'N/A')})"
                    )
                    result = await analyze_paper_with_retry(analysis_chain, paper)
                    return result

            # Process batch concurrently
            batch_results = await asyncio.gather(
                *[analyze_with_semaphore(paper) for paper in batch],
                return_exceptions=True,
            )

            # Handle results and exceptions
            for i, result in enumerate(batch_results):
                if isinstance(result, Exception):
                    logger.error(f"Unexpected error for paper {i}: {result}")
                    # Create error result
                    paper = batch[i]
                    import re

                    pubdate = paper.get("pubdate", "")
                    year = ""
                    if pubdate:
                        year_match = re.search(r"\b(\d{4})\b", pubdate)
                        if year_match:
                            year = year_match.group(1)

                    error_result = {
                        "pmid": paper.get("pmid", ""),
                        "title": paper.get("title", ""),
                        "abstract": paper.get("abstract", ""),
                        "journal": paper.get("journal", ""),
                        "year": year,
                        "doi": paper.get("doi", ""),
                        "authors": "; ".join(paper.get("authors", [])),
                        "is_genome_editing": False,
                        "editing_targets": [],
                        "editing_methods": [],
                        "plant_species": [],
                        "phenotype_description": "Analysis error",
                        "abstract_chinese": "Translation failed",
                        "confidence": 0.0,
                        "reasoning": f"Unexpected error: {str(result)}",
                    }
                    analysis_results.append(error_result)
                else:
                    analysis_results.append(result)

            # Save cache after each batch
            logger.info("Saving progress to cache...")
            save_analysis_cache(llm_analysis_cache_file, analysis_results)

            # Update timing statistics and calculate ETA
            completed_batches += 1
            elapsed_time = time.time() - batch_start_time
            avg_time_per_batch = elapsed_time / completed_batches
            remaining_batches = total_batches - completed_batches
            eta_seconds = avg_time_per_batch * remaining_batches

            # Format ETA
            eta_minutes = int(eta_seconds // 60)
            eta_hours = eta_minutes // 60
            eta_minutes_remainder = eta_minutes % 60

            # Progress update with ETA
            total_analyzed = len(analysis_results)
            progress_pct = total_analyzed / len(papers) * 100

            if eta_hours > 0:
                eta_str = f"{eta_hours}h {eta_minutes_remainder}m"
            elif eta_minutes > 0:
                eta_str = f"{eta_minutes}m {int(eta_seconds % 60)}s"
            else:
                eta_str = f"{int(eta_seconds)}s"

            logger.info(
                f"Progress: {total_analyzed}/{len(papers)} ({progress_pct:.1f}%) | "
                f"Avg: {avg_time_per_batch:.1f}s/batch | "
                f"ETA: {eta_str}"
            )

            # Brief pause between batches
            if batch_end < len(papers_to_analyze):
                await asyncio.sleep(1)

    logger.info(f"\nAnalysis completed: processed {len(analysis_results)} papers")

    # ==================== 步骤 5: 导出分析结果 ====================
    logger.info("\n" + "=" * 80)
    logger.info("步骤 5: 导出分析结果")
    logger.info("=" * 80)

    # Export JSON format (complete analysis results)
    with open(analysis_json_file, "w", encoding="utf-8") as f:
        json.dump(analysis_results, f, ensure_ascii=False, indent=2)
    logger.info(f"Complete analysis results exported to JSON: {analysis_json_file}")

    # 导出最终结果 CSV 格式（用户要求的字段）
    final_csv_fields = [
        "pmid",
        "title",
        "abstract",
        "journal",
        "year",
        "doi",
        "abstract_chinese",
        "phenotype_description",
    ]

    final_csv_file = output_dir / "pubmed_uorf_final_results.csv"

    with open(final_csv_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=final_csv_fields)
        writer.writeheader()

        for result in analysis_results:
            row = {
                "pmid": result.get("pmid", ""),
                "title": result.get("title", ""),
                "abstract": result.get("abstract", ""),
                "journal": result.get("journal", ""),
                "year": result.get("year", ""),
                "doi": result.get("doi", ""),
                "abstract_chinese": result.get("abstract_chinese", ""),
                "phenotype_description": result.get(
                    "phenotype_description", "不涉及基因组编辑"
                ),
            }
            writer.writerow(row)

    logger.info(f"最终结果已导出到 CSV: {final_csv_file}")

    # 导出符合要求的论文（仅包含涉及基因组编辑的论文）
    editing_papers = [
        result for result in analysis_results if result.get("is_genome_editing", False)
    ]

    logger.info(f"\n筛选出 {len(editing_papers)} 篇涉及 UTR/uORF 基因组编辑的论文")

    if editing_papers:
        with open(editing_papers_csv_file, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=final_csv_fields)
            writer.writeheader()

            for result in editing_papers:
                row = {
                    "pmid": result.get("pmid", ""),
                    "title": result.get("title", ""),
                    "abstract": result.get("abstract", ""),
                    "journal": result.get("journal", ""),
                    "year": result.get("year", ""),
                    "doi": result.get("doi", ""),
                    "abstract_chinese": result.get("abstract_chinese", ""),
                    "phenotype_description": result.get(
                        "phenotype_description", "不涉及基因组编辑"
                    ),
                }
                writer.writerow(row)

        logger.info(f"符合要求的论文已单独导出到: {editing_papers_csv_file}")
    else:
        logger.warning("未找到涉及 UTR/uORF 基因组编辑的论文")

    # 导出详细分析结果 CSV（包含所有分析字段，用于进一步分析）
    detailed_csv_fields = [
        "pmid",
        "title",
        "journal",
        "year",
        "doi",
        "authors",
        "is_genome_editing",
        "editing_targets",
        "editing_methods",
        "plant_species",
        "phenotype_description",
        "confidence",
        "reasoning",
    ]

    detailed_csv_file = output_dir / "uorf_genome_editing_detailed_analysis.csv"

    with open(detailed_csv_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=detailed_csv_fields)
        writer.writeheader()

        for result in analysis_results:
            row = {
                "pmid": result.get("pmid", ""),
                "title": result.get("title", ""),
                "journal": result.get("journal", ""),
                "year": result.get("year", ""),
                "doi": result.get("doi", ""),
                "authors": result.get("authors", ""),
                "is_genome_editing": result.get("is_genome_editing", False),
                "editing_targets": "; ".join(result.get("editing_targets", [])),
                "editing_methods": "; ".join(result.get("editing_methods", [])),
                "plant_species": "; ".join(result.get("plant_species", [])),
                "phenotype_description": result.get(
                    "phenotype_description", "不涉及基因组编辑"
                ),
                "confidence": result.get("confidence", 0.0),
                "reasoning": result.get("reasoning", ""),
            }
            writer.writerow(row)

    logger.info(f"详细分析结果已导出到 CSV: {detailed_csv_file}")

    # ==================== 统计信息 ====================
    logger.info("\n" + "=" * 80)
    logger.info("分析统计")
    logger.info("=" * 80)

    # 统计涉及基因组编辑的论文数量
    genome_editing_count = sum(
        1 for result in analysis_results if result.get("is_genome_editing", False)
    )

    logger.info(f"总论文数: {len(analysis_results)}")
    logger.info(f"涉及 UTR/uORF 基因组编辑的论文: {genome_editing_count}")
    logger.info(
        f"比例: {genome_editing_count / len(analysis_results) * 100:.1f}%"
        if analysis_results
        else "0%"
    )

    # 统计编辑方法
    editing_methods_counter: dict[str, int] = {}
    for result in analysis_results:
        if result.get("is_genome_editing", False):
            for method in result.get("editing_methods", []):
                editing_methods_counter[method] = (
                    editing_methods_counter.get(method, 0) + 1
                )

    if editing_methods_counter:
        logger.info("\n【使用的基因组编辑技术】")
        for method, count in sorted(
            editing_methods_counter.items(), key=lambda x: x[1], reverse=True
        ):
            logger.info(f"  {method}: {count} 篇")

    logger.info("\n" + "=" * 80)
    logger.info("处理完成！")
    logger.info("=" * 80)
    logger.info("\n输出文件：")
    logger.info(f"  1. 论文原始数据: {csv_file}")
    logger.info(f"  2. 所有论文分析结果 CSV: {final_csv_file}")
    logger.info(f"  3. 符合要求的论文 CSV (仅基因组编辑): {editing_papers_csv_file}")
    logger.info(f"  4. 详细分析结果 CSV: {detailed_csv_file}")
    logger.info(f"  5. 完整分析结果 JSON: {analysis_json_file}")
    logger.info(f"  6. LLM 分析缓存: {llm_analysis_cache_file}")


if __name__ == "__main__":
    asyncio.run(main())
