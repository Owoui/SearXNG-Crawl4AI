# Sear-Crawl4AI

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

[中文](README.md) | English

## Introduction

Sear-Crawl4AI is an open-source search and crawling tool based on SearXNG and Crawl4AI, serving as an open-source alternative to Tavily. It provides similar search and web content extraction capabilities while being fully open-source and customizable.

Key Features:
- Search results retrieval through SearXNG search engine
- Web content crawling and processing using Crawl4AI
- Clean RESTful API interface
- Customizable search engine and crawling parameters

## Installation

### Prerequisites

- Python 3.8+
- SearXNG instance (local or remote)
- Playwright browser (installation script handles automatically)

### Installation Steps

1. Clone the repository
```bash
git clone https://github.com/yourusername/sear-crawl4AI-plugin.git
cd sear-crawl4AI-plugin
```

2. Install dependencies
```bash
pip install -r requirements.txt
```

3. Configure environment variables
```bash
cp .env.example .env
# Edit .env file and modify configurations as needed
```

## Usage

### Start the Service

```bash
python main.py
```

Service runs by default at `http://0.0.0.0:3000`

### API Endpoints

#### Search Endpoint

```
POST /search
```

Request body:
```json
{
  "query": "search keywords",
  "limit": 10,
  "disabled_engines": "wikipedia__general,currency__general",
  "enabled_engines": "baidu__general"
}
```

Parameters:
- `query`: Search query string (required)
- `limit`: Maximum number of results to return, default is 10
- `disabled_engines`: List of disabled search engines, comma-separated
- `enabled_engines`: List of enabled search engines, comma-separated

Response:
```json
{
  "content": "Crawled web content...",
  "success_count": 8,
  "failed_urls": ["https://example.com/failed1", "https://example.com/failed2"]
}
```

## Deployment Notes

When deploying SearXNG, pay special attention to the following configuration:

1. Modify the SearXNG settings.yml configuration file:
   - Add or modify formats configuration in the `search` section:
   ```yaml
   search:
     formats:
       - html
       - json
   ```
   This configuration ensures SearXNG returns JSON format search results, which is necessary for the Sear-Crawl4AI plugin to function properly.

## Configuration Options

The following parameters can be configured through the `.env` file:

```
# SearXNG Configuration
SEARXNG_HOST=localhost
SEARXNG_PORT=8080
SEARXNG_BASE_PATH=/search

# API Service Configuration
API_HOST=0.0.0.0
API_PORT=3000

# Crawler Configuration
DEFAULT_SEARCH_LIMIT=10
CONTENT_FILTER_THRESHOLD=0.6
WORD_COUNT_THRESHOLD=10

# Search Engine Configuration
DISABLED_ENGINES=wikipedia__general,currency__general,...
ENABLED_ENGINES=baidu__general
```

## Development

### Project Structure

```
.
├── .env.example        # Environment variables example file
├── config.py           # Configuration loading module
├── crawler.py          # Crawler functionality module
├── logger.py           # Logging module
├── main.py             # Main program and API endpoints
├── requirements.txt    # Dependencies list
└── README.md           # Project documentation
```

### Extending Functionality

To extend functionality, you can modify the following files:

- `crawler.py`: Add new crawling strategies or content processing methods
- `main.py`: Add new API endpoints
- `config.py`: Add new configuration parameters

## License

[MIT](LICENSE)

## Acknowledgments

- [SearXNG](https://github.com/searxng/searxng) - Privacy-respecting meta search engine
- [Crawl4AI](https://github.com/crawl4ai/crawl4ai) - Web crawling library for AI
- [FastAPI](https://fastapi.tiangolo.com/) - Modern, fast web framework
