# Google-in-a-Day: Lightweight Concurrent Search Engine

This project is a high-performance, concurrent web crawler and real-time search engine built entirely from scratch using **only Python's native libraries**. It demonstrates architectural sensibility, thread safety, and back-pressure management under heavy network I/O.

## 🚀 How to Run

1. Clone the repository.
2. Ensure you have Python 3.8+ installed (No external dependencies required).
3. Run the main orchestrator:
   ```bash
   python main.py
4. Enter a Seed URL (e.g., https://quotes.toscrape.com/).

5. The system will start crawling in the background. Type stats to see the live CLI Dashboard, or type any word to perform a Live Index Search.

##🏗️ System Architecture & AI Stewardship
As the System Architect steering the AI agents, several critical design decisions were enforced to meet the strict project constraints:

###1. Native-Only Constraint
No external high-level frameworks (like Scrapy, BeautifulSoup, or Requests) were used. The crawler network I/O is handled by urllib.request, and HTML parsing is done via a custom class extending html.parser.HTMLParser. This required implementing custom SSL bypass contexts to handle real-world certificate issues.

###2. Concurrency & Thread Safety
The system uses Python's built-in threading module. To prevent data corruption during "Live Indexing" (where the Searcher reads the index while the Crawler writes to it), a strict threading.Lock() mechanism is implemented. This ensures thread-safe operations across the shared indexed_data dictionary.

###3. Back-Pressure & Queue Management
To prevent memory leaks and uncontrolled crawling (OOM errors), a standard queue.Queue with a strictly defined maxsize is utilized. When the crawler finds links faster than the workers can process them, the queue.Full exception triggers our Throttling (Back-pressure) state. Worker threads are safely blocked without crashing the system, proving the architecture's resilience under load.

###4. Search & Relevancy Heuristic
A straightforward "Term Frequency" (Bag of Words) approach is used for relevancy. The query is tokenized, and exact matches are rewarded. This simple heuristic fulfills the requirement without the overhead of complex NLP models, though it is intentionally susceptible to "stop-word inflation" from large pages (a trade-off accepted for performance).

### 5. Persistence & Recovery (Bonus Achievement)
The system features a robust **State Checkpointing** mechanism. Upon a graceful shutdown (using the `exit` command), the current state of the engine—including the `visited` set, the remaining `url_queue`, and the full `indexed_data`—is serialized and saved to `data/snapshot.json`. 

- **Resumability:** On startup, the user is prompted to resume from the previous session. If selected, the engine reconstructs the memory state from the JSON snapshot, allowing the crawl to continue from the exact point it left off.
- **Data Integrity:** This ensures that hours of crawling progress are not lost due to system restarts or manual interruptions.
