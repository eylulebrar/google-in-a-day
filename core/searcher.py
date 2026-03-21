import threading
import re

class QueryEngine:
    """
    Live indexing sırasında thread-safe arama yapmayı sağlayan ve
    kelime frekansına (TF) göre sonuçları sıralayan arama motoru.
    """
    def __init__(self, index_data_ref, index_lock_ref):
        # ConcurrencyManager'daki referansları alıyoruz ki aynı bellek alanına bakalım
        self.indexed_data = index_data_ref
        self.index_lock = index_lock_ref

    def search(self, query, top_n=10):
        query = query.lower().strip()
        if not query:
            return []

        # YENİ: Sorguyu kelimelere böl (Tokenization)
        query_terms = query.split()
        results = []
        
        with self.index_lock:
            for url, data in self.indexed_data.items():
                text_content = data.get("text", "").lower()
                score = 0
                
                # Her bir terimin frekansını (TF) ayrı ayrı hesapla ve topla
                for term in query_terms:
                    # 3 karakterden kısa kelimeleri (ve, bir, bu vb.) skora katma (Stop-words mantığı)
                    if len(term) < 3:
                        continue
                    # Sadece o kelimeyi ara
                    matches = re.findall(r'\b' + re.escape(term) + r'\b', text_content)
                    score += len(matches)
                
                if score > 0:
                    results.append({
                        "score": score,
                        "url": url,
                        "origin": data.get("origin", "N/A"),
                        "depth": data.get("depth", 0)
                    })

        results.sort(key=lambda x: x["score"], reverse=True)
        
        formatted_results = []
        for res in results[:top_n]:
            formatted_results.append((res["url"], res["origin"], res["depth"]))
            
        return formatted_results

# Ufak bir test bloğu
if __name__ == "__main__":
    # Sahte bir veritabanı simülasyonu
    mock_lock = threading.Lock()
    mock_data = {
        "https://example.com/page1": {
            "text": "python programlama python öğrenmek çok zevkli", 
            "origin": "https://example.com", 
            "depth": 1
        },
        "https://example.com/page2": {
            "text": "sadece bir kez geciyor", 
            "origin": "https://example.com", 
            "depth": 1
        }
    }
    
    engine = QueryEngine(mock_data, mock_lock)
    print("Arama Sonuçları ('python'):")
    for result in engine.search("python"):
        print(result)