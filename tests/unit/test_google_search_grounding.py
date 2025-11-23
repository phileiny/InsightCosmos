# -*- coding: utf-8 -*-
"""
单元测试：GoogleSearchGroundingTool

基于 googleapis/python-genai v1.33.0 官方 SDK
测试 Gemini Search Grounding 功能

测试案例:
- TC-4V2-01 到 TC-4V2-14
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.tools.google_search_grounding_v2 import GoogleSearchGroundingTool


class TestGoogleSearchGroundingTool(unittest.TestCase):
    """GoogleSearchGroundingTool 单元测试"""

    def setUp(self):
        """测试前准备"""
        self.api_key = "test_api_key_12345"
        self.test_query = "AI multi-agent systems"

    def tearDown(self):
        """测试后清理"""
        pass

    # TC-4V2-01: 初始化（有 API Key）
    @patch('google.genai.Client')
    def test_init_with_api_key(self, mock_client_class):
        """测试使用 API Key 初始化工具"""
        # Mock Client
        mock_client = Mock()
        mock_client_class.return_value = mock_client

        # 初始化工具
        tool = GoogleSearchGroundingTool(api_key=self.api_key)

        # 验证
        self.assertEqual(tool.api_key, self.api_key)
        self.assertEqual(tool.model_name, "gemini-2.5-flash")
        mock_client_class.assert_called_once_with(api_key=self.api_key)

    # TC-4V2-02: 初始化（无 API Key）
    @patch('src.utils.config.Config.load')
    def test_init_without_api_key_raises_error(self, mock_config_load):
        """测试无 API Key 时抛出错误"""
        # Mock Config.load 抛出错误
        mock_config_load.side_effect = ValueError("API key not found")

        # 验证抛出 ValueError
        with self.assertRaises(ValueError) as context:
            GoogleSearchGroundingTool()

        self.assertIn("Google API key not found", str(context.exception))

    # TC-4V2-03: 构建搜索 Prompt
    def test_build_search_prompt(self):
        """测试搜索 Prompt 构建"""
        with patch('google.genai.Client'):
            tool = GoogleSearchGroundingTool(api_key=self.api_key)

            # 测试基本 Prompt
            prompt = tool.build_search_prompt(
                query="AI news",
                max_results=10,
                date_restrict=None,
                language='en'
            )

            self.assertIn("AI news", prompt)
            self.assertIn("10", prompt)

            # 测试带时间限制的 Prompt
            prompt_with_date = tool.build_search_prompt(
                query="AI news",
                max_results=5,
                date_restrict="past week",
                language='en'
            )

            self.assertIn("past week", prompt_with_date)

    # TC-4V2-04: 单次搜索（成功）
    @patch('google.genai.Client')
    def test_search_articles_success(self, mock_client_class):
        """测试成功的单次搜索"""
        # Mock Client
        mock_client = Mock()
        mock_client_class.return_value = mock_client

        # Mock Response
        mock_response = Mock()
        mock_candidate = Mock()
        mock_grounding_metadata = Mock()

        # Mock Grounding Chunks
        mock_web_chunk = Mock()
        mock_web_chunk.uri = 'https://example.com/article'
        mock_web_chunk.title = 'Test Article'

        mock_chunk = Mock()
        mock_chunk.web = mock_web_chunk

        mock_grounding_metadata.grounding_chunks = [mock_chunk]
        mock_candidate.grounding_metadata = mock_grounding_metadata
        mock_response.candidates = [mock_candidate]

        mock_client.models.generate_content.return_value = mock_response

        # 测试
        tool = GoogleSearchGroundingTool(api_key=self.api_key)
        result = tool.search_articles("AI news", max_results=5)

        # 验证
        self.assertEqual(result['status'], 'success')
        self.assertEqual(result['query'], 'AI news')
        self.assertGreater(len(result['articles']), 0)
        self.assertEqual(result['articles'][0]['url'], 'https://example.com/article')
        self.assertEqual(result['articles'][0]['title'], 'Test Article')

    # TC-4V2-05: 单次搜索（API 错误）
    @patch('google.genai.Client')
    def test_search_articles_api_error(self, mock_client_class):
        """测试 API 错误处理"""
        # Mock Client
        mock_client = Mock()
        mock_client_class.return_value = mock_client

        # Mock API Error
        mock_client.models.generate_content.side_effect = Exception("API Error")

        # 测试
        tool = GoogleSearchGroundingTool(api_key=self.api_key)
        result = tool.search_articles("AI news")

        # 验证
        self.assertEqual(result['status'], 'error')
        self.assertIn('API Error', result['error_message'])

    # TC-4V2-06: 批次搜索（全部成功）
    @patch('google.genai.Client')
    def test_batch_search_all_success(self, mock_client_class):
        """测试批次搜索（全部成功）"""
        # Mock Client
        mock_client = Mock()
        mock_client_class.return_value = mock_client

        # Mock Response（简化版）
        mock_response = Mock()
        mock_candidate = Mock()
        mock_grounding_metadata = Mock()
        mock_grounding_metadata.grounding_chunks = []
        mock_candidate.grounding_metadata = mock_grounding_metadata
        mock_response.candidates = [mock_candidate]

        mock_client.models.generate_content.return_value = mock_response

        # 测试
        tool = GoogleSearchGroundingTool(api_key=self.api_key)
        queries = ["AI", "robotics", "multi-agent"]
        result = tool.batch_search(queries, max_results_per_query=3)

        # 验证
        self.assertIn(result['status'], ['success', 'partial'])  # 可能无结果但成功
        self.assertEqual(result['summary']['total_queries'], 3)

    # TC-4V2-07: 批次搜索（部分失败）
    @patch('google.genai.Client')
    def test_batch_search_partial_failure(self, mock_client_class):
        """测试批次搜索（部分失败）"""
        # Mock Client
        mock_client = Mock()
        mock_client_class.return_value = mock_client

        # Mock：第一次成功，第二次失败
        mock_response_success = Mock()
        mock_candidate = Mock()
        mock_grounding_metadata = Mock()
        mock_grounding_metadata.grounding_chunks = []
        mock_candidate.grounding_metadata = mock_grounding_metadata
        mock_response_success.candidates = [mock_candidate]

        mock_client.models.generate_content.side_effect = [
            mock_response_success,  # 第一次成功
            Exception("API Error"),  # 第二次失败
            mock_response_success   # 第三次成功
        ]

        # 测试
        tool = GoogleSearchGroundingTool(api_key=self.api_key)
        queries = ["AI", "robotics", "multi-agent"]
        result = tool.batch_search(queries, max_results_per_query=2)

        # 验证
        self.assertEqual(result['status'], 'partial')
        self.assertEqual(result['summary']['failed_queries'], 1)
        self.assertGreater(len(result['errors']), 0)

    # TC-4V2-08: 提取 Grounding Metadata
    @patch('google.genai.Client')
    def test_extract_articles_from_response(self, mock_client_class):
        """测试从 Response 提取文章"""
        with patch('google.genai.Client'):
            tool = GoogleSearchGroundingTool(api_key=self.api_key)

            # Mock Response
            mock_response = Mock()
            mock_candidate = Mock()
            mock_grounding_metadata = Mock()

            # 创建多个 Chunks
            chunks = []
            for i in range(3):
                mock_web = Mock()
                mock_web.uri = f'https://example{i}.com/article'
                mock_web.title = f'Article {i}'

                mock_chunk = Mock()
                mock_chunk.web = mock_web
                chunks.append(mock_chunk)

            mock_grounding_metadata.grounding_chunks = chunks
            mock_candidate.grounding_metadata = mock_grounding_metadata
            mock_response.candidates = [mock_candidate]

            # 测试
            articles = tool.extract_articles_from_response(mock_response, "test query")

            # 验证
            self.assertEqual(len(articles), 3)
            self.assertEqual(articles[0]['url'], 'https://example0.com/article')
            self.assertEqual(articles[1]['title'], 'Article 1')

    # TC-4V2-09: 解析 Grounding Chunk
    @patch('google.genai.Client')
    def test_parse_grounding_chunk(self, mock_client_class):
        """测试解析单个 Grounding Chunk"""
        with patch('google.genai.Client'):
            tool = GoogleSearchGroundingTool(api_key=self.api_key)

            # Mock Web Chunk
            mock_web_chunk = Mock()
            mock_web_chunk.uri = 'https://www.example.com/article'
            mock_web_chunk.title = 'Test Article Title'

            # 测试
            article = tool.parse_grounding_chunk(mock_web_chunk, "AI robotics")

            # 验证
            self.assertIsNotNone(article)
            self.assertEqual(article['url'], 'https://www.example.com/article')
            self.assertEqual(article['title'], 'Test Article Title')
            self.assertEqual(article['source'], 'google_search_grounding')
            self.assertEqual(article['search_query'], 'AI robotics')

    # TC-4V2-10: 提取域名
    def test_extract_domain(self):
        """测试从 URL 提取域名"""
        # 测试带 www 的 URL
        domain1 = GoogleSearchGroundingTool.extract_domain("https://www.example.com/article")
        self.assertEqual(domain1, "example.com")

        # 测试不带 www 的 URL
        domain2 = GoogleSearchGroundingTool.extract_domain("https://blog.openai.com/post")
        self.assertEqual(domain2, "blog.openai.com")

        # 测试无效 URL
        domain3 = GoogleSearchGroundingTool.extract_domain("")
        self.assertEqual(domain3, "unknown")

    # TC-4V2-11: URL 去重
    @patch('google.genai.Client')
    def test_url_deduplication(self, mock_client_class):
        """测试 URL 去重功能"""
        with patch('google.genai.Client'):
            tool = GoogleSearchGroundingTool(api_key=self.api_key)

            # Mock Response with duplicate URLs
            mock_response = Mock()
            mock_candidate = Mock()
            mock_grounding_metadata = Mock()

            # 创建重复的 Chunks
            chunks = []
            for i in range(5):
                mock_web = Mock()
                # 前3个URL相同，后2个不同
                if i < 3:
                    mock_web.uri = 'https://example.com/article'
                else:
                    mock_web.uri = f'https://example{i}.com/article'
                mock_web.title = f'Article {i}'

                mock_chunk = Mock()
                mock_chunk.web = mock_web
                chunks.append(mock_chunk)

            mock_grounding_metadata.grounding_chunks = chunks
            mock_candidate.grounding_metadata = mock_grounding_metadata
            mock_response.candidates = [mock_candidate]

            # 测试
            articles = tool.extract_articles_from_response(mock_response, "test")

            # 验证：应该只有3篇文章（去重后）
            self.assertEqual(len(articles), 3)

    # TC-4V2-12: Context Manager
    @patch('google.genai.Client')
    def test_context_manager(self, mock_client_class):
        """测试 Context Manager 功能"""
        # Mock Client
        mock_client = Mock()
        mock_client_class.return_value = mock_client

        # 使用 with 语句
        with GoogleSearchGroundingTool(api_key=self.api_key) as tool:
            self.assertIsNotNone(tool)
            self.assertEqual(tool.api_key, self.api_key)

        # 验证 close() 被调用
        mock_client.close.assert_called_once()

    # TC-4V2-13: 验证 API 凭证（有效）
    @patch('google.genai.Client')
    def test_validate_api_credentials_success(self, mock_client_class):
        """测试 API 凭证验证（成功）"""
        # Mock Client
        mock_client = Mock()
        mock_client_class.return_value = mock_client

        # Mock 成功的搜索
        mock_response = Mock()
        mock_candidate = Mock()
        mock_grounding_metadata = Mock()
        mock_grounding_metadata.grounding_chunks = []
        mock_candidate.grounding_metadata = mock_grounding_metadata
        mock_response.candidates = [mock_candidate]

        mock_client.models.generate_content.return_value = mock_response

        # 测试
        tool = GoogleSearchGroundingTool(api_key=self.api_key)
        is_valid = tool.validate_api_credentials()

        # 验证
        self.assertTrue(is_valid)

    # TC-4V2-14: 空搜索结果处理
    @patch('google.genai.Client')
    def test_empty_search_results(self, mock_client_class):
        """测试空搜索结果处理"""
        # Mock Client
        mock_client = Mock()
        mock_client_class.return_value = mock_client

        # Mock 空结果
        mock_response = Mock()
        mock_candidate = Mock()
        mock_grounding_metadata = Mock()
        mock_grounding_metadata.grounding_chunks = []  # 空列表
        mock_candidate.grounding_metadata = mock_grounding_metadata
        mock_response.candidates = [mock_candidate]

        mock_client.models.generate_content.return_value = mock_response

        # 测试
        tool = GoogleSearchGroundingTool(api_key=self.api_key)
        result = tool.search_articles("nonexistent query")

        # 验证
        self.assertEqual(result['status'], 'success')
        self.assertEqual(len(result['articles']), 0)
        self.assertEqual(result['total_results'], 0)


if __name__ == '__main__':
    # 运行测试
    unittest.main(verbosity=2)
