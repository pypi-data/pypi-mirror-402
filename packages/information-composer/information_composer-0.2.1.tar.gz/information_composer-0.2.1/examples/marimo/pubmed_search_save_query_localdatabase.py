import marimo


__generated_with = "0.17.7"
app = marimo.App()


@app.cell
def _():
    import marimo as mo

    return


@app.cell
def _():
    from pathlib import Path

    from information_composer.pubmed.database import PubMedDatabase

    db_path = Path(".pubmed_marimo.db")
    db_path.parent.mkdir(parents=True, exist_ok=True)

    db = PubMedDatabase(str(db_path))
    return


@app.cell
def _():
    from information_composer.pubmed.pubmed import query_pmid

    return (query_pmid,)


@app.cell
def _(query_pmid):
    query = "(uORFs OR uORF) and (plant)"
    pmids = query_pmid(email="hello@example.com", query=query)
    return (pmids,)


@app.cell
def _(pmids):
    print(pmids[:5])
    return


@app.cell
def _():
    from information_composer.pubmed.pubmed import fetch_pubmed_details_batch

    return (fetch_pubmed_details_batch,)


@app.cell
async def _(fetch_pubmed_details_batch, pmids):
    records = await fetch_pubmed_details_batch(pmids)
    return (records,)


@app.cell
async def _(records):
    import asyncio
    import os

    from langchain_core.messages import HumanMessage
    from langchain_openai import ChatOpenAI

    # 从环境变量读取配置
    openai_base_url = os.getenv("OPENAI_BASE_URL")
    openai_api_key = os.getenv("OPENAI_API_KEY")

    # 初始化 ChatOpenAI
    llm = ChatOpenAI(
        base_url=openai_base_url,
        api_key=openai_api_key,
        model="anthropic/claude-sonnet-4.5",
    )

    # 异步翻译单个摘要
    async def translate_abstract(record):
        if record.get("abstract"):
            message = HumanMessage(
                content=f"请将以下英文摘要翻译成中文:\n\n{record['abstract']}"
            )
            response = await llm.ainvoke([message])
            record["abstract_zh"] = response.content
        else:
            record["abstract_zh"] = ""
        return record

    # 异步翻译所有摘要
    async def translate_all():
        tasks = [translate_abstract(record) for record in records]
        return await asyncio.gather(*tasks)

    _translated_records = await translate_all()

    # 更新原始 records 列表
    for i, translated in enumerate(_translated_records):
        records[i] = translated

    _translated_records[:2]
    return


@app.cell
def _():
    import pandas as pd

    return (pd,)


@app.cell
def _(pd, records):
    df = pd.DataFrame(records)
    return (df,)


@app.cell
def _(df):
    df
    return


@app.cell
def _():
    return


if __name__ == "__main__":
    app.run()
