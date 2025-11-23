"""
Unit Tests for Content Extraction Tool

測試 ContentExtractor 的各種功能與錯誤處理。

Author: Ray 張瑞涵
Date: 2025-11-23
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import requests

from src.tools.content_extractor import ContentExtractor, extract_content


class TestContentExtractor:
    """ContentExtractor 類的測試集"""

    def test_init_default_params(self):
        """測試預設參數初始化"""
        extractor = ContentExtractor()

        assert extractor.timeout == 30
        assert extractor.max_retries == 3
        assert extractor.user_agent == ContentExtractor.DEFAULT_USER_AGENT
        assert extractor._session is not None

    def test_init_custom_params(self):
        """測試自定義參數初始化"""
        custom_ua = "CustomBot/1.0"
        extractor = ContentExtractor(timeout=60, max_retries=5, user_agent=custom_ua)

        assert extractor.timeout == 60
        assert extractor.max_retries == 5
        assert extractor.user_agent == custom_ua

    def test_validate_url_valid(self):
        """測試驗證有效的 URL"""
        extractor = ContentExtractor()

        # 這些 URL 都應該通過驗證
        valid_urls = [
            "https://example.com",
            "http://example.com/page",
            "https://example.com/path/to/article",
            "https://sub.domain.example.com"
        ]

        for url in valid_urls:
            assert extractor._validate_url(url) is True

    def test_validate_url_invalid(self):
        """測試驗證無效的 URL"""
        extractor = ContentExtractor()

        # 這些 URL 都應該拋出 ValueError
        invalid_urls = [
            "",
            "not-a-url",
            "ftp://example.com",  # 不支援的協議
            "example.com",         # 缺少協議
            None
        ]

        for url in invalid_urls:
            with pytest.raises(ValueError):
                extractor._validate_url(url)

    @patch('src.tools.content_extractor.requests.Session.get')
    def test_fetch_html_success(self, mock_get):
        """測試成功抓取 HTML"""
        # 模擬成功的 HTTP 回應
        mock_response = Mock()
        mock_response.text = "<html><body>Test Content</body></html>"
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        extractor = ContentExtractor()
        html = extractor._fetch_html("https://example.com")

        assert html == "<html><body>Test Content</body></html>"
        mock_get.assert_called_once()

    @patch('src.tools.content_extractor.requests.Session.get')
    def test_fetch_html_404_error(self, mock_get):
        """測試處理 404 錯誤"""
        # 模擬 404 錯誤
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.raise_for_status.side_effect = requests.HTTPError("404 Not Found")
        mock_get.return_value = mock_response

        extractor = ContentExtractor()

        with pytest.raises(requests.HTTPError):
            extractor._fetch_html("https://example.com/not-found")

    @patch('src.tools.content_extractor.requests.Session.get')
    def test_fetch_html_timeout(self, mock_get):
        """測試處理超時"""
        # 模擬超時
        mock_get.side_effect = requests.Timeout("Connection timeout")

        extractor = ContentExtractor(timeout=1)

        with pytest.raises(requests.Timeout):
            extractor._fetch_html("https://example.com")

    @patch('src.tools.content_extractor.trafilatura.extract')
    @patch('src.tools.content_extractor.trafilatura.extract_metadata')
    def test_extract_with_trafilatura_success(self, mock_metadata, mock_extract):
        """測試使用 trafilatura 成功提取內容"""
        # 模擬 trafilatura 的回應（需要至少 50 字元）
        long_content = "This is the extracted content from the article. " * 2  # 至少 50 字元
        mock_extract.side_effect = [
            long_content,  # 純文本
            f"<p>{long_content}</p>"  # HTML
        ]

        mock_meta = Mock()
        mock_meta.title = "Test Article"
        mock_meta.author = "Test Author"
        mock_meta.date = "2025-11-23"
        mock_meta.language = "en"
        mock_metadata.return_value = mock_meta

        extractor = ContentExtractor()
        result = extractor._extract_with_trafilatura(
            "<html>...</html>",
            "https://example.com"
        )

        assert result["content"] == long_content.strip()  # 代碼會 strip
        assert result["title"] == "Test Article"
        assert result["author"] == "Test Author"
        assert result["published_date"] == "2025-11-23"
        assert result["language"] == "en"

    @patch('src.tools.content_extractor.trafilatura.extract')
    def test_extract_with_trafilatura_no_content(self, mock_extract):
        """測試 trafilatura 無法提取內容的情況"""
        # 模擬 trafilatura 返回 None
        mock_extract.return_value = None

        extractor = ContentExtractor()

        with pytest.raises(ValueError, match="No substantial content"):
            extractor._extract_with_trafilatura(
                "<html>...</html>",
                "https://example.com"
            )

    def test_extract_with_beautifulsoup_success(self):
        """測試使用 BeautifulSoup 成功提取內容"""
        html = """
        <html>
            <head><title>Test Article</title></head>
            <body>
                <article>
                    <h1>Article Title</h1>
                    <p>This is the first paragraph.</p>
                    <p>This is the second paragraph.</p>
                </article>
            </body>
        </html>
        """

        extractor = ContentExtractor()
        result = extractor._extract_with_beautifulsoup(html)

        assert "Article Title" in result["content"]
        assert "first paragraph" in result["content"]
        assert "second paragraph" in result["content"]
        assert result["title"] == "Test Article"

    def test_extract_with_beautifulsoup_no_content(self):
        """測試 BeautifulSoup 無法提取內容"""
        html = "<html><body></body></html>"

        extractor = ContentExtractor()

        with pytest.raises(ValueError, match="Insufficient content"):
            extractor._extract_with_beautifulsoup(html)

    @patch('src.tools.content_extractor.ContentExtractor._fetch_html')
    @patch('src.tools.content_extractor.ContentExtractor._extract_with_trafilatura')
    def test_extract_success(self, mock_trafilatura, mock_fetch):
        """測試完整的提取流程 - 成功情況"""
        # 模擬 HTTP 抓取
        mock_fetch.return_value = "<html>...</html>"

        # 模擬 trafilatura 提取
        mock_trafilatura.return_value = {
            "content": "Article content here.",
            "content_html": "<p>Article content here.</p>",
            "title": "Test Article",
            "author": "Author Name",
            "published_date": "2025-11-23",
            "language": "en",
            "images": ["https://example.com/image.jpg"]
        }

        extractor = ContentExtractor()
        result = extractor.extract("https://example.com/article")

        assert result["status"] == "success"
        assert result["url"] == "https://example.com/article"
        assert result["title"] == "Test Article"
        assert result["author"] == "Author Name"
        assert result["content"] == "Article content here."
        assert result["word_count"] == 3  # "Article content here."
        assert result["extraction_method"] == "trafilatura"
        assert "extraction_time" in result

    @patch('src.tools.content_extractor.ContentExtractor._fetch_html')
    @patch('src.tools.content_extractor.ContentExtractor._extract_with_trafilatura')
    @patch('src.tools.content_extractor.ContentExtractor._extract_with_beautifulsoup')
    def test_extract_fallback_to_beautifulsoup(self, mock_bs, mock_trafilatura, mock_fetch):
        """測試提取失敗時降級使用 BeautifulSoup"""
        # 模擬 HTTP 抓取成功
        mock_fetch.return_value = "<html>...</html>"

        # 模擬 trafilatura 失敗
        mock_trafilatura.side_effect = ValueError("Extraction failed")

        # 模擬 BeautifulSoup 成功
        mock_bs.return_value = {
            "content": "Fallback content",
            "content_html": None,
            "title": "Fallback Title",
            "author": None,
            "published_date": None,
            "language": None,
            "images": []
        }

        extractor = ContentExtractor()
        result = extractor.extract("https://example.com/article")

        assert result["status"] == "success"
        assert result["extraction_method"] == "beautifulsoup"
        assert result["content"] == "Fallback content"
        mock_trafilatura.assert_called_once()
        mock_bs.assert_called_once()

    @patch('src.tools.content_extractor.ContentExtractor._fetch_html')
    def test_extract_http_404_error(self, mock_fetch):
        """測試處理 HTTP 404 錯誤"""
        # 模擬 404 錯誤
        mock_response = Mock()
        mock_response.status_code = 404
        http_error = requests.HTTPError("404 Not Found")
        http_error.response = mock_response
        mock_fetch.side_effect = http_error

        extractor = ContentExtractor()
        result = extractor.extract("https://example.com/not-found")

        assert result["status"] == "error"
        assert "404" in result["error_message"]
        assert result["url"] == "https://example.com/not-found"

    @patch('src.tools.content_extractor.ContentExtractor._fetch_html')
    def test_extract_timeout_error(self, mock_fetch):
        """測試處理超時錯誤"""
        mock_fetch.side_effect = requests.Timeout("Connection timeout")

        extractor = ContentExtractor()
        result = extractor.extract("https://example.com")

        assert result["status"] == "error"
        assert "timeout" in result["error_message"].lower()

    def test_extract_invalid_url(self):
        """測試處理無效 URL"""
        extractor = ContentExtractor()
        result = extractor.extract("not-a-url")

        assert result["status"] == "error"
        assert "Invalid URL" in result["error_message"]

    @patch('src.tools.content_extractor.ContentExtractor.extract')
    def test_extract_batch_success(self, mock_extract):
        """測試批量提取 - 成功情況"""
        # 模擬 extract 方法返回成功結果
        mock_extract.side_effect = [
            {"status": "success", "url": "https://example.com/1", "content": "Content 1"},
            {"status": "success", "url": "https://example.com/2", "content": "Content 2"},
            {"status": "success", "url": "https://example.com/3", "content": "Content 3"}
        ]

        extractor = ContentExtractor()
        urls = [
            "https://example.com/1",
            "https://example.com/2",
            "https://example.com/3"
        ]

        results = extractor.extract_batch(urls)

        assert len(results) == 3
        assert all(r["status"] == "success" for r in results)
        assert mock_extract.call_count == 3

    @patch('src.tools.content_extractor.ContentExtractor.extract')
    def test_extract_batch_mixed_results(self, mock_extract):
        """測試批量提取 - 成功與失敗混合"""
        # 模擬部分成功、部分失敗
        mock_extract.side_effect = [
            {"status": "success", "url": "https://example.com/1", "content": "Content 1"},
            {"status": "error", "url": "https://example.com/2", "error_message": "404"},
            {"status": "success", "url": "https://example.com/3", "content": "Content 3"}
        ]

        extractor = ContentExtractor()
        urls = ["https://example.com/1", "https://example.com/2", "https://example.com/3"]

        results = extractor.extract_batch(urls)

        assert len(results) == 3
        assert results[0]["status"] == "success"
        assert results[1]["status"] == "error"
        assert results[2]["status"] == "success"

    def test_extract_images_from_html(self):
        """測試從 HTML 提取圖片"""
        html = """
        <div>
            <img src="https://example.com/image1.jpg" alt="Image 1">
            <img src="https://example.com/image2.png" alt="Image 2">
            <img src="relative/path.jpg" alt="Relative">
        </div>
        """

        extractor = ContentExtractor()
        images = extractor._extract_images_from_html(html)

        assert len(images) == 2  # 只有 HTTP 開頭的圖片
        assert "https://example.com/image1.jpg" in images
        assert "https://example.com/image2.png" in images

    def test_extract_images_limit(self):
        """測試圖片提取數量限制"""
        # 創建包含 10 張圖片的 HTML
        html = "<div>" + "".join([
            f'<img src="https://example.com/image{i}.jpg">' for i in range(10)
        ]) + "</div>"

        extractor = ContentExtractor()
        images = extractor._extract_images_from_html(html)

        # 最多返回 5 張圖片
        assert len(images) == 5


class TestConvenienceFunction:
    """測試便捷函式"""

    @patch('src.tools.content_extractor.ContentExtractor.extract')
    def test_extract_content_function(self, mock_extract):
        """測試 extract_content 便捷函式"""
        mock_extract.return_value = {
            "status": "success",
            "title": "Test Article"
        }

        result = extract_content("https://example.com")

        assert result["status"] == "success"
        assert result["title"] == "Test Article"
        mock_extract.assert_called_once()

    @patch('src.tools.content_extractor.ContentExtractor.__init__')
    @patch('src.tools.content_extractor.ContentExtractor.extract')
    def test_extract_content_with_kwargs(self, mock_extract, mock_init):
        """測試 extract_content 傳遞額外參數"""
        mock_init.return_value = None
        mock_extract.return_value = {"status": "success"}

        extract_content("https://example.com", timeout=60, max_retries=5)

        # 驗證參數被正確傳遞
        mock_init.assert_called_once_with(timeout=60, max_retries=5)


class TestWordCount:
    """測試字數統計"""

    @patch('src.tools.content_extractor.ContentExtractor._fetch_html')
    @patch('src.tools.content_extractor.ContentExtractor._extract_with_trafilatura')
    def test_word_count_english(self, mock_trafilatura, mock_fetch):
        """測試英文文章字數統計"""
        mock_fetch.return_value = "<html>...</html>"
        mock_trafilatura.return_value = {
            "content": "This is a test article with ten words here today.",
            "content_html": None,
            "title": "Test",
            "author": None,
            "published_date": None,
            "language": "en",
            "images": []
        }

        extractor = ContentExtractor()
        result = extractor.extract("https://example.com")

        assert result["word_count"] == 10

    @patch('src.tools.content_extractor.ContentExtractor._fetch_html')
    @patch('src.tools.content_extractor.ContentExtractor._extract_with_trafilatura')
    def test_word_count_empty_content(self, mock_trafilatura, mock_fetch):
        """測試空內容的字數統計"""
        mock_fetch.return_value = "<html>...</html>"
        mock_trafilatura.return_value = {
            "content": "",
            "content_html": None,
            "title": "Test",
            "author": None,
            "published_date": None,
            "language": "en",
            "images": []
        }

        extractor = ContentExtractor()
        result = extractor.extract("https://example.com")

        assert result["word_count"] == 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
