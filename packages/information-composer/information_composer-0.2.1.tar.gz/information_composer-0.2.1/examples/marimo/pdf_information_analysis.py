import marimo


__generated_with = "0.17.7"
app = marimo.App(width="medium")


@app.cell
def _():
    import json
    import os
    from pathlib import Path

    from langchain_community.document_loaders import PyPDFLoader
    from langchain_openai import ChatOpenAI
    import marimo as mo
    import polars as pl

    # 从环境变量读取配置
    openai_base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
    openai_api_key = os.getenv("OPENAI_API_KEY", "")

    # 文件浏览器 - 支持多选
    file_browser = mo.ui.file_browser(
        initial_path="/Users/forrest/Downloads/uORF文章汇总/",
        multiple=True,  # 支持多文件选择
        filetypes=[".pdf"],
    )

    mo.md(f"""
    ## 📚 批量 PDF 文档分析工具

    选择多个 PDF 文件进行批量分析：

    {file_browser}

    """)
    return (
        ChatOpenAI,
        PyPDFLoader,
        file_browser,
        json,
        mo,
        openai_api_key,
        openai_base_url,
        pl,
    )


@app.cell
def _(file_browser, mo):
    if file_browser.value and len(file_browser.value) > 0:
        file_list = "\n".join([f"- `{f.name}`" for f in file_browser.value])
        mo.md(f"""
        ### ✅ 已选择的 PDF 文件:

        {file_list}
        """)
    else:
        mo.md("📂 请选择至少一个 PDF 文件")
    return


@app.cell
def _():
    question = "这篇论文是否与 uORF 相关, 如果是请给出 uORF 所在基因， uORF 突变的表型信息，物种信息"
    return (question,)


@app.cell
def _(ChatOpenAI, PyPDFLoader, json, openai_api_key, openai_base_url):
    import asyncio
    # from langchain_openai import ChatOpenAI

    # 异步处理单个 PDF 的函数（带进度）
    async def process_single_pdf_with_progress(
        pdf_file, question, llm, semaphore, progress_list
    ):
        """异步处理单个 PDF 文件，并更新进度"""
        filename = pdf_file.name
        print(filename)
        async with semaphore:
            try:
                loop = asyncio.get_event_loop()

                def load_pdf():
                    loader = PyPDFLoader(str(pdf_file.path))
                    docs = loader.load()
                    return "\n\n".join([doc.page_content for doc in docs])

                pdf_text = await loop.run_in_executor(None, load_pdf)

                max_chars = 80000
                truncated_text = pdf_text[:max_chars]
                if len(pdf_text) > max_chars:
                    truncated_text += "\n\n... (文本已截断)"

                prompt = f"""你是一个专业的文档分析助手。请根据提供的 PDF 内容回答用户的问题。如果内容中没有相关信息，请明确说明。

    PDF 内容：
    {truncated_text}

    用户问题：{question}

    请基于上述 PDF 内容用 JSON 格式回答问题，
    例如：
    {{
    "是否与uORF有关": "是",
    "物种": "水稻",
    "基因名": "Waxy",
    "uORF突变表型": "直链淀粉含量增多"
    }}

    如果不相关，请返回：
    {{
    "是否与uORF有关": "否",
    "物种": "",
    "基因名": "",
    "uORF突变表型": ""
    }}
    """

                response = await llm.ainvoke(prompt)
                answer = response.content

                try:
                    json_start = answer.find("{")
                    json_end = answer.rfind("}") + 1
                    if json_start >= 0 and json_end > json_start:
                        json_str = answer[json_start:json_end]
                        parsed_result = json.loads(json_str)
                    else:
                        parsed_result = {"错误": "无法解析 JSON"}
                except json.JSONDecodeError:
                    parsed_result = {"错误": "JSON 解析失败", "原始回答": answer}

                result_entry = {"文件名": filename, **parsed_result}

                # 更新进度
                progress_list.append(filename)

                return result_entry

            except Exception as e:
                progress_list.append(f"❌ {filename}")
                return {"文件名": filename, "错误": str(e)}

    async def batch_process_pdfs_with_progress(pdf_files, question, max_concurrent=5):
        """批量异步处理，带进度追踪"""
        # openai_base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
        # openai_api_key = os.getenv("OPENAI_API_KEY", "")

        llm = ChatOpenAI(
            base_url=openai_base_url,
            api_key=openai_api_key,
            model="anthropic/claude-sonnet-4.5",
            temperature=0.3,
        )

        semaphore = asyncio.Semaphore(max_concurrent)
        progress_list = []

        tasks = [
            process_single_pdf_with_progress(
                pdf_file, question, llm, semaphore, progress_list
            )
            for pdf_file in pdf_files
        ]

        results = await asyncio.gather(*tasks)

        return results

    # 执行批量分析
    # results = []

    # if not start_analysis_button.value:
    #     mo.md("💡 提示：设置好问题后，点击'🚀 开始批量分析'按钮")
    # elif not file_browser.value:
    #     mo.md("⚠️ 请先选择 PDF 文件")
    # elif not analysis_question.value:
    #     mo.md("⚠️ 请输入分析问题")
    # else:
    # with mo.status.spinner(title=f"🤔 正在异步分析 {len(file_browser.value)} 个文件..."):

    return (batch_process_pdfs_with_progress,)


@app.cell
async def _(batch_process_pdfs_with_progress, file_browser, question):
    results = await batch_process_pdfs_with_progress(
        file_browser.value, question, max_concurrent=5
    )
    return (results,)


@app.cell
def _(mo, pl, results):
    # 展示结果表格
    df_results = None
    if results:
        df_results = pl.DataFrame(results)

        mo.vstack(
            [
                mo.md("### 📈 分析结果表格"),
                mo.ui.table(df_results),
            ]
        )
    else:
        mo.md("")
    return (df_results,)


@app.cell
def _(df_results):
    df_results
    return


@app.cell
def _(df_results, mo):
    # 导出功能
    try:
        if df_results is not None and len(df_results) > 0:
            export_button = mo.ui.button(label="📥 导出为 CSV")

            mo.vstack(
                [
                    mo.md("### 💾 导出数据"),
                    export_button,
                ]
            )

            if export_button.value:
                try:
                    # 保存 CSV
                    output_path = "pdf_analysis_results.csv"
                    df_results.write_csv(output_path)

                    mo.md(f"""
                    ✅ **导出成功！**

                    文件已保存至: `{output_path}`

                    你可以在文件系统中找到这个 CSV 文件。
                    """)
                except Exception as e:
                    mo.md(f"❌ 导出失败: {str(e)}")
        else:
            mo.md("")
    except:
        mo.md("")
    return


if __name__ == "__main__":
    app.run()
