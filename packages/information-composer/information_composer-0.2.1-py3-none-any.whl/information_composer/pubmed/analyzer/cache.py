"""
缓存机制
基于文件的分析结果缓存，提升重复分析的效率。
"""

from datetime import datetime, timedelta
import hashlib
import json
import logging
from pathlib import Path
from typing import Any


logger = logging.getLogger(__name__)


class AnalysisCache:
    """分析结果缓存管理器"""

    def __init__(
        self,
        cache_dir: str = "./pubmed_analysis_cache",
        expire_days: int = 30,
        enabled: bool = True,
    ):
        """
        初始化缓存管理器
        Args:
            cache_dir: 缓存目录路径
            expire_days: 缓存过期天数
            enabled: 是否启用缓存
        """
        self.cache_dir = Path(cache_dir)
        self.expire_days = expire_days
        self.enabled = enabled
        if self.enabled:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"缓存已启用，缓存目录: {self.cache_dir}")

    def _generate_cache_key(self, pmid: str, analysis_config: dict[str, Any]) -> str:
        """
        生成缓存键
        Args:
            pmid: PubMed ID
            analysis_config: 分析配置
        Returns:
            缓存键（哈希值）
        """
        # 将配置转换为稳定的字符串表示
        config_str = json.dumps(analysis_config, sort_keys=True)
        cache_str = f"{pmid}_{config_str}"
        # 生成 MD5 哈希
        return hashlib.md5(cache_str.encode()).hexdigest()

    def _get_cache_file_path(self, cache_key: str) -> Path:
        """
        获取缓存文件路径
        Args:
            cache_key: 缓存键
        Returns:
            缓存文件路径
        """
        # 使用哈希的前两个字符作为子目录，避免单个目录文件过多
        subdir = cache_key[:2]
        cache_subdir = self.cache_dir / subdir
        cache_subdir.mkdir(parents=True, exist_ok=True)
        return cache_subdir / f"{cache_key}.json"

    def get(self, pmid: str, analysis_config: dict[str, Any]) -> dict[str, Any] | None:
        """
        获取缓存结果
        Args:
            pmid: PubMed ID
            analysis_config: 分析配置
        Returns:
            缓存的分析结果，如果不存在或已过期则返回 None
        """
        if not self.enabled:
            return None
        try:
            cache_key = self._generate_cache_key(pmid, analysis_config)
            cache_file = self._get_cache_file_path(cache_key)
            if not cache_file.exists():
                logger.debug(f"缓存未命中: PMID={pmid}")
                return None
            # 读取缓存文件
            with open(cache_file, encoding="utf-8") as f:
                cache_data = json.load(f)
            # 检查是否过期
            cached_time = datetime.fromisoformat(cache_data["cached_at"])
            expire_time = cached_time + timedelta(days=self.expire_days)
            if datetime.now() > expire_time:
                logger.debug(f"缓存已过期: PMID={pmid}")
                # 删除过期缓存
                cache_file.unlink()
                return None
            logger.debug(f"缓存命中: PMID={pmid}")
            return cache_data["result"]
        except Exception as e:
            logger.warning(f"读取缓存失败: {e}")
            return None

    def set(
        self,
        pmid: str,
        analysis_config: dict[str, Any],
        result: dict[str, Any],
    ) -> bool:
        """
        设置缓存
        Args:
            pmid: PubMed ID
            analysis_config: 分析配置
            result: 分析结果
        Returns:
            是否成功设置缓存
        """
        if not self.enabled:
            return False
        try:
            cache_key = self._generate_cache_key(pmid, analysis_config)
            cache_file = self._get_cache_file_path(cache_key)
            # 构建缓存数据
            cache_data = {
                "pmid": pmid,
                "analysis_config": analysis_config,
                "result": result,
                "cached_at": datetime.now().isoformat(),
                "cache_key": cache_key,
            }
            # 写入缓存文件
            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump(cache_data, f, ensure_ascii=False, indent=2)
            logger.debug(f"缓存已保存: PMID={pmid}")
            return True
        except Exception as e:
            logger.warning(f"保存缓存失败: {e}")
            return False

    def clear_expired(self) -> int:
        """
        清理过期缓存
        Returns:
            清理的缓存文件数量
        """
        if not self.enabled:
            return 0
        cleared_count = 0
        expire_time = datetime.now() - timedelta(days=self.expire_days)
        try:
            for cache_file in self.cache_dir.rglob("*.json"):
                try:
                    with open(cache_file, encoding="utf-8") as f:
                        cache_data = json.load(f)
                    cached_time = datetime.fromisoformat(cache_data["cached_at"])
                    if cached_time < expire_time:
                        cache_file.unlink()
                        cleared_count += 1
                except Exception as e:
                    logger.warning(f"清理缓存文件失败 {cache_file}: {e}")
            logger.info(f"清理了 {cleared_count} 个过期缓存文件")
            return cleared_count
        except Exception as e:
            logger.error(f"清理过期缓存失败: {e}")
            return cleared_count

    def clear_all(self) -> int:
        """
        清空所有缓存
        Returns:
            清理的缓存文件数量
        """
        if not self.enabled:
            return 0
        cleared_count = 0
        try:
            for cache_file in self.cache_dir.rglob("*.json"):
                try:
                    cache_file.unlink()
                    cleared_count += 1
                except Exception as e:
                    logger.warning(f"删除缓存文件失败 {cache_file}: {e}")
            logger.info(f"清空了 {cleared_count} 个缓存文件")
            return cleared_count
        except Exception as e:
            logger.error(f"清空缓存失败: {e}")
            return cleared_count

    def get_cache_stats(self) -> dict[str, Any]:
        """
        获取缓存统计信息
        Returns:
            缓存统计信息
        """
        if not self.enabled:
            return {
                "enabled": False,
                "total_files": 0,
                "total_size_mb": 0,
            }
        try:
            total_files = 0
            total_size = 0
            for cache_file in self.cache_dir.rglob("*.json"):
                total_files += 1
                total_size += cache_file.stat().st_size
            return {
                "enabled": True,
                "cache_dir": str(self.cache_dir),
                "total_files": total_files,
                "total_size_mb": round(total_size / (1024 * 1024), 2),
                "expire_days": self.expire_days,
            }
        except Exception as e:
            logger.error(f"获取缓存统计失败: {e}")
            return {
                "enabled": True,
                "error": str(e),
            }
