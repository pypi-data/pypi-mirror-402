"""User agent utilities for Google Scholar crawler."""

import random


# Comprehensive list of realistic user agents
USER_AGENTS = [
    # Chrome on Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
    # Firefox on Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:119.0) Gecko/20100101 Firefox/119.0",
    # Chrome on macOS
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    # Safari on macOS
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 "
    "(KHTML, like Gecko) Version/17.1 Safari/605.1.15",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 "
    "(KHTML, like Gecko) Version/16.6 Safari/605.1.15",
    # Firefox on macOS
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:120.0) "
    "Gecko/20100101 Firefox/120.0",
    # Chrome on Linux
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/119.0.0.0 Safari/537.36",
    # Firefox on Linux
    "Mozilla/5.0 (X11; Linux x86_64; rv:120.0) Gecko/20100101 Firefox/120.0",
    "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:120.0) Gecko/20100101 Firefox/120.0",
    # Edge on Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36 Edg/119.0.0.0",
    # Mobile Chrome (for diversity)
    "Mozilla/5.0 (Linux; Android 10; SM-G973F) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_1 like Mac OS X) AppleWebKit/605.1.15 "
    "(KHTML, like Gecko) CriOS/120.0.0.0 Mobile/15E148 Safari/604.1",
]
# Academic-focused user agents (lower priority but more believable for scholarly search)
ACADEMIC_USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 "
    "(KHTML, like Gecko) Version/17.1 Safari/605.1.15",
]


def get_random_user_agent(academic_focused: bool = False) -> str:
    """
    Get a random user agent string.
    Args:
        academic_focused: If True, prefer user agents that look more academic
    Returns:
        Random user agent string
    """
    agents = ACADEMIC_USER_AGENTS if academic_focused else USER_AGENTS
    return random.choice(agents)


def get_user_agent_by_browser(browser: str = "chrome") -> str:
    """
    Get a user agent for a specific browser.
    Args:
        browser: Browser type (chrome, firefox, safari, edge)
    Returns:
        User agent string for the specified browser
    """
    browser = browser.lower()
    if browser == "chrome":
        chrome_agents = [
            ua for ua in USER_AGENTS if "Chrome/" in ua and "Edg/" not in ua
        ]
        return random.choice(chrome_agents)
    elif browser == "firefox":
        firefox_agents = [ua for ua in USER_AGENTS if "Firefox/" in ua]
        return random.choice(firefox_agents)
    elif browser == "safari":
        safari_agents = [
            ua for ua in USER_AGENTS if "Safari/" in ua and "Chrome/" not in ua
        ]
        return random.choice(safari_agents)
    elif browser == "edge":
        edge_agents = [ua for ua in USER_AGENTS if "Edg/" in ua]
        return random.choice(edge_agents)
    else:
        return get_random_user_agent()


def get_user_agent_by_platform(platform: str = "windows") -> str:
    """
    Get a user agent for a specific platform.
    Args:
        platform: Platform type (windows, macos, linux, mobile)
    Returns:
        User agent string for the specified platform
    """
    platform = platform.lower()
    if platform == "windows":
        windows_agents = [ua for ua in USER_AGENTS if "Windows NT" in ua]
        return random.choice(windows_agents)
    elif platform in ["macos", "mac"]:
        mac_agents = [ua for ua in USER_AGENTS if "Macintosh" in ua]
        return random.choice(mac_agents)
    elif platform == "linux":
        linux_agents = [
            ua for ua in USER_AGENTS if "Linux" in ua and "Android" not in ua
        ]
        return random.choice(linux_agents)
    elif platform == "mobile":
        mobile_agents = [
            ua
            for ua in USER_AGENTS
            if any(mobile in ua for mobile in ["Android", "iPhone", "Mobile"])
        ]
        return random.choice(mobile_agents)
    else:
        return get_random_user_agent()


class UserAgentRotator:
    """User agent rotator with session management."""

    def __init__(self, agents: list[str] | None = None, rotation_interval: int = 10):
        """
        Initialize user agent rotator.
        Args:
            agents: List of user agents to rotate through
            rotation_interval: Number of requests before rotating
        """
        self.agents = agents or USER_AGENTS.copy()
        self.rotation_interval = rotation_interval
        self.current_index = 0
        self.request_count = 0
        # Shuffle agents for randomness
        random.shuffle(self.agents)

    def get_user_agent(self) -> str:
        """Get current user agent and rotate if needed."""
        if self.request_count >= self.rotation_interval:
            self.rotate()
            self.request_count = 0
        self.request_count += 1
        return self.agents[self.current_index]

    def rotate(self) -> None:
        """Manually rotate to next user agent."""
        self.current_index = (self.current_index + 1) % len(self.agents)

    def get_current_agent(self) -> str:
        """Get current user agent without incrementing counter."""
        return self.agents[self.current_index]
