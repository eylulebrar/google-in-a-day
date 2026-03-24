import time
import threading
import logging
import json
import os
import re
from collections import Counter
from urllib.parse import urlparse, parse_qs
from http.server import HTTPServer, BaseHTTPRequestHandler

from utils.concurrency import ConcurrencyManager
from core.searcher import QueryEngine
from ui.dashboard import CLIDashboard

# Set logging to ERROR to keep the CLI clean from worker background warnings
logging.getLogger().setLevel(logging.ERROR)

# ==========================================
# YENİ EKLENEN: NATIVE API SERVER (Port 3600)
# ==========================================
class NativeSearchAPI(BaseHTTPRequestHandler):
    searcher_ref = None

    def do_GET(self):
        parsed_url = urlparse(self.path)
        
        if parsed_url.path == '/search':
            qs = parse_qs(parsed_url.query)
            query = qs.get('query', [''])[0]
            
            if query and self.searcher_ref:
                results = self.searcher_ref.search(query, top_n=5)
                
                response_data = {
                    "query": query,
                    "results": results
                }
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps(response_data, indent=4).encode('utf-8'))
            else:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(b'{"error": "Missing query parameter"}')
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        pass


# ==========================================
# ANA SİSTEM
# ==========================================
def main():
    print("\n" + "="*55)
    print("      GOOGLE-IN-A-DAY: SYSTEM ORCHESTRATOR")
    print("="*55)

    origin = input("Enter Seed URL (origin) [Default: https://quotes.toscrape.com/]: ").strip()
    if not origin:
        origin = "https://quotes.toscrape.com/"
        
    k_input = input("Enter Max Crawl Depth (k) [Default: 2]: ").strip()
    k = int(k_input) if k_input.isdigit() else 2
        
    resume_input = input("Resume from previous session snapshot? (y/n): ").lower().strip()
    resume_mode = True if resume_input == 'y' else False

    print(f"\n[*] Initializing Engine for origin: {origin}")
    print(f"[*] Configuration: Max Depth (k)={k}, Workers=5, Native-Only Mode=ON")
    
    manager = ConcurrencyManager(seed_url=origin, max_depth=k, num_workers=5, max_queue_size=200)
    dashboard = CLIDashboard()
    
    crawler_thread = threading.Thread(
        target=manager.start_crawling, 
        args=(resume_mode,), 
        daemon=True
    )
    crawler_thread.start()

    searcher = QueryEngine(manager.indexed_data, manager.index_lock)

    # ---------------------------------------------------------
    # API SUNUCUSUNU BAŞLATMA KISMI (Port 3600)
    # ---------------------------------------------------------
    NativeSearchAPI.searcher_ref = searcher
    try:
        api_server = HTTPServer(('', 3600), NativeSearchAPI)
        api_thread = threading.Thread(target=api_server.serve_forever, daemon=True)
        api_thread.start()
        print("[+] Native API Server listening on http://localhost:3600")
    except Exception as e:
        print(f"[-] Could not start API server on port 3600: {e}")
    # ---------------------------------------------------------

    time.sleep(1) 
    
    print("\n[+] System is running in background. Live Indexing active.")
    print("-" * 60)
    print("COMMANDS:")
    print(" - 'stats' : View Real-time Dashboard (Metrics & Back-pressure)")
    print(" - 'exit'  : Gracefully save state and shutdown")
    print(" - [Word]  : Type any phrase to search the live index")
    print("-" * 60 + "\n")

    searched_words = set()
    
    while True:
        try:
            cmd = input("Search Query > ").strip()
            if not cmd:
                continue
                
            if cmd.lower() not in ['exit', 'stats']:
                searched_words.add(cmd.lower())
                
            if cmd.lower() == 'exit':
                print("\n[!] Graceful shutdown initiated...")
                
                current_queue = list(manager.url_queue.queue)
                success = manager.persistence.save_state(
                    manager.crawler.visited, 
                    current_queue, 
                    manager.indexed_data
                )
                
                if success:
                    print("[Snapshot] System state successfully saved to data/snapshot.json")
                else:
                    print("[Error] Failed to save system state.")
                    
                try:
                    if searched_words: 
                        os.makedirs("data/storage", exist_ok=True)
                        with open("data/storage/p.data", "w", encoding="utf-8") as f:
                            for url, page_data in manager.indexed_data.items():
                                if isinstance(page_data, dict):
                                    text = page_data.get('text', '')
                                    origin_url = page_data.get('origin', 'unknown')
                                    depth = page_data.get('depth', 0)
                                    
                                    if isinstance(text, str) and text:
                                        words = re.findall(r'\b\w+\b', text.lower())
                                        word_counts = Counter(words)
                                        
                                        for word in searched_words:
                                            if word in word_counts:
                                                freq = word_counts[word]
                                                f.write(f"{word} {url} {origin_url} {depth} {freq}\n")
                                                
                        print(f"[+] Exported data for your searches ({', '.join(searched_words)}) to p.data")
                    else:
                        print("[-] No searches made this session. Skipping p.data export.")
                        
                except Exception as e:
                    print(f"[-] Could not export p.data: {e}")
                    
                break
                
            elif cmd.lower() == 'stats':
                with manager.stats_lock:
                    stats = manager.stats
                q_size = manager.url_queue.qsize()
                
                dashboard.display_metrics(
                    processed_count=stats['processed'],
                    queue_depth=q_size,
                    throttling_status=stats['throttling'],
                    total_indexed=len(manager.indexed_data)
                )
                
            else:
                # Perform Live Index Search
                results = searcher.search(cmd, top_n=5)
                if not results:
                    print(f"[-] '{cmd}' not found in current index. Crawling continues...\n")
                else:
                    print(f"\n" + "*"*10 + f" Search Results for '{cmd}' " + "*"*10)
                    for idx, res in enumerate(results, 1):
                        # CLI ekranında PRD kuralına sadık kalarak sadece Triple basıyoruz.
                        # Score ve Title arka planda JSON objesinde yaşamaya devam ediyor.
                        print(f"{idx}. Triple: ('{res['relevant_url']}', '{res['origin_url']}', {res['depth']})")
                        print(f"   URL: {res['relevant_url']} | Source: {res['origin_url']} | Depth: {res['depth']}")
                    print("*" * (30 + len(cmd)) + "\n")
                    
        except KeyboardInterrupt:
            print("\n[!] Interrupted by user. Closing...")
            break

if __name__ == "__main__":
    main()