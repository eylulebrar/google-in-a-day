import os

class CLIDashboard:
    """
    Provides a clean terminal-based interface to visualize 
    real-time system metrics and crawling progress.
    """
    def __init__(self):
        pass

    def display_metrics(self, processed_count, queue_depth, throttling_status, total_indexed):
        """Prints a formatted table of system metrics."""
        
        # Throttling durumunu daha dikkat çekici yazalım
        status_text = "ACTIVE (Back-pressure)" if throttling_status else "Normal / Stable"
        
        print("\n" + "="*20 + " SYSTEM DASHBOARD " + "="*20)
        print(f"{'Metric':<25} | {'Value':<25}")
        print("-" * 58)
        print(f"{'Processed URLs':<25} | {processed_count:<25}")
        print(f"{'Current Queue Depth':<25} | {queue_depth:<25} / 200")
        print(f"{'System Load Status':<25} | {status_text:<25}")
        print(f"{'Total Indexed Pages':<25} | {total_indexed:<25}")
        print("=" * 58 + "\n")

    def clear_screen(self):
        """Clears the terminal (optional for a cleaner UI)."""
        os.system('cls' if os.name == 'nt' else 'clear')