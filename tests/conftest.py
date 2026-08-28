"""共享 fixtures。"""

from __future__ import annotations

import pytest

from kodeagent.core.llm import MockLLMProvider


@pytest.fixture
def mock_llm() -> MockLLMProvider:
    return MockLLMProvider(responses={"hello": "hi there"})
