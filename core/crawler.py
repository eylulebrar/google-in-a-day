import urllib.request
import urllib.parse
from html.parser import HTMLParser
import threading
import logging
import ssl

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(threadName)s - %(message)s')

class NativeHTMLParser(HTMLParser):
    def __init__(self, base_url):
        super().__init__()
        self.base_url = base_url
        self.extracted_links = set()
        self.text_content = []

    def handle_starttag(self, tag, attrs):
        if tag == 'a':
            for name, value in attrs:
                if name == 'href':
                    full_url = urllib.parse.urljoin(self.base_url, value)
                    parsed = urllib.parse.urlparse(full_url)
                    if parsed.scheme in ('http', 'https'):
                        clean_url = urllib.parse.urlunparse((parsed.scheme, parsed.netloc, parsed.path, '', parsed.query, ''))
                        self.extracted_links.add(clean_url)

    def handle_data(self, data):
        stripped = data.strip()
        if stripped:
            self.text_content.append(stripped)

    def get_text(self):
        return " ".join(self.text_content)


class CrawlerEngine:
    def __init__(self):
        self.visited = set()
        self.visited_lock = threading.Lock()

    def is_visited(self, url):
        with self.visited_lock:
            if url in self.visited:
                return True
            self.visited.add(url)
            return False

    def fetch_and_parse(self, url):
        # ÇÖZÜM: İlk linki de listeye ekliyoruz, ama işlemi durdurmuyoruz!
        with self.visited_lock:
            self.visited.add(url)

        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
            
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE

            with urllib.request.urlopen(req, timeout=5, context=ctx) as response:
                content_type = response.getheader('Content-Type')
                if not content_type or 'text/html' not in content_type:
                    return None, None 

                html_bytes = response.read()
                html_str = html_bytes.decode('utf-8', errors='ignore')

                parser = NativeHTMLParser(url)
                parser.feed(html_str)
                
                return parser.extracted_links, parser.get_text()

        except Exception as e:
            return None, None