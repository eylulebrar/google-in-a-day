# Google-in-a-Day: Lightweight Search Engine

This is a concurrent web crawler and real-time search engine. It is built entirely from scratch using **only Python's native libraries**. It supports live searching, back-pressure management, and state persistence.

## 🚀 How to Run

1. Clone the repository to your local machine.
2. Ensure you have Python 3.8+ installed. No external packages are needed.
3. Open a terminal and run the main file:
   ```bash
   python main.py
4. Enter the origin URL.
5. Enter the k (max depth) for the crawl limit.
6. The crawler will start in the background. You can type stats to see the live dashboard or type any word to search the index while it is crawling. Type exit to save and close safely.



## 📁 Project Structure

I divided the project into logical modules to keep the code clean and maintainable. Here is the complete breakdown of the repository:

* `core/` : Contains the main engines.
  * `crawler.py` : Handles HTML parsing and URL extraction natively.
  * `searcher.py` : Processes queries and returns the `(relevant_url, origin_url, depth)` format.
* `utils/` : Contains system helpers.
  * `concurrency.py` : Manages worker threads, locks, and the queue system.
  * `persistence.py` : Handles saving and loading the system state.
* `ui/` : Contains the user interface.
  * `dashboard.py` : Prints the live system metrics table in the terminal.
* `data/` : Directory for storing the `snapshot.json` persistence file.
* `main.py` : The main orchestrator and Command Line Interface loop.
* `ai_prompt.txt` : The initial AI prompt used to guide the project.
* `product_prd.md` : The formal Product Requirements Document.
* `recommendation.md` : Short roadmap for scaling this project to production.
* `README.md` : The documentation file you are reading right now C: .
* `.cursorrules` : Cursor IDE configuration file enforcing native-only coding constraints.
* `.gitignore` : Git configuration file.


## ⚙️ How the System Works (Key Features)
### 1. Native Crawling (index(origin, k))
The system takes an origin URL and crawls up to k depth. It uses a visited set to make sure it never crawls the same page twice. Everything is done using Python's standard libraries, bypassing SSL errors natively.

### 2. Concurrency & Thread Safety
The engine uses 5 worker threads. To make "Live Indexing" possible (searching while crawling), I used threading.Lock(). This ensures that multiple workers can write to the index at the same time without data corruption.

### 3. Back-Pressure (Queue Management)
To prevent out-of-memory (OOM) errors and system crashes under heavy load, the URL queue has a strict maxsize of 200. If the queue is full, the system blocks new URLs from being added until workers process the existing ones. You can see this as the "ACTIVE (Back-pressure)" status in the stats dashboard.

### 4. Live Search (search(query))
You can search the index at any time. The system uses a basic Term Frequency (TF) heuristic to rank pages (pages where the word appears the most show up first). The results are returned as a list of triples: (relevant_url, origin_url, depth).

### 5. Persistence & Recovery (Bonus)
If you type exit, the system gracefully shuts down. It saves the current visited set, the url_queue, and the indexed_data to a local snapshot.json file. When you restart the program, you can choose to resume the crawl from the exact point you left off instead of starting from scratch.