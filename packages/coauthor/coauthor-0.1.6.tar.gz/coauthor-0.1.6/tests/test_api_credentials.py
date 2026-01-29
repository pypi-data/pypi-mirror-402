"""
Tests for API credential override per workflow task (C2-1178).
"""

import os
import pytest
from unittest.mock import patch
from coauthor.modules.ai import get_api_credentials


def test_get_api_credentials_uses_agent_defaults():
    """Test that agent defaults are used when task has no overrides."""
    task = {"id": "test-task"}
    agent = {"api_key_var": "DEFAULT_API_KEY", "api_url_var": "DEFAULT_API_URL"}

    with patch.dict(os.environ, {"DEFAULT_API_KEY": "default-key-value", "DEFAULT_API_URL": "https://default.api.com"}):
        api_url, api_key = get_api_credentials(task, agent)

    assert api_key == "default-key-value"
    assert api_url == "https://default.api.com"


def test_get_api_credentials_task_overrides_api_key():
    """Test that task.api_key_var overrides agent.api_key_var."""
    task = {"id": "test-task", "api_key_var": "TASK_API_KEY"}
    agent = {"api_key_var": "DEFAULT_API_KEY", "api_url_var": "DEFAULT_API_URL"}

    with patch.dict(
        os.environ,
        {
            "DEFAULT_API_KEY": "default-key-value",
            "DEFAULT_API_URL": "https://default.api.com",
            "TASK_API_KEY": "task-key-value",
        },
    ):
        api_url, api_key = get_api_credentials(task, agent)

    assert api_key == "task-key-value"  # Task override used
    assert api_url == "https://default.api.com"  # Agent default used


def test_get_api_credentials_task_overrides_api_url():
    """Test that task.api_url_var overrides agent.api_url_var."""
    task = {"id": "test-task", "api_url_var": "TASK_API_URL"}
    agent = {"api_key_var": "DEFAULT_API_KEY", "api_url_var": "DEFAULT_API_URL"}

    with patch.dict(
        os.environ,
        {
            "DEFAULT_API_KEY": "default-key-value",
            "DEFAULT_API_URL": "https://default.api.com",
            "TASK_API_URL": "https://task.api.com",
        },
    ):
        api_url, api_key = get_api_credentials(task, agent)

    assert api_key == "default-key-value"  # Agent default used
    assert api_url == "https://task.api.com"  # Task override used


def test_get_api_credentials_task_overrides_both():
    """Test that task can override both api_key_var and api_url_var."""
    task = {"id": "test-task", "api_key_var": "TASK_API_KEY", "api_url_var": "TASK_API_URL"}
    agent = {"api_key_var": "DEFAULT_API_KEY", "api_url_var": "DEFAULT_API_URL"}

    with patch.dict(
        os.environ,
        {
            "DEFAULT_API_KEY": "default-key-value",
            "DEFAULT_API_URL": "https://default.api.com",
            "TASK_API_KEY": "task-key-value",
            "TASK_API_URL": "https://task.api.com",
        },
    ):
        api_url, api_key = get_api_credentials(task, agent)

    assert api_key == "task-key-value"  # Task override used
    assert api_url == "https://task.api.com"  # Task override used


def test_get_api_credentials_uses_direct_api_key():
    """Test that agent.api_key (direct value) is used when present."""
    task = {"id": "test-task"}
    agent = {"api_key": "direct-key-value", "api_url_var": "DEFAULT_API_URL"}

    with patch.dict(os.environ, {"DEFAULT_API_URL": "https://default.api.com"}):
        api_url, api_key = get_api_credentials(task, agent)

    assert api_key == "direct-key-value"
    assert api_url == "https://default.api.com"


def test_get_api_credentials_uses_direct_api_url():
    """Test that agent.api_url (direct value) is used when present."""
    task = {"id": "test-task"}
    agent = {"api_key_var": "DEFAULT_API_KEY", "api_url": "https://direct.api.com"}

    with patch.dict(os.environ, {"DEFAULT_API_KEY": "default-key-value"}):
        api_url, api_key = get_api_credentials(task, agent)

    assert api_key == "default-key-value"
    assert api_url == "https://direct.api.com"


def test_get_api_credentials_task_override_with_missing_env_var():
    """Test that None is returned when task override env var doesn't exist."""
    task = {"id": "test-task", "api_key_var": "NONEXISTENT_API_KEY"}
    agent = {"api_key_var": "DEFAULT_API_KEY", "api_url_var": "DEFAULT_API_URL"}

    with patch.dict(
        os.environ, {"DEFAULT_API_KEY": "default-key-value", "DEFAULT_API_URL": "https://default.api.com"}, clear=True
    ):
        api_url, api_key = get_api_credentials(task, agent)

    assert api_key is None  # Missing env var
    assert api_url == "https://default.api.com"
