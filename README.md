# SearCrawl

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

中文 | [English](README_EN.md)

## 简介

SearCrawl 是一个基于 SearXNG 和 Crawl4AI 的开源搜索和爬取工具，可作为 Tavily 的开源替代品。它提供了类似的搜索和网页内容提取功能，但完全开源且可自定义配置。

主要功能：
- 通过 SearXNG 搜索引擎获取搜索结果
- 使用 Crawl4AI 爬取和处理网页内容
- 提供简洁的 RESTful API 接口
- 支持自定义搜索引擎和爬取参数

## 安装

### 前提条件

- Python 3.8+
- SearXNG 实例（本地或远程）
- Playwright 浏览器（安装脚本会自动处理）

### 安装步骤

1. 克隆仓库
```bash
git clone https://github.com/Bclound/searCrawl.git
cd searCrawl
```

2. 安装依赖
```bash
pip install -r requirements.txt
```

3. 配置环境变量
```bash
cp .env.example .env
# 编辑 .env 文件，根据需要修改配置
```

## 使用方法

### 启动服务

```bash
python main.py
```

服务默认运行在 `http://0.0.0.0:3000`

### API 接口

#### 搜索接口

```
POST /search
```

请求体：
```json
{
  "query": "搜索关键词",
  "limit": 10,
  "disabled_engines": "wikipedia__general,currency__general,wikidata__general,duckduckgo__general,google__general,lingva__general,qwant__general,startpage__general,dictzone__general,mymemory translated__general,brave__general",
  "enabled_engines": "baidu__general"
}
```

参数说明：
- `query`: 搜索查询字符串（必填）
- `limit`: 返回结果数量限制，默认为10
- `disabled_engines`: 禁用的搜索引擎列表，逗号分隔，您可以在searXNG的COOKIES中复制
- `enabled_engines`: 启用的搜索引擎列表，逗号分隔，您可以在searXNG的COOKIES中复制

响应：
```json
{
  "content": "爬取的网页内容...",
  "success_count": 8,
  "failed_urls": ["https://example.com/failed1", "https://example.com/failed2"]
}
```

## 部署注意事项

在部署SearXNG时，需要特别注意以下配置：

1. 修改SearXNG的settings.yml配置文件：
   - 在`search`部分添加或修改formats配置：
   ```yaml
   search:
     formats:
       - html
       - json
   ```
   这个配置确保SearXNG能够返回JSON格式的搜索结果，这对于Sear-Crawl4AI插件的正常工作是必需的。

## 配置选项

可以通过 `.env` 文件配置以下参数：

```
# SearXNG 配置
SEARXNG_HOST=localhost
SEARXNG_PORT=8080
SEARXNG_BASE_PATH=/search

# API 服务配置
API_HOST=0.0.0.0
API_PORT=3000

# 爬虫配置
DEFAULT_SEARCH_LIMIT=10
CONTENT_FILTER_THRESHOLD=0.6
WORD_COUNT_THRESHOLD=10

# 搜索引擎配置
DISABLED_ENGINES=wikipedia__general,currency__general,...
ENABLED_ENGINES=baidu__general
```

## 开发

### 项目结构

```
.
├── .env.example        # 环境变量示例文件
├── config.py           # 配置加载模块
├── crawler.py          # 爬虫功能模块
├── logger.py           # 日志记录模块
├── main.py             # 主程序和API接口
├── requirements.txt    # 依赖项列表
└── README.md           # 项目说明文档
```

### 扩展功能

如需扩展功能，可以修改以下文件：

- `crawler.py`: 添加新的爬取策略或内容处理方法
- `main.py`: 添加新的API端点
- `config.py`: 添加新的配置参数

## 许可证

[MIT](LICENSE)

## 致谢

- [SearXNG](https://github.com/searxng/searxng) - 隐私友好的元搜索引擎
- [Crawl4AI](https://github.com/crawl4ai/crawl4ai) - 用于AI的网页爬取库
- [FastAPI](https://fastapi.tiangolo.com/) - 现代、快速的Web框架
