import threading

class Indexer:
    """
    Handles the storage and retrieval of crawled data.
    Provides a thread-safe interface for the Crawler (writer) 
    and the Searcher (reader).
    """
    def __init__(self):
        # The core database of our search engine
        # Structure: { url: {"text": "...", "origin": "...", "depth": 0} }
        self.storage = {}
        self.lock = threading.Lock()

    def add_document(self, url, text, origin, depth):
        """Adds or updates a document in the index safely."""
        with self.lock:
            self.storage[url] = {
                "text": text,
                "origin": origin,
                "depth": depth
            }

    def get_all_data(self):
        """Returns a reference to the storage (use with caution/locks)."""
        return self.storage

    def get_index_size(self):
        """Returns the total number of indexed pages."""
        with self.lock:
            return len(self.storage)