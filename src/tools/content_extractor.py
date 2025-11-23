"""
Content Extraction Tool - 文章內容提取器

此模組提供從 URL 提取文章完整內容的功能，使用 trafilatura 作為主力提取引擎，
BeautifulSoup 作為備用方案。

主要功能：
- HTTP 內容抓取（含重試機制）
- 智能內容提取（移除廣告、導航等）
- 元數據提取（標題、作者、日期）
- 結構化輸出格式
- 批量提取支援

Author: Ray 張瑞涵
Date: 2025-11-23
"""

import time
import logging
from typing import List, Optional, Dict, Any
from urllib.parse import urlparse

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import trafilatura
from bs4 import BeautifulSoup

# 設定日誌
logger = logging.getLogger(__name__)


class ContentExtractor:
    """
    文章內容提取器

    使用 trafilatura 作為主力提取引擎，提供統一的接口。
    當 trafilatura 無法提取時，自動降級使用 BeautifulSoup 備用方案。

    Example:
        >>> extractor = ContentExtractor()
        >>> article = extractor.extract("https://example.com/article")
        >>> print(article["title"])
        "Example Article Title"
        >>> print(len(article["content"]))
        1234
    """

    DEFAULT_USER_AGENT = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )

    def __init__(
        self,
        timeout: int = 30,
        max_retries: int = 3,
        user_agent: Optional[str] = None
    ):
        """
        初始化提取器

        Args:
            timeout: HTTP 請求超時時間（秒），預設 30 秒
            max_retries: 最大重試次數，預設 3 次
            user_agent: 自定義 User-Agent，預設使用標準瀏覽器 UA
        """
        self.timeout = timeout
        self.max_retries = max_retries
        self.user_agent = user_agent or self.DEFAULT_USER_AGENT
        self._session = self._create_session()

    def _create_session(self) -> requests.Session:
        """
        創建配置好重試策略的 requests Session

        Returns:
            requests.Session: 配置好的 Session 物件
        """
        # 配置重試策略
        retry_strategy = Retry(
            total=self.max_retries,
            backoff_factor=1,  # 1, 2, 4 秒指數退避
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET", "HEAD"]
        )

        adapter = HTTPAdapter(max_retries=retry_strategy)
        session = requests.Session()
        session.mount("http://", adapter)
        session.mount("https://", adapter)

        return session

    def _validate_url(self, url: str) -> bool:
        """
        驗證 URL 格式

        Args:
            url: 要驗證的 URL

        Returns:
            bool: URL 是否有效

        Raises:
            ValueError: URL 格式無效
        """
        if not url or not isinstance(url, str):
            raise ValueError("URL must be a non-empty string")

        parsed = urlparse(url)
        if not all([parsed.scheme, parsed.netloc]):
            raise ValueError(f"Invalid URL format: {url}")

        if parsed.scheme not in ['http', 'https']:
            raise ValueError(f"URL must use http or https protocol: {url}")

        return True

    def _fetch_html(self, url: str) -> str:
        """
        抓取 URL 的 HTML 內容

        Args:
            url: 目標 URL

        Returns:
            str: HTML 內容

        Raises:
            requests.RequestException: 網路請求失敗
        """
        headers = {
            "User-Agent": self.user_agent,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9,zh-TW;q=0.8,zh;q=0.7",
            "Accept-Encoding": "gzip, deflate, br",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1"
        }

        logger.debug(f"Fetching URL: {url}")
        response = self._session.get(url, headers=headers, timeout=self.timeout)
        response.raise_for_status()

        logger.debug(f"Successfully fetched {len(response.text)} characters from {url}")
        return response.text

    def _extract_with_trafilatura(self, html: str, url: str) -> Dict[str, Any]:
        """
        使用 trafilatura 提取內容

        Args:
            html: HTML 內容
            url: 原始 URL（用於元數據提取）

        Returns:
            dict: 提取的內容與元數據

        Raises:
            ValueError: 內容提取失敗
        """
        logger.debug("Extracting content with trafilatura")

        # 提取主文本（純文本格式）
        content = trafilatura.extract(
            html,
            include_images=True,
            include_links=False,
            include_tables=False,
            output_format='txt',
            url=url,
            favor_precision=True  # 優先保證提取精確性
        )

        # 提取 HTML 格式內容（保留基本格式）
        content_html = trafilatura.extract(
            html,
            include_images=True,
            include_links=True,
            include_tables=True,
            output_format='html',
            url=url
        )

        # 提取元數據
        metadata = trafilatura.extract_metadata(html)

        if content is None or len(content.strip()) < 50:
            raise ValueError("No substantial content extracted by trafilatura")

        result = {
            "content": content.strip(),
            "content_html": content_html,
            "title": metadata.title if metadata and metadata.title else None,
            "author": metadata.author if metadata and metadata.author else None,
            "published_date": metadata.date if metadata and metadata.date else None,
            "language": metadata.language if metadata and metadata.language else None,
        }

        # 提取圖片 URL（從 HTML 格式內容中）
        if content_html:
            images = self._extract_images_from_html(content_html)
            result["images"] = images
        else:
            result["images"] = []

        logger.debug(f"Trafilatura extracted {len(content)} chars, title: {result['title']}")
        return result

    def _extract_images_from_html(self, html: str) -> List[str]:
        """
        從 HTML 中提取圖片 URL

        Args:
            html: HTML 內容

        Returns:
            List[str]: 圖片 URL 列表
        """
        soup = BeautifulSoup(html, 'lxml')
        images = []

        for img in soup.find_all('img'):
            src = img.get('src')
            if src and src.startswith('http'):
                images.append(src)

        return images[:5]  # 最多返回 5 張圖片

    def _extract_with_beautifulsoup(self, html: str) -> Dict[str, Any]:
        """
        使用 BeautifulSoup 作為備用方案提取內容

        當 trafilatura 失敗時使用此方法。

        Args:
            html: HTML 內容

        Returns:
            dict: 提取的內容（元數據可能不完整）

        Raises:
            ValueError: 內容提取失敗
        """
        logger.debug("Falling back to BeautifulSoup extraction")

        soup = BeautifulSoup(html, 'lxml')

        # 移除無關元素
        for tag in soup(['script', 'style', 'nav', 'header', 'footer', 'aside', 'iframe']):
            tag.decompose()

        # 嘗試找到主內容區塊
        content_tag = (
            soup.find('article') or
            soup.find('main') or
            soup.find(class_=['content', 'post', 'article', 'entry-content', 'post-content']) or
            soup.find(id=['content', 'main', 'article'])
        )

        if content_tag:
            content = content_tag.get_text(separator='\n', strip=True)
        elif soup.body:
            content = soup.body.get_text(separator='\n', strip=True)
        else:
            raise ValueError("No content found by BeautifulSoup")

        if len(content.strip()) < 50:
            raise ValueError("Insufficient content extracted by BeautifulSoup")

        # 提取標題
        title = None
        title_tag = soup.find('title')
        if title_tag:
            title = title_tag.get_text(strip=True)
        elif soup.find('h1'):
            title = soup.find('h1').get_text(strip=True)

        # 提取圖片
        images = []
        for img in soup.find_all('img')[:5]:
            src = img.get('src')
            if src and src.startswith('http'):
                images.append(src)

        logger.debug(f"BeautifulSoup extracted {len(content)} chars")
        return {
            "content": content.strip(),
            "content_html": None,
            "title": title,
            "author": None,
            "published_date": None,
            "language": None,
            "images": images
        }

    def extract(self, url: str) -> Dict[str, Any]:
        """
        從 URL 提取文章內容

        使用 trafilatura 作為主要方法，失敗時自動降級使用 BeautifulSoup。

        Args:
            url: 文章 URL

        Returns:
            dict: 結構化文章數據，格式如下：
                {
                    "status": "success" | "error",
                    "url": str,
                    "title": Optional[str],
                    "author": Optional[str],
                    "published_date": Optional[str],  # ISO 格式
                    "content": str,                    # 純文本
                    "content_html": Optional[str],     # HTML 格式（可選）
                    "images": List[str],               # 圖片 URL 列表
                    "word_count": int,
                    "language": Optional[str],
                    "error_message": Optional[str],
                    "extraction_time": float,          # 秒
                    "extraction_method": str           # "trafilatura" | "beautifulsoup"
                }

        Example:
            >>> extractor = ContentExtractor()
            >>> article = extractor.extract("https://techcrunch.com/...")
            >>> print(article["status"])
            "success"
            >>> print(article["title"])
            "Breaking News: ..."
        """
        start_time = time.time()

        # 初始化結果結構
        result = {
            "status": "error",
            "url": url,
            "title": None,
            "author": None,
            "published_date": None,
            "content": "",
            "content_html": None,
            "images": [],
            "word_count": 0,
            "language": None,
            "error_message": None,
            "extraction_time": 0.0,
            "extraction_method": None
        }

        try:
            # 1. 驗證 URL
            self._validate_url(url)

            # 2. 抓取 HTML
            html = self._fetch_html(url)

            # 3. 提取內容（先嘗試 trafilatura，失敗則用 BeautifulSoup）
            extraction_error = None
            try:
                extracted = self._extract_with_trafilatura(html, url)
                result["extraction_method"] = "trafilatura"
            except Exception as e:
                extraction_error = str(e)
                logger.warning(f"Trafilatura extraction failed: {e}, falling back to BeautifulSoup")
                try:
                    extracted = self._extract_with_beautifulsoup(html)
                    result["extraction_method"] = "beautifulsoup"
                except Exception as e2:
                    raise ValueError(f"Both extraction methods failed. Trafilatura: {extraction_error}, BeautifulSoup: {str(e2)}")

            # 4. 合併提取結果
            result.update(extracted)

            # 5. 計算字數
            if result["content"]:
                # 簡單的字數統計（英文按空格，中文按字元）
                words = result["content"].split()
                result["word_count"] = len(words)

            # 6. 設定成功狀態
            result["status"] = "success"
            logger.info(f"Successfully extracted content from {url} ({result['word_count']} words)")

        except ValueError as e:
            result["error_message"] = str(e)
            logger.error(f"Validation error for {url}: {e}")

        except requests.HTTPError as e:
            if e.response.status_code == 404:
                result["error_message"] = f"Page not found (404): {url}"
            elif e.response.status_code in [403, 401]:
                result["error_message"] = f"Access denied ({e.response.status_code}): {url}"
            else:
                result["error_message"] = f"HTTP error ({e.response.status_code}): {str(e)}"
            logger.error(result["error_message"])

        except requests.Timeout:
            result["error_message"] = f"Connection timeout after {self.timeout}s: {url}"
            logger.error(result["error_message"])

        except requests.RequestException as e:
            result["error_message"] = f"Network error: {str(e)}"
            logger.error(result["error_message"])

        except Exception as e:
            result["error_message"] = f"Unexpected error: {str(e)}"
            logger.exception(f"Unexpected error extracting {url}")

        finally:
            # 記錄提取時間
            result["extraction_time"] = round(time.time() - start_time, 2)

        return result

    def extract_batch(self, urls: List[str]) -> List[Dict[str, Any]]:
        """
        批量提取多個 URL（順序執行）

        Args:
            urls: URL 列表

        Returns:
            List[dict]: 結構化文章列表（失敗的返回 error 狀態）

        Example:
            >>> extractor = ContentExtractor()
            >>> urls = ["https://example.com/1", "https://example.com/2"]
            >>> results = extractor.extract_batch(urls)
            >>> len(results)
            2
            >>> all(r["status"] in ["success", "error"] for r in results)
            True
        """
        logger.info(f"Starting batch extraction for {len(urls)} URLs")

        results = []
        for i, url in enumerate(urls, 1):
            logger.info(f"Extracting {i}/{len(urls)}: {url}")
            result = self.extract(url)
            results.append(result)

            # 簡單的速率限制（避免被封鎖）
            if i < len(urls):
                time.sleep(0.5)  # 每個請求間隔 0.5 秒

        success_count = sum(1 for r in results if r["status"] == "success")
        logger.info(f"Batch extraction completed: {success_count}/{len(urls)} successful")

        return results


# Convenience function for one-off extractions
def extract_content(url: str, **kwargs) -> Dict[str, Any]:
    """
    便捷函式：從 URL 提取內容

    這是一個便捷函式，用於一次性提取單個 URL。
    如需批量提取或自定義配置，請使用 ContentExtractor 類。

    Args:
        url: 文章 URL
        **kwargs: 傳遞給 ContentExtractor 的額外參數

    Returns:
        dict: 結構化文章數據

    Example:
        >>> article = extract_content("https://example.com/article")
        >>> print(article["title"])
        "Article Title"
    """
    extractor = ContentExtractor(**kwargs)
    return extractor.extract(url)
