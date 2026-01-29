from coauthor.modules.summary import should_summarize, extract_relevant_messages_for_summary


def test_should_summarize_after_first():
    assert should_summarize(1, summarize_after=1, summarize_every=3) is True
    assert should_summarize(2, summarize_after=1, summarize_every=3) is False
    assert should_summarize(3, summarize_after=1, summarize_every=3) is False
    assert should_summarize(4, summarize_after=1, summarize_every=3) is True


def test_should_summarize_disabled_when_after_is_zero():
    assert should_summarize(1, summarize_after=0, summarize_every=3) is False


def test_should_summarize_when_every_is_zero_only_matches_after():
    assert should_summarize(1, summarize_after=1, summarize_every=0) is True
    assert should_summarize(2, summarize_after=1, summarize_every=0) is False


def test_extract_relevant_messages_for_summary():
    messages = [
        {"role": "user", "content": "User msg 1"},
        {"role": "user", "content": "User msg 2"},
        {"role": "user", "content": "User msg 3"},
        {"role": "user", "content": "User msg 4"},
        {"role": "assistant", "content": "No tools"},
        {"role": "assistant", "tool_calls": [{"fn": "one"}], "content": "Tool call one"},
        {"role": "assistant", "tool_calls": [{"fn": "two"}], "content": "Tool call two"},
        {"role": "assistant", "tool_calls": [{"fn": "three"}], "content": "Tool call three"},
        {"role": "tool", "content": "tool resp one"},
        {"role": "tool", "content": "tool resp two"},
        {"role": "tool", "content": "tool resp three"},
    ]
    # Only first 3 user messages, assistant tool calls except the last, tool msgs except last
    summary_msgs = extract_relevant_messages_for_summary(messages)
    assert len(summary_msgs) == 3 + 2 + 2 # 3 user, 2 assistant tool calls, 2 tool responses
    assert all(m["role"] == "user" for m in summary_msgs[:3])
    assert all(m["role"] == "assistant" for m in summary_msgs[3:5])
    assert all(m["role"] == "tool" for m in summary_msgs[5:])

    # Less than 3 tool calls: summary msgs should be empty
    short_msgs = messages[:7]  # Only 2 tool_calls
    assert extract_relevant_messages_for_summary(short_msgs) == []
