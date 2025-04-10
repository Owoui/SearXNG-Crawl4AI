# -*- coding: utf-8 -*-
"""
爬虫模块 - 提供网页爬取和内容处理功能

This module provides web crawling and content processing functionality.
It encapsulates the AsyncWebCrawler from crawl4ai library and provides
high-level methods for crawling web pages and processing their content.
"""

from typing import List, Dict, Any, Optional, Tuple
from crawl4ai import (
    AsyncWebCrawler,
    BrowserConfig,
    CrawlerRunConfig,
    CacheMode,
    CrawlerMonitor,
    DisplayMode
)
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator
from crawl4ai.content_filter_strategy import PruningContentFilter
import markdown
from bs4 import BeautifulSoup
import re
import http.client
from codecs import encode
import json
from fastapi import HTTPException

# 导入配置和日志模块
from config import (
    SEARXNG_HOST,
    SEARXNG_PORT,
    SEARXNG_BASE_PATH,
    DISABLED_ENGINES,
    ENABLED_ENGINES,
    CONTENT_FILTER_THRESHOLD,
    WORD_COUNT_THRESHOLD
)
import logger


class WebCrawler:
    """网页爬虫类，封装了网页爬取和内容处理的功能"""

    def __init__(self):
        """初始化爬虫实例"""
        self.crawler = None
        logger.info("初始化WebCrawler实例")

    async def initialize(self) -> None:
        """初始化AsyncWebCrawler实例

        必须在使用爬虫前调用此方法
        """
        # 配置浏览器
        browser_config = BrowserConfig(headless=True, verbose=True)
        # 初始化爬虫
        self.crawler = await AsyncWebCrawler(config=browser_config).__aenter__()
        logger.info("AsyncWebCrawler初始化完成")

    async def close(self) -> None:
        """关闭爬虫实例，释放资源"""
        if self.crawler:
            await self.crawler.__aexit__(None, None, None)
            logger.info("AsyncWebCrawler已关闭")

    @staticmethod
    def markdown_to_text_regex(markdown_str: str) -> str:
        """使用正则表达式将Markdown文本转换为纯文本

        Args:
            markdown_str: Markdown格式的文本

        Returns:
            str: 转换后的纯文本
        """
        # 移除标题符号
        text = re.sub(r'#+\s*', '', markdown_str)

        # 移除链接和图片
        text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)

        # 移除粗体、斜体等强调符号
        text = re.sub(r'(\*\*|__)(.*?)\1', r'\2', text)
        text = re.sub(r'(\*|_)(.*?)\1', r'\2', text)

        # 移除列表符号
        text = re.sub(r'^[\*\-\+]\s*', '', text, flags=re.MULTILINE)

        # 移除代码块
        text = re.sub(r'`{3}.*?`{3}', '', text, flags=re.DOTALL)
        text = re.sub(r'`(.*?)`', r'\1', text)

        # 移除引用块
        text = re.sub(r'^>\s*', '', text, flags=re.MULTILINE)

        return text.strip()

    @staticmethod
    def markdown_to_text(markdown_str: str) -> str:
        """使用markdown和BeautifulSoup库将Markdown文本转换为纯文本

        Args:
            markdown_str: Markdown格式的文本

        Returns:
            str: 转换后的纯文本
        """
        html = markdown.markdown(markdown_str, extensions=['fenced_code'])
        # 用 BeautifulSoup 提取纯文本
        soup = BeautifulSoup(html, "html.parser")

        text = soup.get_text(separator="\n")  # 保留段落换行

        # 清理多余空行
        cleaned_text = "\n".join([line.strip()
                             for line in text.split("\n") if line.strip()])

        return cleaned_text

    @staticmethod
    def make_searxng_request(query: str, limit: int = 10,
                           disabled_engines: str = DISABLED_ENGINES,
                           enabled_engines: str = ENABLED_ENGINES) -> dict:
        """向SearXNG发送搜索请求

        Args:
            query: 搜索查询字符串
            limit: 返回结果数量限制
            disabled_engines: 禁用的搜索引擎列表，逗号分隔
            enabled_engines: 启用的搜索引擎列表，逗号分隔

        Returns:
            dict: SearXNG返回的搜索结果

        Raises:
            Exception: 当请求失败时抛出异常
        """
        try:
            conn = http.client.HTTPConnection(SEARXNG_HOST, SEARXNG_PORT)
            dataList = []
            boundary = 'wL36Yn8afVp8Ag7AmP8qZ0SA4n1v9T'

            form_data = {
                'q': query,
                'format': 'json',
                'language': 'zh',
                'time_range': 'week',
                'safesearch': '2',
                'pageno': '1',
                'category_general': '1'
            }

            # 添加表单字段
            for key, value in form_data.items():
                dataList.append(encode('--' + boundary))
                dataList.append(encode(f'Content-Disposition: form-data; name={key};'))
                dataList.append(encode('Content-Type: {}'.format('text/plain')))
                dataList.append(encode(''))
                dataList.append(encode(str(value)))

            dataList.append(encode('--'+boundary+'--'))
            dataList.append(encode(''))
            body = b'\r\n'.join(dataList)

            headers = {
                'Cookie': f'disabled_engines={disabled_engines};enabled_engines={enabled_engines};method=POST',
                'User-Agent': 'Sear-Crawl4AI/1.0.0',
                'Accept': '*/*',
                'Host': f'{SEARXNG_HOST}:{SEARXNG_PORT}',
                'Connection': 'keep-alive',
                'Content-Type': f'multipart/form-data; boundary={boundary}'
            }

            logger.info(f"向SearXNG发送搜索请求: {query}")
            conn.request("POST", SEARXNG_BASE_PATH, body, headers)
            res = conn.getresponse()
            data = res.read()
            return json.loads(data.decode("utf-8"))  # 解析 JSON 字符串为字典
        except Exception as e:
            logger.error(f"SearXNG请求失败: {str(e)}")
            raise Exception(f"搜索请求失败: {str(e)}")

    async def crawl_urls(self, urls: List[str], instruction: str) -> Dict[str, Any]:
        """爬取多个URL并处理内容

        Args:
            urls: 要爬取的URL列表
            instruction: 爬取指令，通常是搜索查询

        Returns:
            Dict[str, Any]: 包含处理后内容、成功数量和失败URL的字典

        Raises:
            HTTPException: 当所有URL爬取均失败时抛出异常
        """
        try:
            # 检查爬虫是否已初始化
            if not self.crawler:
                logger.warning("爬虫未初始化，正在自动初始化")
                await self.initialize()

            # 配置Markdown生成器
            md_generator = DefaultMarkdownGenerator(
                content_filter=PruningContentFilter(threshold=CONTENT_FILTER_THRESHOLD),
                options={
                    "ignore_links": True,
                    "ignore_images": True,
                    "escape_html": False,
                }
            )

            # 配置爬虫运行参数
            run_config = CrawlerRunConfig(
                word_count_threshold=WORD_COUNT_THRESHOLD,
                exclude_external_links=True,    # 移除外部链接
                remove_overlay_elements=True,   # 移除弹窗/模态框
                excluded_tags=['img', 'header', 'footer', 'iframe', 'nav'],      # 排除图片标签
                process_iframes=True,           # 处理iframe
                markdown_generator=md_generator,
                cache_mode=CacheMode.BYPASS     # 不使用缓存
            )

            logger.info(f"开始爬取URLs: {', '.join(urls)}")
            results = await self.crawler.arun_many(urls=urls, config=run_config)

            # 创建一个列表来存储所有成功URL的爬取结果
            all_results = []
            failed_urls = []
            retry_urls = []

            # 第一次爬取处理
            for i, result in enumerate(results):
                try:
                    if result is None:
                        logger.debug(f"URL爬取结果为None: {urls[i]}")
                        retry_urls.append(urls[i])
                        continue

                    if not hasattr(result, 'success'):
                        logger.debug(f"URL爬取结果缺少success属性: {urls[i]}")
                        retry_urls.append(urls[i])
                        continue

                    if result.success:
                        if not hasattr(result, 'markdown') or not hasattr(result.markdown, 'fit_markdown'):
                            logger.debug(f"URL爬取结果缺少markdown内容: {urls[i]}")
                            retry_urls.append(urls[i])
                            continue

                        # 将成功的结果的markdown内容添加到列表中
                        result_with_source = result.markdown.fit_markdown + '\n\n'
                        all_results.append(result_with_source)
                        logger.info(f"成功爬取URL: {urls[i]}")
                    else:
                        logger.debug(f"URL爬取失败: {urls[i]}")
                        retry_urls.append(urls[i])
                except Exception as e:
                    # 记录需要重试的URL
                    retry_urls.append(urls[i])
                    error_msg = str(e)
                    logger.warning(f"URL第一次爬取失败: {urls[i]}, 错误信息: {error_msg}")

            # 如果有需要重试的URL，进行第二次爬取
            if retry_urls:
                logger.info(f"重试失败的URLs: {', '.join(retry_urls)}")
                retry_results = await self.crawler.arun_many(urls=retry_urls, config=run_config)

                for i, result in enumerate(retry_results):
                    try:
                        if result is None:
                            logger.debug(f"重试URL爬取结果为None: {retry_urls[i]}")
                            failed_urls.append(retry_urls[i])
                            continue

                        if not hasattr(result, 'success'):
                            logger.debug(f"重试URL爬取结果缺少success属性: {retry_urls[i]}")
                            failed_urls.append(retry_urls[i])
                            continue

                        if result.success:
                            if not hasattr(result, 'markdown') or not hasattr(result.markdown, 'fit_markdown'):
                                logger.debug(f"重试URL爬取结果缺少markdown内容: {retry_urls[i]}")
                                failed_urls.append(retry_urls[i])
                                continue

                            # 将重试成功的结果添加到列表中
                            result_with_source = result.markdown.fit_markdown + '\n\n'
                            all_results.append(result_with_source)
                            logger.info(f"重试成功爬取URL: {retry_urls[i]}")
                        else:
                            logger.debug(f"重试URL爬取仍然失败: {retry_urls[i]}")
                            failed_urls.append(retry_urls[i])
                    except Exception as e:
                        # 记录最终失败的URL
                        failed_urls.append(retry_urls[i])
                        error_msg = str(e)
                        logger.error(f"URL第二次爬取失败: {retry_urls[i]}, 错误信息: {error_msg}")

            if not all_results:
                logger.error("所有URL爬取均失败")
                raise HTTPException(status_code=500, detail="所有URL爬取均失败")

            # 将所有成功结果用分隔符连接成一个完整的字符串
            combined_content = '\n\n==========\n\n'.join(all_results)

            # 转换为纯文本
            plain_text = self.markdown_to_text_regex(self.markdown_to_text(combined_content))

            response = {
                "content": plain_text,
                "success_count": len(all_results),
                "failed_urls": failed_urls
            }

            logger.info(f"爬取完成，成功: {len(all_results)}，失败: {len(failed_urls)}")
            return response
        except Exception as e:
            logger.error(f"爬取过程发生异常: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))
