import re

class QueryEngine:
    def __init__(self, indexed_data, index_lock):
        self.indexed_data = indexed_data
        self.index_lock = index_lock

    def search(self, query, top_n=10):
        query = query.lower().strip()
        if not query:
            return []

        query_terms = query.split()
        results = []
        
        with self.index_lock:
            for url, data in self.indexed_data.items():
                text_content = data.get("text", "").lower()
                freq = 0
                
                for term in query_terms:
                    if len(term) < 3:
                        continue
                    matches = re.findall(r'\b' + re.escape(term) + r'\b', text_content)
                    freq += len(matches)
                
                if freq > 0:
                    depth = data.get("depth", 0)
                    origin = data.get("origin", "unknown")
                    # Eğer crawler title çekmiyorsa varsayılan atıyoruz
                    title = data.get("title", "Untitled Document") 
                    
                    # Quiz Formülü
                    score = (freq * 10) + 1000 - (depth * 5)
                    
                    # Arkadaşının formatındaki JSON objesi
                    results.append({
                        "relevant_url": url,
                        "origin_url": origin,
                        "depth": depth,
                        "score": score,
                        "title": title
                    })

        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:top_n]