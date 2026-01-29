"""tests for familiar-gemini."""

from __future__ import annotations

from unittest.mock import patch

from familiar.agents import Agent
from familiar_gemini import GeminiAgent


class TestGeminiAgent:
    """tests for gemini agent."""

    def test_is_agent_subclass(self):
        assert issubclass(GeminiAgent, Agent)

    def test_name(self):
        agent = GeminiAgent()
        assert agent.name == "gemini"

    def test_output_file(self):
        agent = GeminiAgent()
        assert agent.output_file == "GEMINI.md"

    def test_run_headless(self, tmp_path):
        agent = GeminiAgent()

        with patch("familiar_gemini.subprocess.call", return_value=0) as mock_call:
            result = agent.run(tmp_path, "test prompt", headless=True)
            assert result == 0
            mock_call.assert_called_once_with(
                ["gemini", "-p", "test prompt"], cwd=tmp_path
            )

    def test_run_interactive(self, tmp_path):
        agent = GeminiAgent()

        with patch("familiar_gemini.subprocess.call", return_value=0) as mock_call:
            result = agent.run(tmp_path, "test prompt", headless=False)
            assert result == 0
            mock_call.assert_called_once_with(
                ["gemini", "-i", "test prompt"], cwd=tmp_path
            )

    def test_run_returns_exit_code(self, tmp_path):
        agent = GeminiAgent()

        with patch("familiar_gemini.subprocess.call", return_value=42):
            result = agent.run(tmp_path, "prompt", headless=True)
            assert result == 42
