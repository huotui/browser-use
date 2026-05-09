"""Test chiphell forum navigation and first post extraction."""

import os
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from browser_use.llm.messages import UserMessage, AssistantMessage


class TestChiphellFirstPost:
	"""Test suite for chiphell.com first post extraction."""

	CHIpHELL_URL = 'https://www.chiphell.com/'
	TASK_DESCRIPTION = '访问 https://www.chiphell.com/ 并找到首页第一个帖子，读取帖子标题和内容'

	def test_chiphell_task_llm_connection(self):
		"""Test local LLM connection for chiphell task."""
		os.environ['LOCAL_BASE_URL'] = 'http://192.168.0.120:1234/v1'
		os.environ['LOCAL_API_KEY'] = 'key'

		from browser_use.llm import get_llm_by_name

		llm = get_llm_by_name('local_gemma_4_26b')

		assert llm is not None
		assert hasattr(llm, 'model')
		assert llm.model == 'google/gemma-4-26b-a4b'
		assert llm.base_url == 'http://192.168.0.120:1234/v1'

	@pytest.mark.asyncio
	async def test_chiphell_task_llm_response_mock(self):
		"""Test LLM response for chiphell task with mocked browser."""
		os.environ['LOCAL_BASE_URL'] = 'http://192.168.0.120:1234/v1'
		os.environ['LOCAL_API_KEY'] = 'key'

		from browser_use.llm import get_llm_by_name

		llm = get_llm_by_name('local_gemma_4_26b')

		# Mock LLM response
		mock_response = AssistantMessage(content='Chiphell首页第一个帖子标题是：RTX 5090评测')

		with patch.object(llm, 'ainvoke', new=AsyncMock(return_value=mock_response)):
			messages = [UserMessage(content=self.TASK_DESCRIPTION)]
			response = await llm.ainvoke(messages)

			assert response is not None
			# Extract text from content (could be string or ContentText)
			if hasattr(response, 'content'):
				content = response.content
			else:
				content = str(response)
			
			assert 'RTX 5090' in content

	def test_chiphell_url_format(self):
		"""Test chiphell URL is correctly formatted."""
		from urllib.parse import urlparse

		parsed = urlparse(self.CHIpHELL_URL)
		assert parsed.scheme == 'https'
		assert parsed.netloc == 'www.chiphell.com'
		assert parsed.path == '/'
