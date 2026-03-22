import time
import threading
import logging
from utils.concurrency import ConcurrencyManager
from core.searcher import QueryEngine
from ui.dashboard import CLIDashboard

# Set logging to ERROR to keep the CLI clean from worker background warnings
logging.getLogger().setLevel(logging.ERROR)

def main():
    print("\n" + "="*55)
    print("      GOOGLE-IN-A-DAY: SYSTEM ORCHESTRATOR")
    print("="*55)

    # 1. User Inputs & Configuration (Updated for 'origin' and 'k')
    origin = input("Enter Seed URL (origin) [Default: https://quotes.toscrape.com/]: ").strip()
    if not origin:
        origin = "https://quotes.toscrape.com/"
        
    k_input = input("Enter Max Crawl Depth (k) [Default: 2]: ").strip()
    k = int(k_input) if k_input.isdigit() else 2
        
    resume_input = input("Resume from previous session snapshot? (y/n): ").lower().strip()
    resume_mode = True if resume_input == 'y' else False

    print(f"\n[*] Initializing Engine for origin: {origin}")
    print(f"[*] Configuration: Max Depth (k)={k}, Workers=5, Native-Only Mode=ON")
    
    # 2. Initialize Engines
    # ConcurrencyManager handles Threading, Crawling & Persistence
    # Using 'origin' and 'k' to match the assignment requirements
    manager = ConcurrencyManager(seed_url=origin, max_depth=k, num_workers=5, max_queue_size=200)
    
    # UI Dashboard for Metric Visualization
    dashboard = CLIDashboard()
    
    # Start Crawler in a background daemon thread
    crawler_thread = threading.Thread(
        target=manager.start_crawling, 
        args=(resume_mode,), 
        daemon=True
    )
    crawler_thread.start()

    # QueryEngine shares references with the manager for Live Indexing
    searcher = QueryEngine(manager.indexed_data, manager.index_lock)

    time.sleep(1) # Brief buffer for thread startup
    
    print("\n[+] System is running in background. Live Indexing active.")
    print("-" * 60)
    print("COMMANDS:")
    print(" - 'stats' : View Real-time Dashboard (Metrics & Back-pressure)")
    print(" - 'exit'  : Gracefully save state and shutdown")
    print(" - [Word]  : Type any phrase to search the live index")
    print("-" * 60 + "\n")

    # 3. CLI Interaction Loop
    while True:
        try:
            cmd = input("Search Query > ").strip()
            if not cmd:
                continue
                
            if cmd.lower() == 'exit':
                print("\n[!] Graceful shutdown initiated...")
                
                # FORCE SAVE: Save the current progress and queue before exiting
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
                break
                
            elif cmd.lower() == 'stats':
                # Use the CLIDashboard module for modular visualization
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
                        # res format is exactly the requested triple: (relevant_url, origin_url, depth)
                        print(f"{idx}. Triple: {res}")
                        print(f"   URL: {res[0]} | Source: {res[1]} | Depth: {res[2]}")
                    print("*" * (30 + len(cmd)) + "\n")
                    
        except KeyboardInterrupt:
            print("\n[!] Interrupted by user. Closing...")
            break

if __name__ == "__main__":
    main()