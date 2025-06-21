# Job Data Collect 🧠📊

This repository contains two Python-based crawlers used for collecting company-related data from JobPlanet and Naver News API.

## Contents

### 1. JobPlanet Company Review Crawler
- Crawls company ratings and reviews using Selenium + BeautifulSoup
- Extracts detailed statistics and saves as CSV
- Handles errors, saves progress, and supports 10K+ companies

📂 Folder: `jobplanet_crawler/`

### 2. Naver News API Crawler
- Fetches latest news articles using Naver OpenAPI
- Cleans HTML tags, saves headline, link, description, and date
- Supports CSV input for company names

📂 Folder: `naver_news_crawler/`

## Setup

Install dependencies:

```bash
pip install -r requirements.txt
