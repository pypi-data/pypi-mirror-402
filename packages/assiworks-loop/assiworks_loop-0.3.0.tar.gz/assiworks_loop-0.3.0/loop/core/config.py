"""Configuration management."""

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

import yaml
from dotenv import load_dotenv
from claude_agent_sdk import ClaudeAgentOptions

from loop.agent.hooks import create_safety_hooks


@dataclass
class Config:
    """Application configuration mapped to ClaudeAgentOptions."""

    # SDK options
    model: str = "claude-sonnet-4-20250514"
    permission_mode: str = "acceptEdits"
    allowed_tools: List[str] = field(
        default_factory=lambda: ["Read", "Write", "Edit", "Bash", "Glob", "Grep"]
    )
    cwd: Optional[str] = None

    # Session
    session_dir: str = ".assiworks/sessions"

    # Ralph Loop
    ralph_max_iterations: int = 100
    ralph_no_progress_threshold: int = 3
    ralph_same_error_threshold: int = 5

    # Safety
    bash_blocked_commands: List[str] = field(
        default_factory=lambda: ["rm -rf /", "dd if=", "mkfs", "> /dev/sda"]
    )

    def to_sdk_options(self, resume: Optional[str] = None) -> ClaudeAgentOptions:
        """Convert Config to ClaudeAgentOptions."""
        return ClaudeAgentOptions(
            model=self.model,
            permission_mode=self.permission_mode,
            allowed_tools=self.allowed_tools,
            cwd=self.cwd or str(Path.cwd()),
            hooks=create_safety_hooks(self.bash_blocked_commands),
            resume=resume,
        )


def load_config(config_path: Optional[str] = None) -> Config:
    """Load configuration from file and environment.

    Priority:
    1. Environment variables
    2. Config file (if specified)
    3. Default values
    """
    # Load .env file
    load_dotenv()

    config = Config()

    # Load from YAML if specified
    if config_path and Path(config_path).exists():
        with open(config_path, "r") as f:
            data = yaml.safe_load(f) or {}

        # Map YAML structure to Config
        if "agent" in data:
            agent = data["agent"]
            config.model = agent.get("model", config.model)
            config.permission_mode = agent.get("permission_mode", config.permission_mode)

        if "tools" in data:
            tools = data["tools"]
            config.allowed_tools = tools.get("allowed", config.allowed_tools)
            config.bash_blocked_commands = tools.get(
                "bash_blocked_commands", config.bash_blocked_commands
            )

        if "session" in data:
            session = data["session"]
            config.session_dir = session.get("persistence_dir", config.session_dir)

        if "ralph" in data:
            ralph = data["ralph"]
            config.ralph_max_iterations = ralph.get(
                "max_iterations", config.ralph_max_iterations
            )
            config.ralph_no_progress_threshold = ralph.get(
                "no_progress_threshold", config.ralph_no_progress_threshold
            )
            config.ralph_same_error_threshold = ralph.get(
                "same_error_threshold", config.ralph_same_error_threshold
            )

    # Override with environment variables
    if os.getenv("CLAUDE_MODEL"):
        config.model = os.getenv("CLAUDE_MODEL")

    return config
