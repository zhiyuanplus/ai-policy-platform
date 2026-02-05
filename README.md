# AI 政策情报平台 (AIRP)

AI Regulatory & Policy (AIRP) Platform - An automated platform for tracking, analyzing, and visualizing AI-related government policies.

## 功能概览 (Features)

This project implements a complete pipeline for monitoring and analyzing AI policies, focusing on sources from China.

### 🔍 数据采集 (Data Scraping)
- Scrapers for three major Chinese regulatory bodies:
  - **MIIT (工信部)**: `miit_scraper.py`
  - **CAC (网信办)**: `cac_scraper_v3.py`
  - **TC260 (全国信安标委)**: `tc260_scraper.py`
- The scrapers are designed to fetch all recent documents, with AI-related filtering handled centrally.

### ⚙️ 数据处理与分析 (Data Processing & Analysis)
- All processing logic is centralized in `main.py` for efficiency and consistency.
- **智能去重 (Intelligent De-duplication)**: Identifies and consolidates multiple documents (e.g., announcements, full texts, Q&As) related to the same core policy into a single entry.
- **AI政策筛选 (AI Policy Filtering)**: A scoring mechanism (`ai_score > 4`) filters for policies that are highly relevant to Artificial Intelligence, using a refined list of keywords.
- **多维度量化 (Multi-dimensional Quantification)**: The `ai_analysis.py` module enriches each policy with:
  - **监管态度评分 (Regulatory Score)**: A 1-10 score indicating the government's stance (innovation vs. regulation).
  - **涉及领域 (Identified Domains)**: Tags like "Data Security", "Generative AI", etc.
  - **法律效力层级 (Enforcement Level)**: Classifies documents into categories like "Laws & Regulations", "Administrative Rules", etc.

### 📊 交互式看板 (Interactive Dashboard)
- A web-based dashboard built with Streamlit (`dashboard.py`).
- **多语言支持 (Multi-language)**: Fully bilingual interface (Chinese/English) with a real-time language switcher.
- **核心图表 (Core Visualizations)**:
  - **监管情绪走势图 (Regulatory Sentiment Trend)**: Tracks the average regulatory score over time (Year/Quarter/Month).
  - **各部委发布权重 (Policy Distribution by Department)**: A pie chart showing the proportion of policies from each government body.
  - **政策法律效力层级 (Policy Legal Force Level)**: A bar chart showing the distribution of policies by their legal authority.
- **政策数据详情 (Policy Data Details)**: A detailed, sortable, and searchable table of all filtered policies, with automatic text wrapping for long titles.
- **法律法规参考 (Legal Reference)**: A quick reference section with links to the full text of key AI-related laws and regulations in China.

## 快速开始 (Quick Start)

### 1. 环境准备 (Prerequisites)
Ensure you have Python 3 installed. Then, install the required packages:
```bash
pip3 install -r requirements.txt
```

### 2. 运行流程 (Workflow)

The workflow is designed to be run sequentially.

**Step 1: (Optional) Scrape for New Data**
If you need to fetch the latest policies, run the scraper scripts. Each script saves its findings to a `*_all_policies.csv` file.
```bash
python3 cac_scraper_v3.py
python3 miit_scraper.py
python3 tc260_scraper.py
```

**Step 2: Process, Filter, and Analyze Data**
This is a mandatory step. It reads all `*_all_policies.csv` files, performs de-duplication and AI filtering, runs the analysis, and saves the final, clean data to `all_policies_analyzed.csv`.
```bash
python3 main.py
```

**Step 3: View the Dashboard**
Launch the interactive web dashboard.
```bash
python3 -m streamlit run dashboard.py
```

## 项目结构 (Project Structure)

```
AI_Policy_Tool/
├── main.py                    # Main data processing and analysis pipeline
├── cac_scraper_v3.py          # Scraper for CAC
├── miit_scraper.py            # Scraper for MIIT
├── tc260_scraper.py           # Scraper for TC260
├── ai_analysis.py             # AI analysis and quantification module
├── dashboard.py               # Streamlit interactive dashboard
├── AIPolicyTool_PRD.md        # Product Requirements Document
├── DATA_PROCESSING_LOGIC.md   # Details on data cleaning and analysis logic
├── requirements.txt           # Python package dependencies
└── README.md                  # This file
```

## 输出文件 (Output Files)

- `*_all_policies.csv`: Raw, unfiltered data scraped from each source.
- `all_policies_analyzed.csv`: The final, cleaned, de-duplicated, filtered, and analyzed data ready for the dashboard.
- `metadata.json`: Contains metadata, such as the latest date across all scraped policies.
