"""
URL Processing Module for SmartNotes AI
Handles website content extraction
"""

import re
import logging
import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


def validate_url(url):
    """Simple URL validation"""
    url_pattern = re.compile(
        r'^https?://'
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'
        r'localhost|'
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'
        r'(?::\d+)?'
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    return url_pattern.match(url) is not None


class WebsiteProcessor:
    """Handle website content extraction and scraping"""
    
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
    
    def extract_with_beautifulsoup(self, url):
        """Extract content using BeautifulSoup"""
        try:
            response = requests.get(url, headers=self.headers, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Remove unwanted elements
            for element in soup(['script', 'style', 'nav', 'footer', 'header', 'aside', 'iframe', 'noscript']):
                element.decompose()
            
            # Get title
            title = soup.find('title')
            title_text = title.get_text().strip() if title else 'Webpage'
            
            # Try to find main content
            main_content = None
            
            for selector in ['article', 'main', '[role="main"]']:
                main_content = soup.select_one(selector)
                if main_content:
                    break
            
            if not main_content:
                for pattern in ['content', 'article', 'post', 'entry', 'body']:
                    main_content = soup.find(['div', 'section'], class_=re.compile(pattern, re.I))
                    if main_content:
                        break
            
            if not main_content:
                main_content = soup.find('body')
            
            # Extract text
            if main_content:
                paragraphs = main_content.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
                text_parts = [p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True)]
                text = ' '.join(text_parts)
            else:
                text = soup.get_text(separator=' ', strip=True)
            
            # Clean up text
            text = re.sub(r'\s+', ' ', text).strip()
            
            if len(text.split()) < 50:
                raise Exception("Not enough content extracted from the webpage")
            
            # Try to find author
            author = 'Unknown'
            author_meta = soup.find('meta', attrs={'name': re.compile('author', re.I)})
            if author_meta and author_meta.get('content'):
                author = author_meta['content']
            
            return {
                'success': True,
                'title': title_text,
                'text': text,
                'url': url,
                'word_count': len(text.split()),
                'authors': author,
                'method': 'beautifulsoup'
            }
            
        except Exception as e:
            logger.error(f"BeautifulSoup extraction failed: {e}")
            return {
                'success': False,
                'error': f'Failed to extract content: {str(e)}'
            }
    
    def extract_content(self, url):
        """Main method to extract content from URL"""
        if not validate_url(url):
            return {
                'success': False,
                'error': 'Invalid URL format.'
            }
        
        return self.extract_with_beautifulsoup(url)


# Utility functions
def estimate_reading_time(word_count, words_per_minute=200):
    """Estimate reading time in minutes"""
    return max(1, round(word_count / words_per_minute))


def get_domain_name(url):
    """Extract domain name from URL"""
    try:
        from urllib.parse import urlparse
        parsed = urlparse(url)
        domain = parsed.netloc
        if domain.startswith('www.'):
            domain = domain[4:]
        return domain
    except:
        return 'unknown'