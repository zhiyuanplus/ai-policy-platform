# -*- coding: utf-8 -*-
"""
全国信息安全标准化技术委员会 (TC260) 意见征求稿爬虫
This version is simplified to only scrape data, with filtering handled centrally.
"""
import re
import time
import requests
import pandas as pd
from datetime import datetime
from typing import List, Tuple, Dict, Any
from bs4 import BeautifulSoup
import random
import logging
from urllib.parse import urljoin

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TC260PolicyScraper:
    """TC260 意见征求稿爬虫"""

    def __init__(self, max_pages=10):
        self.base_url = "https://www.tc260.org.cn"
        self.list_path = "/portal/suggestion"
        self.max_pages = max_pages
        self.delay_range = (0.5, 1.5)
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)

    def safe_request(self, url, retries=3):
        """Robustly makes an HTTP GET request with retries and delays."""
        for i in range(retries):
            try:
                time.sleep(random.uniform(*self.delay_range))
                response = self.session.get(url, timeout=20)
                response.raise_for_status()
                response.encoding = response.apparent_encoding
                return response
            except requests.exceptions.RequestException as e:
                logger.error(f"Error fetching {url} (Attempt {i+1}/{retries}): {e}")
                if i < retries - 1:
                    time.sleep(self.delay_range[1] * (i + 1))
        return None

    def extract_date_from_text(self, text: str) -> str:
        """Attempts to extract a date from text using common patterns."""
        date_patterns = [
            r'(\d{4}[-/年]\d{1,2}[-/月]\d{1,2})日?',
            r'发布于[:：\s]*(\d{4}[-/年]\d{1,2}[-/月]\d{1,2})',
        ]
        for pattern in date_patterns:
            match = re.search(pattern, text)
            if match:
                date_str = match.group(1).replace('年', '-').replace('月', '-').replace('/', '-')
                try:
                    return datetime.strptime(date_str, '%Y-%m-%d').strftime('%Y-%m-%d')
                except ValueError:
                    pass
        return None

    def get_list_url(self, page_num: int) -> str:
        return f"{self.base_url}{self.list_path}?page={page_num}"

    def get_default_department(self) -> str:
        return "全国信息安全标准化技术委员会"

    def extract_article_links(self, soup: BeautifulSoup) -> List[Tuple[str, str]]:
        """Extracts article links from a list page."""
        links = []
        list_container = soup.select_one('.publication .right')
        if not list_container:
            return []
            
        items = list_container.select('.item a')
        
        for item in items:
            onclick_attr = item.get('onclick')
            if not onclick_attr: continue
            
            match = re.search(r"jumpDetail\('([^']*)'", onclick_attr)
            if match:
                article_id = match.group(1)
                title = item.get_text(strip=True)
                full_url = urljoin(self.base_url, f"/portal/suggestion-detail/{article_id}")
                links.append((full_url, title))
        
        return links

    def extract_article_content(self, url: str) -> Dict[str, Any]:
        """Extracts content from a single article detail page."""
        logger.info(f"  Scraping details from: {url}")
        response = self.safe_request(url)
        if not response: return {}
        
        soup = BeautifulSoup(response.content, 'html.parser', from_encoding='utf-8')
        
        for element in soup(['script', 'style']):
            element.decompose()
        
        title_elem = soup.select_one('.advice .title h1')
        title_text = title_elem.get_text(strip=True) if title_elem else 'N/A'
        
        date_elem = soup.select_one('.advice .title .time')
        date_text = date_elem.get_text(strip=True) if date_elem else ''
        pub_date = self.extract_date_from_text(date_text)

        content_elem = soup.select_one('.advice-c .info')
        content = content_elem.get_text(separator='\n', strip=True) if content_elem else ''
        
        attachment_links = soup.select('.advice-c .list a')
        if attachment_links:
            attachment_text = "\n\n--- 相关附件 ---\n"
            for link in attachment_links:
                link_href = urljoin(self.base_url, link.get('href', ''))
                link_text = link.get_text(strip=True)
                attachment_text += f"- {link_text}: {link_href}\n"
            content += attachment_text

        return {
            'title': title_text,
            'url': url,
            'publication_date': pub_date,
            'issuing_department': self.get_default_department(),
            'full_text': content
        }

    def scrape_all_policies(self) -> List[Dict[str, Any]]:
        """Main scraping loop for all policies."""
        all_policies = []
        
        for page_num in range(1, self.max_pages + 1):
            list_url = self.get_list_url(page_num)
            logger.info(f"\n--- Scraping Page {page_num}: {list_url} ---")
            
            response = self.safe_request(list_url)
            if not response:
                logger.error(f"Failed to fetch list page {page_num}. Stopping.")
                break

            soup = BeautifulSoup(response.text, 'html.parser')
            links = self.extract_article_links(soup)
            
            if not links:
                logger.info(f"No articles found on page {page_num}. Ending scrape.")
                break
            
            logger.info(f"Found {len(links)} links on page {page_num}.")
            
            for url, title in links:
                if url not in [p['url'] for p in all_policies]:
                    details = self.extract_article_content(url)
                    if details and details.get('title') != 'N/A' and details.get('full_text'):
                        all_policies.append(details)
        
        return all_policies

    def save_to_csv(self, policies: List[Dict[str, Any]], filename: str) -> str:
        """Saves a list of policy dictionaries to a CSV file."""
        if not policies:
            logger.warning("No policies to save.")
            return ""
            
        df = pd.DataFrame(policies)
        
        output_columns = ['title', 'url', 'publication_date', 'issuing_department', 'full_text']
        df = df[[col for col in output_columns if col in df.columns]]
        
        try:
            df.to_csv(filename, index=False, encoding='utf-8-sig')
            logger.info(f"Successfully saved {len(df)} policies to {filename}")
            return filename
        except Exception as e:
            logger.error(f"Failed to save data to {filename}: {e}")
            return ""

def main():
    """主函数"""
    print("=" * 60)
    print("TC260 意见征求稿爬虫 v2.0 (Simplified, No AI Filter)")
    print("=" * 60)
    
    scraper = TC260PolicyScraper(max_pages=5)
    
    policies = scraper.scrape_all_policies()
    
    if not policies:
        print("\n未获取到任何政策数据，程序终止。")
        return
    
    filename = scraper.save_to_csv(policies, "tc260_all_policies.csv")

    if filename:
        print(f"\n✓ 抓取完成: {len(policies)} 条政策已保存到 {filename}")

if __name__ == "__main__":
    main()