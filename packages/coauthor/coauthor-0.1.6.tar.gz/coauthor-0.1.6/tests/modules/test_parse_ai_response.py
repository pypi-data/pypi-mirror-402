import logging

from coauthor.modules.jira_watcher import parse_ai_response


def test_parse_ai_response_direct_json_string():
    logger = logging.getLogger(__name__)
    response = '{"comment": "hello", "labels": ["x"]}'
    parsed = parse_ai_response(response, logger)
    assert parsed["comment"] == "hello"
    assert parsed["labels"] == ["x"]


def test_parse_ai_response_fenced_json_string():
    logger = logging.getLogger(__name__)
    response = """```json
{"comment": "hello"}
```"""
    parsed = parse_ai_response(response, logger)
    assert parsed["comment"] == "hello"


def test_parse_ai_response_extract_braces():
    logger = logging.getLogger(__name__)
    response = "Here you go: {\"comment\": \"hello\"} thanks"
    parsed = parse_ai_response(response, logger)
    assert parsed["comment"] == "hello"


def test_parse_ai_response_invalid_returns_none():
    logger = logging.getLogger(__name__)
    assert parse_ai_response("not json", logger) is None
