# -*- coding: utf-8 -*-
"""
ARPI Platform - Master Data Pipeline
Orchestrates the entire ETL and analysis process.
"""
import os
import pandas as pd
import re
import json # Import json module
from ai_analysis import PolicyAnalyzer
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Centralized AI Filtering Logic ---
AI_KEYWORDS = [
    # 核心AI术语
    "人工智能", "AI", "生成式", "大模型", "AIGC",
    # 关键技术
    "算法", "深度合成", "机器学习", "深度学习", "自然语言处理",
    # 重要概念
    "智能", "算法推荐"
]

def calculate_ai_score(row):
    """Calculates an AI relevance score for a given policy row."""
    score = 0
    title = row.get('title', '')
    text = row.get('full_text', '')
    
    if not isinstance(title, str) or not isinstance(text, str):
        return 0

    full_content = title.lower() + " " + text.lower()
    
    for keyword in AI_KEYWORDS:
        count = full_content.count(keyword.lower())
        if count > 0:
            if keyword in ["人工智能", "大模型", "生成式", "AIGC"]:
                score += count * 3
            elif keyword in ["算法", "智能", "深度合成", "机器学习", "深度学习"]:
                score += count * 2
            else:
                score += count
    return score

def unify_data():
    """Loads, unifies, de-duplicates, and filters data from all scraper CSVs.
    Returns the filtered DataFrame and the overall max publication date."""
    logging.info("--- Stage 1: Unifying & Filtering Data ---")
    source_files = {
        "cac": "cac_all_policies.csv",
        "miit": "miit_all_policies.csv",
        "tc260": "tc260_all_policies.csv"
    }
    all_dfs = []
    for source, filename in source_files.items():
        if os.path.exists(filename):
            logging.info(f"  - Loading {filename}...")
            try:
                df = pd.read_csv(filename)
                df['source'] = source
                all_dfs.append(df)
            except Exception as e:
                logging.error(f"    - Error loading {filename}: {e}")
        else:
            logging.warning(f"  - File not found: {filename}")

    if not all_dfs:
        logging.error("No data files found to unify. Halting.")
        return None, None # Return None for both df and max_date

    unified_df = pd.concat(all_dfs, ignore_index=True)
    logging.info(f"  - Total policies loaded: {len(unified_df)}")
    
    # --- Data Cleaning and Intelligent De-duplication ---
    unified_df.dropna(subset=['title'], inplace=True)
    unified_df['publication_date'] = pd.to_datetime(unified_df['publication_date'], errors='coerce')
    unified_df.dropna(subset=['publication_date'], inplace=True)
    
    for col in ['title', 'issuing_department', 'full_text']:
        if col in unified_df.columns:
            unified_df[col] = unified_df[col].astype(str).fillna('')

    # Capture overall max date before any filtering
    overall_max_date = unified_df['publication_date'].max() 
    logging.info(f"  - Overall latest policy date: {overall_max_date.strftime('%Y-%m-%d')}")

    # Helper to extract core title from 《...》
    def get_core_title(title):
        match = re.search(r'《([^》]+)》', title)
        if match:
            return match.group(1)
        return title # Fallback to full title if no marks
    
    unified_df['core_title'] = unified_df['title'].apply(get_core_title)
    unified_df['content_length'] = unified_df['full_text'].str.len()

    # Sort by core title, then date (newest first), then content length (longest first)
    unified_df.sort_values(by=['core_title', 'publication_date', 'content_length'], ascending=[True, False, False], inplace=True)
    
    # De-duplicate based on the core title, keeping the best candidate (the first one after sorting)
    num_before_dedup = len(unified_df)
    unified_df.drop_duplicates(subset=['core_title'], keep='first', inplace=True)
    num_after_dedup = len(unified_df)
    logging.info(f"  - Intelligent de-duplication: {num_before_dedup} -> {num_after_dedup} policies.")
    
    # --- AI Policy Filtering ---
    logging.info("  - Applying centralized AI filter...")
    unified_df['ai_score'] = unified_df.apply(calculate_ai_score, axis=1)
    
    ai_filtered_df = unified_df[unified_df['ai_score'] > 4].copy()
    logging.info(f"  - AI Filter Result: {len(ai_filtered_df)} / {len(unified_df)} policies identified as AI-related.")

    if ai_filtered_df.empty:
        logging.warning("No AI-related policies found after filtering. Halting.")
        return None, None # Return None for both df and max_date

    # --- Department Name Standardization ---
    def standardize_department(name):
        name = str(name)
        if '工业和信息化部' in name:
            return '中华人民共和国工业和信息化部'
        if '网信办' in name or '国家互联网信息办公室' in name:
            return '国家互联网信息办公室'
        if '市场监督管理总局' in name:
            return '国家市场监督管理总局'
        if '全国信息安全标准化技术委员会' in name:
            return '全国信息安全标准化技术委员会'
        if name == '科技司':
            return '科技司'
        if name == '办公厅':
            return '办公厅'
        return name

    ai_filtered_df['unified_department'] = ai_filtered_df['issuing_department'].apply(standardize_department)
    logging.info("  - Department names standardized.")
    
    return ai_filtered_df, overall_max_date

def analyze_data(df):
    """Applies AI analysis to the unified DataFrame."""
    if df is None:
        return None
    logging.info("--- Stage 2: Analyzing Data ---")
    analyzer = PolicyAnalyzer()
    analysis_results = [analyzer.analyze_policy(row.to_dict()) for _, row in df.iterrows()]
    analyzed_df = pd.concat([df.reset_index(drop=True), pd.DataFrame(analysis_results)], axis=1)
    logging.info("  - Analysis complete.")
    
    # Sort by publication_date from newest to oldest
    analyzed_df.sort_values(by='publication_date', ascending=False, inplace=True)
    logging.info("  - Policies sorted by publication date (newest first).")

    try:
        analyzed_df.to_csv("all_policies_analyzed.csv", index=False, encoding='utf-8-sig')
        logging.info("  - Successfully saved analyzed data to: all_policies_analyzed.csv")
    except Exception as e:
        logging.error(f"  - Error saving analyzed data: {e}")
        return None
        
    return analyzed_df

def main():
    """Main pipeline execution."""
    logging.info("====== Starting ARPI Data Pipeline ======")
    
    # Step 1: Unify and filter data
    filtered_df, overall_max_date = unify_data()
    
    # Step 2: Analyze data
    analyzed_df = analyze_data(filtered_df)
    
    if analyzed_df is not None:
        # Save overall_max_date to metadata.json
        metadata_path = "metadata.json"
        try:
            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump({'overall_max_date': overall_max_date.strftime('%Y-%m-%d')}, f, ensure_ascii=False, indent=2)
            logging.info(f"  - Overall max date saved to {metadata_path}")
        except Exception as e:
            logging.error(f"  - Failed to save metadata: {e}")

        logging.info("====== ARPI Data Pipeline Finished ======")
        logging.info("You can now run the dashboard: python3 -m streamlit run dashboard.py")
    else:
        logging.warning("====== ARPI Data Pipeline Finished with no data to analyze ======")

if __name__ == "__main__":
    main()