import threading
import queue
import time
import logging
from core.crawler import CrawlerEngine
from utils.persistence import PersistenceManager

class ConcurrencyManager:
    """
    Worker thread'leri, queue depth limitlerini ve rate limiting'i yöneten orkestratör.
    """
    def __init__(self, seed_url, max_depth, num_workers=5, max_queue_size=1000, max_rate_sec=0.5):
        self.seed_url = seed_url
        self.max_depth = max_depth
        self.num_workers = num_workers
        self.max_rate_sec = max_rate_sec
        
        self.persistence = PersistenceManager()
        
        # Back Pressure: maxsize limiti dolduğunda put() bloke olur
        self.url_queue = queue.Queue(maxsize=max_queue_size)
        self.crawler = CrawlerEngine()
        
        # Searcher'ın (Indexer) kullanacağı, thread-safe veri depoları
        self.indexed_data = {}
        self.index_lock = threading.Lock()
        
        # İstatistikler (Dashboard UI için)
        self.stats = {
            "processed": 0,
            "queued": 1, # seed url eklenecek
            "throttling": False
        }
        self.stats_lock = threading.Lock()

    def worker_task(self):
        while True:
            try:
                # Kuyruktan eleman al, 3 saniye boşsa bekle
                current_url, current_depth = self.url_queue.get(timeout=3)
            except queue.Empty:
                break # Kuyruk boşaldı, worker'ı sonlandır

            # Derinlik k sınırını aştıysa geç
            if current_depth > self.max_depth:
                self.url_queue.task_done()
                self._update_stats(processed_inc=1, queued_inc=-1)
                continue

            # Hedef sunucuyu spamlamamak için rate limiting (Max rate of work)
            time.sleep(self.max_rate_sec)

            logging.info(f"[Derinlik: {current_depth}] Taranıyor: {current_url}")
            new_links, text_content = self.crawler.fetch_and_parse(current_url)

            if new_links is not None and text_content is not None:
                # Indexed veriyi RWMutex / Lock ile koruyarak yaz
                with self.index_lock:
                    self.indexed_data[current_url] = {
                        "text": text_content,
                        "origin": self.seed_url, 
                        "depth": current_depth
                    }

                # Yeni bulunan linkleri kuyruğa ekle (k+1 derinlik ile)
                if current_depth < self.max_depth:
                    for link in new_links:
                        if not self.crawler.is_visited(link): # Sadece yeni linkler
                            try:
                                # block=False ve Full exception ile Throttling durumunu yakalayabiliriz
                                self.url_queue.put((link, current_depth + 1), block=True, timeout=5)
                                self._update_stats(queued_inc=1)
                            except queue.Full:
                                # Queue doldu (Back Pressure tetiklendi)
                                self._set_throttling(True)
                                logging.warning("Kuyruk dolu! Back pressure devrede, URL atlanıyor.")
                                
            self._update_stats(processed_inc=1, queued_inc=-1)
            self.url_queue.task_done()

    def _update_stats(self, processed_inc=0, queued_inc=0):
        with self.stats_lock:
            self.stats["processed"] += processed_inc
            self.stats["queued"] += queued_inc

    def _set_throttling(self, status):
        with self.stats_lock:
            self.stats["throttling"] = status

    def start_crawling(self, resume=False):
        if resume:
            state = self.persistence.load_state()
            if state:
                # Durumu geri yükle
                self.crawler.visited = set(state["visited"])
                self.indexed_data.update(state["indexed_data"])
                for item in state["queue"]:
                    self.url_queue.put(tuple(item))
                logging.info(f"[Persistence] {len(state['visited'])} URL ve kuyruk geri yüklendi.")
        else:
            # Normal başlangıç
            self.url_queue.put((self.seed_url, 0))
        
        threads = []
        for i in range(self.num_workers):
            t = threading.Thread(target=self.worker_task, name=f"Worker-{i}")
            t.daemon = True
            t.start()
            threads.append(t)
            
        self.url_queue.join()
        
        # Tarama bitince durumu kaydet (Persistence Bonus)
        queue_list = list(self.url_queue.queue)
        self.persistence.save_state(self.crawler.visited, queue_list, self.indexed_data)
        logging.info("Sistem durumu diske kaydedildi.")

# Test bloğu
if __name__ == "__main__":
    # max_depth=1 vererek recursive çalışmasını test edelim
    manager = ConcurrencyManager(seed_url="https://example.com", max_depth=1, num_workers=2)
    manager.start_crawling()
    print(f"Toplam İndekslenen Sayfa: {len(manager.indexed_data)}")
    
    
    
# PRD'deki isterleri karşılamak için utils/concurrency.py dosyasını oluşturacağız. Ajanların (worker threads) sistemi boğmasını engellemek için Python'un yerleşik queue.Queue(maxsize=...) yapısını kullanacağız. Bu bize doğal bir "Back Pressure" sağlayacak; çünkü kuyruk dolduğunda thread'ler put() işleminde bloke olup bekleyecek (throttling), böylece memory leak veya OOM (Out of Memory) riskini ortadan kaldıracağız. Derinlik kontrolü için de BFS (Breadth-First Search) mantığıyla queue'ya (url, current_depth) tuple'ları atacağız.