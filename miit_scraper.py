# -*- coding: utf-8 -*-
"""
Dedicated scraper for policies from www.miit.gov.cn (中华人民共和国工业和信息化部).
This version is simplified to only scrape data, with filtering handled centrally.
"""
import time
import random
import re
import pandas as pd
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import requests
import logging
from urllib.parse import urljoin

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Configuration for MIIT Scraper ---
MIIT_BASE_URL = "https://www.miit.gov.cn"
MIIT_POLICY_LIST_PATH = "/jgsj/kjs/wjfb/"  # 科技司-文件发布

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

# --- Helper Functions ---
def safe_get(url, headers=None, retries=3, delay_range=(1, 3)):
    """Robustly makes an HTTP GET request with retries and delays."""
    for i in range(retries):
        try:
            time.sleep(random.uniform(*delay_range))
            response = requests.get(url, headers=headers, timeout=15)
            response.raise_for_status()
            response.encoding = response.apparent_encoding
            return response
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching {url} (Attempt {i+1}/{retries}): {e}")
            if i < retries - 1:
                time.sleep(delay_range[1] * (i + 1))
    return None

def extract_date_from_text(text):
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

def extract_department_from_text(text):
    """Attempts to extract an issuing department from text."""
    dept_patterns = [
        r'(?:发文机关|发布单位|发布部门)[:：\s]*(.*?)(?:\n|$|\s{2,})',
        r'(.*?)(?:部|委|局|厅)[\s]?(?:令|发|函|文|规|公告|通知|意见)'
    ]
    for pattern in dept_patterns:
        match = re.search(pattern, text)
        if match:
            department = match.group(1).strip()
            if 3 <= len(department) <= 30 and "、" not in department and "，" not in department:
                return department
    return "工业和信息化部"

# --- Core Scrapers ---
def get_miit_policy_details(policy_url):
    """Fetches and extracts details from a single MIIT policy page."""
    logger.info(f"  Scraping policy details: {policy_url}")
    details = {'title': 'N/A', 'url': policy_url, 'publication_date': None, 'issuing_department': None, 'full_text': ''}
    response = safe_get(policy_url, headers=HEADERS)
    if not response:
        return details

    soup = BeautifulSoup(response.text, 'html.parser')
    for script_or_style in soup(["script", "style"]):
        script_or_style.decompose()

    title_tag = soup.find('h1') or soup.select_one('.article-title') or soup.select_one('#main_content .title')
    details['title'] = title_tag.get_text(strip=True) if title_tag else 'N/A'

    content_div = soup.find('div', class_='art_con') or soup.find('div', id='zoom') or soup.find('div', class_='content_body')
    full_text = content_div.get_text(separator='\n', strip=True) if content_div else soup.get_text(separator='\n', strip=True)
    details['full_text'] = full_text

    details['publication_date'] = extract_date_from_text(full_text)
    details['issuing_department'] = extract_department_from_text(full_text)
    
    meta_info_div = soup.select_one('.meta-info') or soup.select_one('.article-meta')
    if meta_info_div:
        meta_text = meta_info_div.get_text()
        if not details['publication_date']:
            date_match = re.search(r'发布日期[:：\s]*(\d{4}[-/年]\d{1,2}[-/月]\d{1,2})', meta_text)
            if date_match:
                details['publication_date'] = date_match.group(1).replace('年', '-').replace('月', '-')
        if not details['issuing_department'] or details['issuing_department'] == "工业和信息化部":
            dept_match = re.search(r'(?:发文机关|发布单位|发布部门)[:：\s]*(.*?)(?:\n|$|\s{2,})', meta_text)
            if dept_match:
                details['issuing_department'] = dept_match.group(1).strip()
    return details

def scrape_miit_policy_list(max_pages=5):
    """Scrapes policy links from MIIT's policy list pages using Selenium."""
    all_policies_data = []
    logger.info("--- Starting browser for scraping ---")
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument(f"user-agent={HEADERS['User-Agent']}")
    try:
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    except Exception as e:
        logger.error(f"Could not start Selenium WebDriver: {e}")
        return []

    try:
        list_url = f"{MIIT_BASE_URL}{MIIT_POLICY_LIST_PATH}index.html"
        logger.info(f"Accessing initial list page: {list_url}")
        driver.get(list_url)
        for page_num in range(1, max_pages + 1):
            logger.info(f"\n--- Scraping Page {page_num} ---")
            wait = WebDriverWait(driver, 20)
            try:
                logger.info("Waiting for policy list to load...")
                wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".page-content ul")))
            except Exception as e:
                logger.error(f"Timeout or error while waiting for list content: {e}")
                break
            
            list_element_for_staleness_check = driver.find_element(By.CSS_SELECTOR, ".page-content ul")
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            policy_links_container = soup.select_one('.page-content ul')
            
            if not policy_links_container:
                logger.warning("Could not find policy list container.")
                break
            
            links = policy_links_container.find_all('a', href=True)
            found_on_page = 0
            for link in links:
                href = link['href'].strip()
                if href.startswith('./'):
                    href = href[1:]
                
                full_url = urljoin(MIIT_BASE_URL + MIIT_POLICY_LIST_PATH, href)

                if 'art_' in full_url or re.search(r'/\d{4,}/\d+\.html', full_url):
                    if full_url not in [p['url'] for p in all_policies_data]:
                        policy_data = get_miit_policy_details(full_url)
                        if policy_data and policy_data['title'] != 'N/A' and policy_data['full_text']:
                            all_policies_data.append(policy_data)
                            found_on_page += 1
            
            logger.info(f"Found {found_on_page} new policies on page {page_num}.")
            
            if page_num < max_pages:
                try:
                    next_button_xpath = "//a[text()='下一页']"
                    wait.until(EC.element_to_be_clickable((By.XPATH, next_button_xpath)))
                    next_button = driver.find_element(By.XPATH, next_button_xpath)
                    if "layui-disabled" in next_button.get_attribute("class"):
                        logger.info("'Next page' button is disabled. Reached the last page.")
                        break
                    logger.info("Clicking 'Next page'...")
                    driver.execute_script("arguments[0].click();", next_button)
                    logger.info("Waiting for page to refresh...")
                    wait.until(EC.staleness_of(list_element_for_staleness_check))
                except Exception:
                    logger.warning("Could not find 'Next page' button, or it was the last page.")
                    break
    except Exception as e:
        logger.critical(f"A critical error occurred during Selenium scraping: {e}")
    finally:
        logger.info("Closing browser.")
        driver.quit()
    return all_policies_data

def main():
    """Main function to run the MIIT policy scraper."""
    print("=" * 60)
    print("MIIT Policy Scraper v2.0 (Simplified, No AI Filter)")
    print("=" * 60)
    
    policies = scrape_miit_policy_list(max_pages=10)
    if not policies:
        print("\nFailed to scrape any policy data from MIIT website.")
        return

    print(f"\nSuccessfully scraped {len(policies)} policies from MIIT.")

    df_all = pd.DataFrame(policies)
    all_filename = 'miit_all_policies.csv'
    df_all.to_csv(all_filename, index=False, encoding='utf-8-sig')
    print(f"\n✓ All policies saved to {all_filename}")

if __name__ == "__main__":
    main()