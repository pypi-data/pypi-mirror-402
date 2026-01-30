"""
文本处理工具函数模块
提供文本处理、清理和分析的实用工具函数。
"""

import logging
import re
import string


logger = logging.getLogger(__name__)


def clean_text(
    text: str,
    remove_punctuation: bool = False,
    remove_numbers: bool = False,
    remove_extra_spaces: bool = True,
) -> str:
    """
    清理文本内容
    Args:
        text: 原始文本
        remove_punctuation: 是否移除标点符号
        remove_numbers: 是否移除数字
        remove_extra_spaces: 是否移除多余空格
    Returns:
        清理后的文本
    """
    if not text:
        return ""
    # 移除多余空格
    if remove_extra_spaces:
        text = re.sub(r"\s+", " ", text.strip())
    # 移除标点符号
    if remove_punctuation:
        # 包括中文标点符号
        punctuation = string.punctuation + '，。！？；：""（）【】《》'
        text = text.translate(str.maketrans("", "", punctuation))
    # 移除数字
    if remove_numbers:
        text = re.sub(r"\d+", "", text)
    return text


def extract_sentences(text: str) -> list[str]:
    """
    提取文本中的句子
    Args:
        text: 输入文本
    Returns:
        句子列表
    """
    # 简单的句子分割，基于句号、问号、感叹号（包括中文标点）
    sentences = re.split(r"[.!?。！？]+", text)
    # 清理和过滤
    cleaned_sentences = []
    for sentence in sentences:
        sentence = sentence.strip()
        if sentence and len(sentence) > 5:  # 过滤太短的句子
            cleaned_sentences.append(sentence)
    return cleaned_sentences


def extract_paragraphs(text: str) -> list[str]:
    """
    提取文本中的段落
    Args:
        text: 输入文本
    Returns:
        段落列表
    """
    # 按双换行符分割段落
    paragraphs = text.split("\n\n")
    # 清理段落
    cleaned_paragraphs = []
    for paragraph in paragraphs:
        paragraph = paragraph.strip()
        if paragraph and len(paragraph) > 20:  # 过滤太短的段落
            cleaned_paragraphs.append(paragraph)
    return cleaned_paragraphs


def extract_keywords(
    text: str, min_length: int = 3, max_length: int = 20, min_frequency: int = 2
) -> list[tuple[str, int]]:
    """
    提取文本中的关键词
    Args:
        text: 输入文本
        min_length: 关键词最小长度
        max_length: 关键词最大长度
        min_frequency: 最小出现频率
    Returns:
        关键词列表，每个元素为(关键词, 频率)
    """
    # 清理文本
    cleaned_text = clean_text(text, remove_punctuation=True, remove_numbers=True)
    # 转换为小写并分割单词
    words = cleaned_text.lower().split()
    # 过滤单词
    filtered_words = []
    for word in words:
        if min_length <= len(word) <= max_length and word.isalpha():
            filtered_words.append(word)
    # 检查是否主要是中文文本
    chinese_chars = [char for char in cleaned_text if "\u4e00" <= char <= "\u9fff"]
    if len(chinese_chars) > len(cleaned_text) * 0.5:  # 如果中文字符超过50%
        # 中文分词：按字符分割
        # 尝试双字符组合
        for i in range(len(chinese_chars) - 1):
            word = chinese_chars[i] + chinese_chars[i + 1]
            if len(word) >= min_length and len(word) <= max_length:
                filtered_words.append(word)
        # 如果还是没有找到，尝试单个字符
        if not filtered_words:
            for char in chinese_chars:
                if min_length <= len(char) <= max_length:
                    filtered_words.append(char)
    # 统计频率
    word_freq: dict[str, int] = {}
    for word in filtered_words:
        word_freq[word] = word_freq.get(word, 0) + 1
    # 过滤低频词并排序
    keywords = [
        (word, freq) for word, freq in word_freq.items() if freq >= min_frequency
    ]
    keywords.sort(key=lambda x: x[1], reverse=True)
    return keywords


def extract_entities(text: str) -> dict[str, list[str]]:
    """
    提取文本中的实体（简单实现）
    Args:
        text: 输入文本
    Returns:
        实体字典，包含不同类型的实体
    """
    entities: dict[str, list[str]] = {
        "emails": [],
        "urls": [],
        "phone_numbers": [],
        "dates": [],
        "numbers": [],
    }
    # 提取邮箱
    email_pattern = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"
    entities["emails"] = re.findall(email_pattern, text)
    # 提取URL
    url_pattern = r"http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+"
    entities["urls"] = re.findall(url_pattern, text)
    # 提取电话号码
    phone_pattern = r"(\+?1?[-.\s]?)?\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})"
    entities["phone_numbers"] = re.findall(phone_pattern, text)
    # 提取日期
    date_pattern = r"\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b"
    entities["dates"] = re.findall(date_pattern, text)
    # 提取数字
    number_pattern = r"\b\d+(?:\.\d+)?\b"
    entities["numbers"] = re.findall(number_pattern, text)
    return entities


def calculate_readability_score(text: str) -> dict[str, float]:
    """
    计算文本可读性分数
    Args:
        text: 输入文本
    Returns:
        可读性分数字典
    """
    sentences = extract_sentences(text)
    words = clean_text(text, remove_punctuation=True).split()
    if not sentences or not words:
        return {"flesch_reading_ease": 0, "flesch_kincaid_grade": 0}
    # 计算音节数（简化版本）
    syllables = 0
    for word in words:
        syllables += count_syllables(word)
    # Flesch Reading Ease
    avg_sentence_length = len(words) / len(sentences)
    avg_syllables_per_word = syllables / len(words)
    flesch_score = (
        206.835 - (1.015 * avg_sentence_length) - (84.6 * avg_syllables_per_word)
    )
    # Flesch-Kincaid Grade Level
    fk_grade = (0.39 * avg_sentence_length) + (11.8 * avg_syllables_per_word) - 15.59
    return {
        "flesch_reading_ease": round(flesch_score, 2),
        "flesch_kincaid_grade": round(fk_grade, 2),
    }


def count_syllables(word: str) -> int:
    """
    计算单词的音节数（简化版本）
    Args:
        word: 单词
    Returns:
        音节数
    """
    word = word.lower()
    vowels = "aeiouy"
    syllable_count = 0
    prev_was_vowel = False
    for char in word:
        if char in vowels:
            if not prev_was_vowel:
                syllable_count += 1
            prev_was_vowel = True
        else:
            prev_was_vowel = False
    # 处理以e结尾的单词
    if word.endswith("e") and syllable_count > 1:
        syllable_count -= 1
    # 至少有一个音节
    return max(1, syllable_count)


def remove_stopwords(text: str, custom_stopwords: set[str] | None = None) -> str:
    """
    移除停用词
    Args:
        text: 输入文本
        custom_stopwords: 自定义停用词集合
    Returns:
        移除停用词后的文本
    """
    # 默认停用词
    default_stopwords = {
        "a",
        "an",
        "and",
        "are",
        "as",
        "at",
        "be",
        "by",
        "for",
        "from",
        "has",
        "he",
        "in",
        "is",
        "it",
        "its",
        "of",
        "on",
        "that",
        "the",
        "to",
        "was",
        "will",
        "with",
        "this",
        "but",
        "they",
        "have",
        "had",
        "what",
        "said",
        "each",
        "which",
        "their",
        "time",
        "if",
        "up",
        "out",
        "many",
        "then",
        "them",
        "can",
        "only",
        "other",
        "new",
        "some",
        "could",
        "these",
        "may",
        "say",
        "use",
        "her",
        "than",
        "first",
        "been",
        "call",
        "who",
        "oil",
        "sit",
        "now",
        "find",
        "long",
        "down",
        "day",
        "did",
        "get",
        "come",
        "made",
        "part",
    }
    if custom_stopwords:
        stopwords = default_stopwords.union(custom_stopwords)
    else:
        stopwords = default_stopwords
    words = text.split()
    filtered_words = [word for word in words if word.lower() not in stopwords]
    return " ".join(filtered_words)


def extract_ngrams(text: str, n: int = 2) -> list[str]:
    """
    提取n-gram
    Args:
        text: 输入文本
        n: n-gram的大小
    Returns:
        n-gram列表
    """
    cleaned_text = clean_text(text, remove_punctuation=True)
    words = cleaned_text.split()
    ngrams = []
    # 检查是否主要是中文文本
    chinese_chars = [char for char in cleaned_text if "\u4e00" <= char <= "\u9fff"]
    if len(chinese_chars) > len(cleaned_text) * 0.5:  # 如果中文字符超过50%
        # 中文n-gram
        if len(chinese_chars) >= n:
            for i in range(len(chinese_chars) - n + 1):
                ngram = "".join(chinese_chars[i : i + n])
                ngrams.append(ngram)
    else:
        # 英文n-gram
        if len(words) >= n:
            for i in range(len(words) - n + 1):
                ngram = " ".join(words[i : i + n])
                ngrams.append(ngram)
    return ngrams


def calculate_text_similarity(text1: str, text2: str) -> float:
    """
    计算两个文本的相似度（基于Jaccard相似度）
    Args:
        text1: 第一个文本
        text2: 第二个文本
    Returns:
        相似度分数（0-1之间）
    """
    # 清理文本并转换为词集合
    words1 = set(clean_text(text1, remove_punctuation=True).lower().split())
    words2 = set(clean_text(text2, remove_punctuation=True).lower().split())
    if not words1 and not words2:
        return 1.0
    if not words1 or not words2:
        return 0.0
    # 计算Jaccard相似度
    intersection = words1.intersection(words2)
    union = words1.union(words2)
    return len(intersection) / len(union)


def summarize_text(text: str, max_sentences: int = 3) -> str:
    """
    简单的文本摘要（基于句子长度和关键词）
    Args:
        text: 输入文本
        max_sentences: 最大句子数
    Returns:
        摘要文本
    """
    sentences = extract_sentences(text)
    if len(sentences) <= max_sentences:
        return text
    # 提取关键词
    keywords = extract_keywords(text, min_frequency=1)
    keyword_set = {kw[0] for kw in keywords[:10]}  # 取前10个关键词
    # 为每个句子评分
    sentence_scores = []
    for sentence in sentences:
        score = 0
        sentence_words = set(
            clean_text(sentence, remove_punctuation=True).lower().split()
        )
        # 基于关键词的分数
        keyword_matches = len(sentence_words.intersection(keyword_set))
        score += keyword_matches * 2
        # 基于句子长度的分数（中等长度的句子得分更高）
        length = len(sentence_words)
        if 10 <= length <= 30:
            score += 1
        sentence_scores.append((sentence, score))
    # 按分数排序并选择前几个句子
    sentence_scores.sort(key=lambda x: x[1], reverse=True)
    selected_sentences = [sent[0] for sent in sentence_scores[:max_sentences]]
    return ". ".join(selected_sentences) + "."


def get_document_stats(text: str) -> dict[str, int]:
    """
    获取文档统计信息
    Args:
        text: 输入文本
    Returns:
        包含统计信息的字典
    """
    if not text:
        return {
            "total_lines": 0,
            "characters": 0,
            "words": 0,
            "sentences": 0,
            "paragraphs": 0,
        }
    # 基本统计
    lines = text.split("\n")
    total_lines = len(lines)
    non_empty_lines = len([line for line in lines if line.strip()])
    # 字符统计
    characters = len(text)
    characters_no_spaces = len(
        text.replace(" ", "").replace("\n", "").replace("\t", "")
    )
    # 单词统计
    words = clean_text(text, remove_punctuation=True).split()
    word_count = len(words)
    # 句子统计
    sentences = extract_sentences(text)
    sentence_count = len(sentences)
    # 段落统计
    paragraphs = extract_paragraphs(text)
    paragraph_count = len(paragraphs)
    return {
        "total_lines": total_lines,
        "non_empty_lines": non_empty_lines,
        "characters": characters,
        "characters_no_spaces": characters_no_spaces,
        "words": word_count,
        "sentences": sentence_count,
        "paragraphs": paragraph_count,
    }
