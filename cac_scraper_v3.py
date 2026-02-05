# -*- coding: utf-8 -*-
"""
网信办政策爬虫 - 独立版本 (Simplified for central filtering)
"""
import re
import time
import requests
import pandas as pd
from datetime import datetime
from typing import List, Tuple, Dict, Any
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import random
import logging
from urllib.parse import urljoin

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CACPolicyScraper:
    """网信办政策爬虫"""

    def __init__(self, max_pages=10):
        self.base_url = "https://www.cac.gov.cn"
        self.list_path = "/wxzw/wxfb/"
        self.max_pages = max_pages
        self.delay_range = (1.0, 3.0)
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        self.driver = None

    def safe_request(self, url, retries=3, delay_range=(1, 3)):
        """Robustly makes an HTTP GET request with retries and delays."""
        for i in range(retries):
            try:
                time.sleep(random.uniform(*delay_range))
                response = self.session.get(url, timeout=20)
                response.raise_for_status()
                response.encoding = response.apparent_encoding
                return response
            except requests.exceptions.RequestException as e:
                logger.error(f"Error fetching {url} (Attempt {i+1}/{retries}): {e}")
                if i < retries - 1:
                    time.sleep(delay_range[1] * (i + 1))
        return None

    def clean_text(self, text: str) -> str:
        """Cleans text by removing excessive whitespace."""
        return re.sub(r'\s+', ' ', text).strip()

    def extract_date_from_text(self, text: str) -> str:
        """Attempts to extract a date from text using common patterns."""
        date_patterns = [
            r'(\d{4}[-/年]\d{1,2}[-/月]\d{1,2})日?',
            r'发布日期[:：\s]*(\d{4}[-/年]\d{1,2}[-/月]\d{1,2})',
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

    def extract_department_from_text(self, text: str) -> str:
        """Attempts to extract an issuing department from text."""
        dept_patterns = [
            r'^(?:中华人民共和国)?(国家互联网信息办公室|国家网信办)',
            r'(?:发文机关|发布单位|发布部门)[:：\s]*(.*?)(?:\n|$|\s{2,})'
        ]
        for pattern in dept_patterns:
            match = re.search(pattern, text)
            if match:
                department = match.group(1).strip()
                if department and 3 <= len(department) <= 30:
                    return department
        return self.get_default_department()

    def get_list_url(self, page_num: int) -> str:
        return urljoin(self.base_url, f"{self.list_path}A093702index_{page_num}.htm")

    def get_default_department(self) -> str:
        return "国家网信办"

    def extract_article_links(self, soup: BeautifulSoup) -> List[Tuple[str, str]]:
        """从列表页提取文章链接"""
        links = []
        list_container = soup.select_one('#loadingInfoPage')
        if not list_container:
            return []
            
        all_links = list_container.select('li h5 a')
        
        for link in all_links:
            href = link.get('href', '')
            text = link.get_text(strip=True)
            if not href or not text: continue
            
            full_url = urljoin(self.base_url, href)
            if any(skip in full_url.lower() for skip in ['javascript:', '#', '.pdf', '.doc', '.xls', '.zip']): continue
            
            links.append((full_url, text))
        
        unique_links = list(dict.fromkeys(links))
        return unique_links

    def extract_article_content(self, url: str) -> Dict[str, Any]:
        """提取文章详细内容"""
        logger.info(f"  Scraping details from: {url}")
        response = self.safe_request(url)
        if not response: return {}
        
        soup = BeautifulSoup(response.content, 'html.parser', from_encoding='utf-8')
        
        for element in soup(['script', 'style']):
            element.decompose()
        
        title = soup.select_one('h1, .article_title')
        title_text = title.get_text(strip=True) if title else 'N/A'
        
        content_elem = soup.select_one('#content, .TRS_Editor, .article_content, .content')
        content = content_elem.get_text(separator='\n', strip=True) if content_elem else soup.get_text(separator='\n', strip=True)
        content = self.clean_text(content)
        
        meta_info = soup.select_one('.article_info, .pages-date, .article-inf')
        meta_text = meta_info.get_text(strip=True) if meta_info else ''
        
        pub_date = self.extract_date_from_text(meta_text) or self.extract_date_from_text(content)
        department = self.extract_department_from_text(meta_text) or self.extract_department_from_text(content)

        return {
            'title': title_text,
            'url': url,
            'publication_date': pub_date,
            'issuing_department': department,
            'full_text': content
        }

    def handle_pagination(self, page_num: int) -> bool:
        if page_num >= self.max_pages:
            logger.info("Reached max pages limit.")
            return False
        
        try:
            wait = WebDriverWait(self.driver, 10)
            next_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//div[@id='Page']//a[text()='>']")))
            self.driver.execute_script("arguments[0].click();", next_button)
            return True
        except Exception as e:
            logger.warning(f"Could not find or click next page button. Ending pagination. Reason: {e}")
            return False

    def scrape_all_policies(self) -> List[Dict[str, Any]]:
        """Main scraping loop for all policies."""
        all_policies = []
        
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument(f"user-agent={self.headers['User-Agent']}")

        try:
            self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        except Exception as e:
            logger.error(f"Failed to start Selenium WebDriver: {e}")
            return []

        try:
            list_url = self.get_list_url(1)
            logger.info(f"\n--- Scraping Page 1: {list_url} ---")
            self.driver.get(list_url)

            for page_num in range(1, self.max_pages + 1):
                if page_num > 1:
                    logger.info(f"\n--- Scraping Page {page_num} ---")
                
                try:
                    WebDriverWait(self.driver, 20).until(EC.presence_of_element_located((By.CSS_SELECTOR, "#loadingInfoPage li a")))
                    time.sleep(random.uniform(2.0, 4.0))
                except Exception as e:
                    logger.warning(f"Timeout waiting for article list on page {page_num}. Ending scrape. Reason: {e}")
                    break

                soup = BeautifulSoup(self.driver.page_source, 'html.parser')
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
                
                if not self.handle_pagination(page_num):
                    break
        
        except Exception as e:
            logger.error(f"A critical error occurred during scraping: {e}", exc_info=True)
        finally:
            if self.driver:
                self.driver.quit()
                logger.info("Browser closed.")
        
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
    print("网信办政策爬虫 v3.3 (Simplified, No AI Filter)")
    print("=" * 60)
    
    scraper = CACPolicyScraper(max_pages=5)
    
    policies = scraper.scrape_all_policies()
    
    if not policies:
        print("\n未获取到任何政策数据，程序终止。")
        return
    
    filename = scraper.save_to_csv(policies, "cac_all_policies.csv")
    
    if filename:
        print(f"\n✓ 抓取完成: {len(policies)} 条政策已保存到 {filename}")

if __name__ == "__main__":
    main()
