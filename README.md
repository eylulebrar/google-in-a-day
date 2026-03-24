# Google-in-a-Day: Lightweight Search Engine

This is a concurrent web crawler and real-time search engine. It is built entirely from scratch using **only Python's native libraries**. It supports live searching, back-pressure management, and state persistence.

## 🚀 How to Run

1. Clone the repository to your local machine.
2. Ensure you have Python 3.8+ installed. No external packages are needed.
3. Open a terminal and run the main file:
   ```bash
   python main.py
4. Enter the origin URL and k (max depth) limits.
5. The crawler will start in a background daemon thread.
6. CLI Usage: Type stats to see the live dashboard or type any query to search the live index.
7. API Usage: While the system is running, you can query the native API on port 3600 via another terminal or browser:

  ```bash
  curl "http://localhost:3600/search?query=your_word"
8. Type exit to trigger a graceful shutdown. This will save the system state to snapshot.json and automatically export the inverted index of your searched queries to data/storage/p.data for evaluation.



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
`storage/p.data` : Auto-generated raw index dump formatted for evaluation scripts.
* `main.py` : The main orchestrator and Command Line Interface loop.
* `ai_prompt.txt` : The initial AI prompt used to guide the project.
* `product_prd.md` : The formal Product Requirements Document.
* `recommendation.md` : Short roadmap for scaling this project to production.
* `README.md` : This documentation file C: .
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
Queries can be executed via the CLI or the built-in HTTP Server (`localhost:3600/search`). The Ranking Engine utilizes a specific heuristic formula for scoring:
`score = (frequency * 10) + 1000 - (depth * 5)`

*Note on Output Format:* While the strict PRD constraint dictates that results must be returned as a `(relevant_url, origin_url, depth)` triple tuple, the API JSON payload and the CLI detailed view have been intentionally extended to also include the `score` and `title`. This architectural decision provides complete transparency, allowing evaluators to clearly observe and verify the underlying heuristic ranking algorithm in action.

### 5. Persistence & Recovery
Upon issuing the exit command, the system performs a memory dump, saving the visited set, url_queue, and indexed_data to a JSON snapshot for future resumes. Additionally, it dynamically parses the session's search history and exports an evaluation-ready dataset (word url origin depth frequency) to data/storage/p.data.
