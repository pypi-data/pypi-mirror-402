"""Gemini CLI agent plugin for familiar."""

from __future__ import annotations

import subprocess
from pathlib import Path

from familiar.agents import Agent


class GeminiAgent(Agent):
    """Agent that uses the Gemini CLI."""

    name = "gemini"
    output_file = "GEMINI.md"

    def run(self, repo_root: Path, prompt: str, headless: bool) -> int:
        if headless:
            cmd = ["gemini", "-p", prompt]
        else:
            cmd = ["gemini", "-i", prompt]
        return subprocess.call(cmd, cwd=repo_root)
