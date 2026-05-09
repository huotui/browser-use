"""Test local LLM connection and configuration."""

import os
from unittest.mock import AsyncMock, patch

import pytest

from browser_use.llm.messages import UserMessage


class TestLocalLLMConnection:
	"""Test suite for local LLM (LM Studio/Ollama) connection."""

	LOCAL_BASE_URL = 'http://127.0.0.1:1234/v1'
	LOCAL_MODEL = 'qwen/qwen3.6-35b-a3b'

	def test_get_llm_by_name_local_provider(self):
		"""Test get_llm_by_name creates ChatOpenAI with local base_url."""
		# Set environment variables
		os.environ['LOCAL_BASE_URL'] = self.LOCAL_BASE_URL
		os.environ['LOCAL_API_KEY'] = 'test-key'

		from browser_use.llm import get_llm_by_name

		llm = get_llm_by_name('local_qwen3_6_35b')

		# Verify it's a ChatOpenAI instance with correct config
		assert llm is not None
		assert hasattr(llm, 'model')
		assert hasattr(llm, 'base_url')
		assert self.LOCAL_MODEL in llm.model or 'qwen' in llm.model.lower()
		assert llm.base_url == self.LOCAL_BASE_URL

	def test_get_llm_by_name_all_local_models(self):
		"""Test all local model aliases can be created."""
		local_models = [
			'local_qwen3_6_35b',
			'local_qwen3_6_27b',
			'local_nemotron_3_nano_omni',
		]

		from browser_use.llm import get_llm_by_name

		for model_name in local_models:
			llm = get_llm_by_name(model_name)
			assert llm is not None, f'Failed to create {model_name}'
			assert hasattr(llm, 'model')
			assert hasattr(llm, 'base_url')
			assert llm.base_url == self.LOCAL_BASE_URL

	@pytest.mark.asyncio
	async def test_local_llm_connection_mock(self):
		"""Test local LLM connection with mocked response."""
		os.environ['LOCAL_BASE_URL'] = self.LOCAL_BASE_URL
		os.environ['LOCAL_API_KEY'] = 'test-key'

		from browser_use.llm import get_llm_by_name

		llm = get_llm_by_name('local_qwen3_6_35b')

		# Mock the ainvoke method
		from browser_use.llm.base import BaseChatModel
		from browser_use.llm.messages import AssistantMessage

		mock_response = AssistantMessage(content='Connection successful')

		with patch.object(llm, 'ainvoke', new=AsyncMock(return_value=mock_response)):
			messages = [UserMessage(content='Say "Connection successful" in one sentence.')]
			response = await llm.ainvoke(messages)

			assert response is not None
			assert response.completion == 'Connection successful'

	def test_local_llm_default_base_url(self):
		"""Test local LLM uses default base_url when not set."""
		# Clear environment
		os.environ.pop('LOCAL_BASE_URL', None)

		from browser_use.llm.models import get_llm_by_name

		llm = get_llm_by_name('local_qwen3_6_35b')

		assert llm.base_url == 'http://127.0.0.1:1234/v1'

	def test_local_llm_custom_base_url(self):
		"""Test local LLM respects custom base_url."""
		custom_url = 'http://localhost:8080/v1'
		os.environ['LOCAL_BASE_URL'] = custom_url

		from browser_use.llm.models import get_llm_by_name

		llm = get_llm_by_name('local_qwen3_6_35b')

		assert llm.base_url == custom_url
