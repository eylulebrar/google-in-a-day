import json
import os

class PersistenceManager:
    """Sistemin durumunu (Snapshot) diske kaydeder ve geri yükler."""
    def __init__(self, filepath="data/snapshot.json"):
        self.filepath = filepath
        # data klasörü yoksa oluştur
        os.makedirs(os.path.dirname(self.filepath), exist_ok=True)

    def save_state(self, visited, queue_list, indexed_data):
        """Tüm sistem durumunu JSON olarak diske yazar."""
        # Kuyruktaki (url, depth) tuple'larını JSON'da saklamak için liste yapıyoruz
        state = {
            "visited": list(visited),
            "queue": list(queue_list), 
            "indexed_data": indexed_data
        }
        try:
            with open(self.filepath, "w", encoding="utf-8") as f:
                json.dump(state, f, ensure_ascii=False, indent=4)
            return True
        except Exception:
            return False

    def load_state(self):
        """Eğer varsa, diskteki son durumu geri yükler."""
        if not os.path.exists(self.filepath):
            return None
        try:
            with open(self.filepath, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return None