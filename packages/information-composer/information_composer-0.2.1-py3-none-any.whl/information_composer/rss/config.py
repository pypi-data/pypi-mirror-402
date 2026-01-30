"""Configuration manager for RSS feeds.
This module manages RSS feed subscriptions through YAML configuration files,
supporting CRUD operations and validation.
"""

# import os
from pathlib import Path
from typing import Any

import yaml

from information_composer.rss.models import FeedConfig


class ConfigManager:
    """Manager for RSS feed configuration."""

    def __init__(self, config_path: str | Path | None = None) -> None:
        """Initialize configuration manager.
        Args:
            config_path: Path to configuration file. If None, uses default location.
        """
        if config_path is None:
            config_path = (
                Path.home() / ".config" / "information-composer" / "rss_feeds.yaml"
            )
        self.config_path = Path(config_path)
        self.config_data: dict[str, Any] = {}

    def load_config(self) -> dict[str, Any]:
        """Load configuration from file.
        Returns:
            Configuration dictionary
        Raises:
            FileNotFoundError: If config file doesn't exist
            RuntimeError: If config file is invalid
        """
        if not self.config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {self.config_path}")
        try:
            with open(self.config_path) as f:
                self.config_data = yaml.safe_load(f) or {}
            return self.config_data
        except yaml.YAMLError as e:
            raise RuntimeError(f"Error parsing configuration file: {e}") from e

    def save_config(self, config_data: dict[str, Any] | None = None) -> None:
        """Save configuration to file.
        Args:
            config_data: Configuration data to save. If None, uses current config.
        """
        if config_data is not None:
            self.config_data = config_data
        # Ensure directory exists
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_path, "w") as f:
            yaml.safe_dump(
                self.config_data, f, default_flow_style=False, allow_unicode=True
            )

    def init_default_config(self) -> None:
        """Initialize default configuration with Nature and Molecular Plant feeds."""
        default_config = {
            "version": "1.0",
            "settings": {
                "cache_enabled": True,
                "cache_dir": ".cache/rss",
                "cache_expire_days": 7,
                "fetch_timeout": 30,
                "max_retries": 3,
                "retry_delay": 2,
                "user_agent": "information-composer/0.1.3",
                "max_concurrent": 5,
                "delay_between_requests": 1.0,
            },
            "feeds": {
                "academic_journals": [
                    {
                        "name": "Molecular Plant",
                        "url": "http://www.cell.com/molecular-plant/inpress.rss",
                        "category": "Plant Science",
                        "enabled": True,
                        "tags": ["plant", "molecular-biology", "genomics"],
                        "update_interval": 3600,
                        "filter": {
                            "keywords": ["rice", "gene expression", "plant immunity"],
                            "exclude_keywords": [],
                        },
                        "metadata": {"publisher": "Cell Press", "impact_factor": 27.5},
                    },
                    {
                        "name": "Nature",
                        "url": "https://www.nature.com/nature.rss",
                        "category": "Multidisciplinary Science",
                        "enabled": True,
                        "tags": ["nature", "multidisciplinary", "research"],
                        "update_interval": 1800,
                        "filter": {
                            "keywords": ["genomics", "CRISPR", "plant"],
                            "exclude_keywords": [],
                        },
                        "metadata": {
                            "publisher": "Nature Publishing Group",
                            "impact_factor": 64.8,
                        },
                    },
                ],
                "tech_blogs": [],
                "news": [],
            },
            "filter_rules": {
                "global_exclude": ["advertisement", "sponsored"],
                "date_filter": {"enabled": False, "days_back": 30},
            },
            "output": {
                "default_format": "json",
                "output_dir": "./rss_output",
                "save_raw": False,
            },
        }
        self.config_data = default_config
        self.save_config()

    def validate_config(self) -> tuple[bool, list[str]]:
        """Validate configuration structure and content.
        Returns:
            Tuple of (is_valid, list of error messages)
        """
        errors = []
        if not self.config_data:
            errors.append("Configuration is empty")
            return False, errors
        # Check required top-level keys
        if "version" not in self.config_data:
            errors.append("Missing 'version' field")
        if "feeds" not in self.config_data:
            errors.append("Missing 'feeds' field")
            return False, errors
        # Validate each feed
        feeds = self.config_data.get("feeds", {})
        for group_name, feed_list in feeds.items():
            if not isinstance(feed_list, list):
                errors.append(f"Feed group '{group_name}' must be a list")
                continue
            for idx, feed in enumerate(feed_list):
                feed_id = f"{group_name}[{idx}]"
                # Check required fields
                if "name" not in feed:
                    errors.append(f"{feed_id}: Missing 'name' field")
                if "url" not in feed:
                    errors.append(f"{feed_id}: Missing 'url' field")
                # Validate URL format
                if "url" in feed and not feed["url"].startswith(
                    ("http://", "https://")
                ):
                    errors.append(f"{feed_id}: Invalid URL format")
                # Validate update_interval
                if "update_interval" in feed:
                    try:
                        interval = int(feed["update_interval"])
                        if interval < 0:
                            errors.append(
                                f"{feed_id}: update_interval must be positive"
                            )
                    except (ValueError, TypeError):
                        errors.append(f"{feed_id}: update_interval must be a number")
        return len(errors) == 0, errors

    def get_enabled_feeds(self) -> list[FeedConfig]:
        """Get all enabled feeds from configuration.
        Returns:
            List of enabled FeedConfig objects
        """
        feeds = []
        for _group_name, feed_list in self.config_data.get("feeds", {}).items():
            for feed_data in feed_list:
                if feed_data.get("enabled", True):
                    feeds.append(FeedConfig.from_dict(feed_data))
        return feeds

    def get_feeds_by_group(self, group_name: str) -> list[FeedConfig]:
        """Get feeds from a specific group.
        Args:
            group_name: Name of the feed group
        Returns:
            List of FeedConfig objects in the group
        """
        feed_list = self.config_data.get("feeds", {}).get(group_name, [])
        return [FeedConfig.from_dict(feed) for feed in feed_list]

    def get_feed_by_name(self, name: str) -> FeedConfig | None:
        """Get a feed by its name.
        Args:
            name: Feed name
        Returns:
            FeedConfig object or None if not found
        """
        for _group_name, feed_list in self.config_data.get("feeds", {}).items():
            for feed_data in feed_list:
                if feed_data.get("name") == name:
                    return FeedConfig.from_dict(feed_data)
        return None

    def add_feed(self, feed_config: FeedConfig, group: str = "tech_blogs") -> None:
        """Add a new feed to configuration.
        Args:
            feed_config: Feed configuration to add
            group: Group to add feed to
        """
        if "feeds" not in self.config_data:
            self.config_data["feeds"] = {}
        if group not in self.config_data["feeds"]:
            self.config_data["feeds"][group] = []
        # Check if feed already exists
        existing_names = [f.get("name") for f in self.config_data["feeds"][group]]
        if feed_config.name in existing_names:
            raise ValueError(
                f"Feed '{feed_config.name}' already exists in group '{group}'"
            )
        self.config_data["feeds"][group].append(feed_config.to_dict())
        self.save_config()

    def remove_feed(self, name: str) -> bool:
        """Remove a feed by name.
        Args:
            name: Feed name to remove
        Returns:
            True if feed was removed, False if not found
        """
        for group_name, feed_list in self.config_data.get("feeds", {}).items():
            for idx, feed in enumerate(feed_list):
                if feed.get("name") == name:
                    del self.config_data["feeds"][group_name][idx]
                    self.save_config()
                    return True
        return False

    def update_feed(self, name: str, updates: dict[str, Any]) -> bool:
        """Update a feed's configuration.
        Args:
            name: Feed name to update
            updates: Dictionary of fields to update
        Returns:
            True if feed was updated, False if not found
        """
        for _group_name, feed_list in self.config_data.get("feeds", {}).items():
            for feed in feed_list:
                if feed.get("name") == name:
                    feed.update(updates)
                    self.save_config()
                    return True
        return False

    def enable_feed(self, name: str) -> bool:
        """Enable a feed.
        Args:
            name: Feed name to enable
        Returns:
            True if feed was enabled, False if not found
        """
        return self.update_feed(name, {"enabled": True})

    def disable_feed(self, name: str) -> bool:
        """Disable a feed.
        Args:
            name: Feed name to disable
        Returns:
            True if feed was disabled, False if not found
        """
        return self.update_feed(name, {"enabled": False})

    def list_all_feeds(self) -> list[dict[str, Any]]:
        """List all feeds with their groups.
        Returns:
            List of dictionaries with feed info and group
        """
        all_feeds = []
        for group_name, feed_list in self.config_data.get("feeds", {}).items():
            for feed in feed_list:
                all_feeds.append(
                    {
                        "group": group_name,
                        "name": feed.get("name"),
                        "url": feed.get("url"),
                        "enabled": feed.get("enabled", True),
                        "category": feed.get("category", ""),
                    }
                )
        return all_feeds

    def get_settings(self) -> dict[str, Any]:
        """Get global settings from configuration.
        Returns:
            Settings dictionary
        """
        return self.config_data.get("settings", {})
