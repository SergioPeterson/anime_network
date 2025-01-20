from DataCollection import Anime, Series
from Network import Anime_Network

class Testing:
    """
    A class for debugging and visualizing outputs.

    Includes default example inputs or takes inputs to test on specific cases.
    """
    def __init__(self):
        # Example data for testing
        self.test_series = Series("Jujutsu Kaisen", 40748)
        self.test_anime = Anime("Jujutsu Kaisen", [["Jujutsu Kaisen", 40748], ["Jujutsu Kaisen Season 2", 51009]])

    def test_fetch_episodes(self):
        print("[TEST] Testing fetch_episodes...")
        try:
            self.test_series.fetch_episodes()
            assert len(self.test_series.episodes) > 0, "No episodes were fetched. Check API response."
            print("[PASS] Episodes fetched successfully:")
            for ep in self.test_series.episodes[:5]:  # Show only the first 5 for brevity
                print(ep)
        except Exception as e:
            print("[FAIL] fetch_episodes encountered an error:", e)

    def test_fetch_all_episodes(self):
        print("[TEST] Testing fetch_all_episodes...")
        try:
            self.test_anime.fetch_all_episodes()
            assert len(self.test_anime.all_episodes) > 0, "No episodes were fetched across series."
            print("[PASS] All episodes fetched successfully. Sample data:")
            for ep in self.test_anime.all_episodes[:5]:  # Show only the first 5 for brevity
                print(ep)
        except Exception as e:
            print("[FAIL] fetch_all_episodes encountered an error:", e)

    def test_get_episode_urls(self):
        print("[TEST] Testing get_episode_urls...")
        try:
            self.test_anime.fetch_all_episodes()  # Ensure episodes are fetched
            urls = self.test_anime.get_episode_urls()
            assert len(urls) > 0, "No episode URLs were generated."
            print("[PASS] Episode URLs generated successfully. Sample data:")
            for url in urls[:5]:  # Show only the first 5 for brevity
                print(url)
        except Exception as e:
            print("[FAIL] get_episode_urls encountered an error:", e)

    def test_get_episode_characters(self):
        print("[TEST] Testing get_episode_characters...")
        try:
            self.test_anime.fetch_all_episodes()  # Ensure episodes are fetched
            urls = self.test_anime.get_episode_urls()
            sample_url = urls[0]["url"] if urls else None
            if not sample_url:
                raise ValueError("No valid URL to test.")
            characters = self.test_anime.get_episode_characters(sample_url)
            print("[PASS] Characters fetched successfully for the first episode. Sample characters:", characters[:5])
        except Exception as e:
            print("[FAIL] get_episode_characters encountered an error:", e)

    def test_save_episodes(self):
        print("[TEST] Testing save_episodes...")
        try:
            output_path = "./test_episodes.csv"
            self.test_anime.save_episodes(csv_file_path=output_path, limit=10)
            print(f"[PASS] Episodes saved successfully to {output_path}")
        except Exception as e:
            print("[FAIL] save_episodes encountered an error:", e)

    def test_make_link(self):
        print("[TEST] Testing make_link...")
        try:
            test_title = "It's a Test? Example"
            result = self.test_anime.make_link(test_title)
            expected = "It%27s_a_Test%3F_Example"
            assert result == expected, f"Expected {expected}, got {result}"
            print("[PASS] make_link works as expected.")
        except Exception as e:
            print("[FAIL] make_link encountered an error:", e)

if __name__ == "__main__":
    tester = Testing()
    tester.test_fetch_episodes()
    tester.test_fetch_all_episodes()
    tester.test_get_episode_urls()
    tester.test_get_episode_characters()
    tester.test_save_episodes()
    tester.test_make_link()