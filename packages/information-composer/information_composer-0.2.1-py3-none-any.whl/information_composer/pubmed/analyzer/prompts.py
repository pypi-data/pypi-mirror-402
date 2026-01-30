"""
提示词模板管理
管理不同分析任务的提示词模板。
"""

from langchain_core.prompts import ChatPromptTemplate


class PromptManager:
    """提示词模板管理器"""

    @staticmethod
    def get_summary_prompt() -> ChatPromptTemplate:
        """
        获取论文总结提示词模板
        Returns:
            论文总结的 ChatPromptTemplate
        """
        system_message = """你是一位专业的科学文献分析助手。你的任务是阅读论文的标题和摘要，提取关键信息并生成结构化总结。
请严格按照以下 JSON 格式返回结果：
{{
    "main_findings": ["发现1", "发现2", ...],  // 1-5项主要研究发现
    "innovations": ["创新点1", "创新点2", ...],  // 1-3项创新点
    "conclusions": "核心结论的简洁描述"  // 一句话总结核心结论
}}
注意：
1. main_findings 应提取论文最重要的研究发现，每项用一句话清晰描述
2. innovations 应识别论文相对于现有研究的突破和创新之处
3. conclusions 应概括论文的核心结论和意义
4. 所有内容应简洁准确，避免冗余"""
        user_message = """请分析以下论文：
标题: {title}
摘要: {abstract}
请按照要求的 JSON 格式返回分析结果。"""
        return ChatPromptTemplate.from_messages(
            [("system", system_message), ("human", user_message)]
        )

    @staticmethod
    def get_domain_prompt() -> ChatPromptTemplate:
        """
        获取领域判定提示词模板
        Returns:
            领域判定的 ChatPromptTemplate
        """
        system_message = """你是一位专业的科学文献领域分类专家。你的任务是判断论文是否属于指定的研究领域，并给出相关性评分。
请严格按照以下 JSON 格式返回结果：
{{
    "relevant_domains": ["领域1", "领域2"],  // 相关的领域列表
    "domain_scores": {{
        "领域1": 0.9,  // 0-1之间的相关性评分
        "领域2": 0.7
    }},
    "primary_domain": "主要领域名称",  // 最相关的领域
    "reasoning": "判定依据的简要说明"  // 解释为什么判定为这些领域
}}
评分标准：
- 0.8-1.0: 核心研究领域，论文主要关注该领域
- 0.5-0.8: 相关领域，论文涉及该领域的方法或应用
- 0.0-0.5: 弱相关或不相关
注意：
1. 只返回评分 >= 0.5 的领域到 relevant_domains
2. primary_domain 必须是 relevant_domains 中评分最高的领域
3. reasoning 应基于标题、摘要中的具体内容"""
        user_message = """请判断以下论文是否属于指定的研究领域：
标题: {title}
摘要: {abstract}
候选领域: {domains}
请按照要求的 JSON 格式返回领域判定结果。"""
        return ChatPromptTemplate.from_messages(
            [("system", system_message), ("human", user_message)]
        )

    @staticmethod
    def format_summary_prompt(title: str, abstract: str) -> dict[str, str]:
        """
        格式化论文总结提示词
        Args:
            title: 论文标题
            abstract: 论文摘要
        Returns:
            格式化后的提示词参数
        """
        return {"title": title, "abstract": abstract}

    @staticmethod
    def format_domain_prompt(
        title: str, abstract: str, domains: list[str]
    ) -> dict[str, str]:
        """
        格式化领域判定提示词
        Args:
            title: 论文标题
            abstract: 论文摘要
            domains: 候选领域列表
        Returns:
            格式化后的提示词参数
        """
        domains_str = ", ".join(domains)
        return {"title": title, "abstract": abstract, "domains": domains_str}


# 示例和测试用的简化提示词
SUMMARY_EXAMPLE_INPUT = {
    "title": "CRISPR-Cas9 mediated genome editing in rice",
    "abstract": "We developed a highly efficient CRISPR-Cas9 system for targeted mutagenesis in rice. The system achieved 95% editing efficiency and can be used for multiplex gene editing. This technology enables rapid functional genomics studies in rice.",
}
SUMMARY_EXAMPLE_OUTPUT = {
    "main_findings": [
        "Developed a highly efficient CRISPR-Cas9 system for rice with 95% editing efficiency",
        "System supports multiplex gene editing capabilities",
        "Enables rapid functional genomics studies",
    ],
    "innovations": [
        "Achieved significantly higher editing efficiency than previous systems",
        "First demonstration of efficient multiplex editing in rice",
    ],
    "conclusions": "The CRISPR-Cas9 system provides a powerful tool for rice functional genomics and crop improvement",
}
DOMAIN_EXAMPLE_INPUT = {
    "title": "Epigenetic regulation of flowering time in Arabidopsis",
    "abstract": "We investigated the role of histone modifications in flowering time control. Our results show that H3K27me3 marks are dynamically regulated during vernalization and play a key role in FLC repression.",
    "domains": ["Epigenetics", "Plant Development", "Cancer Research"],
}
DOMAIN_EXAMPLE_OUTPUT = {
    "relevant_domains": ["Epigenetics", "Plant Development"],
    "domain_scores": {
        "Epigenetics": 0.95,
        "Plant Development": 0.85,
        "Cancer Research": 0.1,
    },
    "primary_domain": "Epigenetics",
    "reasoning": "The paper focuses on histone modifications (H3K27me3) which is a core epigenetic mechanism. It studies flowering time control which is a plant development topic. No relevance to cancer research.",
}
