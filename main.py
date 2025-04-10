# -*- coding: utf-8 -*-
"""
Sear-Crawl4AI - 一个基于SearXNG和Crawl4AI的开源搜索和爬取工具

Sear-Crawl4AI is an open-source alternative to Tavily, providing search and crawling
capabilities using SearXNG as the search engine and Crawl4AI for web crawling.

此项目可以作为Tavily的开源替代品，提供类似的搜索和网页内容提取功能。
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn
import sys
import subprocess

# 导入自定义模块
from config import API_HOST, API_PORT, DEFAULT_SEARCH_LIMIT, DISABLED_ENGINES, ENABLED_ENGINES
from crawler import WebCrawler
import logger

# 初始化FastAPI应用
app = FastAPI(
    title="Sear-Crawl4AI API",
    description="一个基于SearXNG和Crawl4AI的开源搜索和爬取工具，可作为Tavily的开源替代品",
    version="1.0.0"
)

# 全局爬虫实例
crawler = None


# 请求模型定义
class SearchRequest(BaseModel):
    """搜索请求模型

    Attributes:
        query: 搜索查询字符串
        limit: 返回结果数量限制，默认为10
        disabled_engines: 禁用的搜索引擎列表，逗号分隔
        enabled_engines: 启用的搜索引擎列表，逗号分隔
    """
    query: str
    limit: int = DEFAULT_SEARCH_LIMIT
    disabled_engines: str = DISABLED_ENGINES
    enabled_engines: str = ENABLED_ENGINES


class CrawlRequest(BaseModel):
    """
    爬取请求模型

    Attributes:
        urls: 要爬取的URL列表
        instruction: 爬取指令，通常是搜索查询
    """
    urls: list[str]
    instruction: str


class CrawlRequest(BaseModel):
    """
    爬取请求模型

    Attributes:
        urls: 要爬取的URL列表
        instruction: 爬取指令，通常是搜索查询
    """
    urls: list[str]
    instruction: str


@app.on_event("startup")
async def startup_event():
    """
    应用程序启动事件处理函数

    在FastAPI应用启动时执行，负责初始化爬虫和安装必要的浏览器
    """
    global crawler

    # 配置日志级别
    logger.setup_logger("INFO")
    logger.info("Sear-Crawl4AI 服务启动中...")

    # 检查并安装浏览器
    logger.info("检查 Playwright 浏览器...")
    try:
        # 尝试安装浏览器
        subprocess.run([sys.executable, "-m", "playwright",
                       "install", "chromium"], check=True)
        logger.info("Playwright 浏览器安装成功或已存在")
    except subprocess.CalledProcessError as e:
        logger.error(f"浏览器安装失败: {e}")
        raise

    # 初始化爬虫
    crawler = WebCrawler()
    await crawler.initialize()
    logger.info("爬虫初始化完成")

    # 输出配置信息
    logger.info(f"API服务运行在: http://{API_HOST}:{API_PORT}")
    logger.info("Sear-Crawl4AI 服务启动完成")


@app.on_event("shutdown")
async def shutdown_event():
    """
    应用程序关闭事件处理函数

    在FastAPI应用关闭时执行，负责释放爬虫资源
    """
    global crawler
    if crawler:
        await crawler.close()
        logger.info("爬虫资源已释放")
    logger.info("Sear-Crawl4AI 服务已关闭")


async def crawl(request: CrawlRequest):
    """
    爬取多个URL并处理内容的API端点函数

    Args:
        request: 包含URLs和指令的爬取请求

    Returns:
        Dict: 包含处理后内容、成功数量和失败URL的字典

    Raises:
        HTTPException: 当爬取过程中发生错误时抛出异常
    """
    global crawler
    return await crawler.crawl_urls(request.urls, request.instruction)


@app.post("/search")
async def search(request: SearchRequest):
    """
    搜索API端点

    接收搜索请求，调用SearXNG搜索引擎获取结果，然后爬取搜索结果页面

    Args:
        request: 搜索请求对象，包含查询字符串和配置参数

    Returns:
        Dict: 包含处理后内容、成功数量和失败URL的字典

    Raises:
        HTTPException: 当搜索或爬取过程中发生错误时抛出异常
    """
    try:
        # 添加状态反馈
        logger.info(f"开始搜索: {request.query}")

        # 调用SearXNG搜索引擎
        response = WebCrawler.make_searxng_request(
            query=request.query,
            limit=request.limit,
            disabled_engines=request.disabled_engines,
            enabled_engines=request.enabled_engines
        )

        # 检查搜索结果
        results = response.get("results", [])
        if not results:
            logger.warning("未找到搜索结果")
            raise HTTPException(status_code=404, detail="未找到搜索结果")

        # 限制结果数量并提取URL
        urls = [result["url"] for result in results[:request.limit] if "url" in result]
        if not urls:
            logger.warning("未找到有效的URL")
            raise HTTPException(status_code=404, detail="未找到有效的URL")

        logger.info(f"找到 {len(urls)} 个URL，开始爬取")

        # 调用爬取函数处理URL
        return await crawl(CrawlRequest(urls=urls, instruction=request.query))
    except HTTPException:
        # 直接重新抛出HTTP异常
        raise
    except Exception as e:
        # 记录其他异常并转换为HTTP异常
        logger.error(f"搜索过程发生异常: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    # 程序入口点
    logger.info("通过命令行启动Sear-Crawl4AI服务")
    import uvicorn
    uvicorn.run(app, host=API_HOST, port=API_PORT)
