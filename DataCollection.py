import csv
import time
from bs4 import BeautifulSoup
import requests
from colorama import Fore, Back, Style


class Series:
    """
    Represents a single anime series or season.

    Attributes:
        name (str): The name of the series.
        mal_id (int): The MyAnimeList ID for the series.
        episodes (list): A list of episodes for the series.
    """
    def __init__(self, name, mal_id):
        self.name = name
        self.mal_id = mal_id
        self.url_template = f"https://api.jikan.moe/v4/anime/{self.mal_id}/episodes"
        self.episodes = []
        self.filler_episodes = []

    def fetch_episodes(self, offset=0, debug=False):
        """
        Fetch episodes for the series and store them in the episodes attribute.

        Args:
            offset (int): The starting episode number for this series (default: 0).
        """
        page = 1
        while True:
            url = f"{self.url_template}?page={page}"
            response = requests.get(url)

            if response.status_code != 200:
                print(Fore.RED + f"[ERROR] Error {response.status_code} at {url}")
                print(Style.RESET_ALL)
                break

            data = response.json()
            for ep in data.get("data", []):
                self.episodes.append({
                    "series": self.name,
                    "episode_number": offset + ep["mal_id"],
                    "title": ep["title"]
                })
                if debug:
                    print(f"[DEBUG] {self.episodes[-1]}")
                    time.sleep(0.5)

            # Stop if there are no more pages
            if not data.get("pagination", {}).get("has_next_page"):
                break

            page += 1

    def get_url_template(self):
        return self.url_template
    
    def get_episodes(self):
        return self.episodes
    
    def get_filler_episodes(self):
        return self.filler_episodes

class Anime:
    """
    Represents a collection of series, such as a multi-season anime.

    Attributes:
        name (str): The name of the anime.
        series_list (list): A list of Series objects.
        all_episodes (list): A combined list of all episodes from all series.
        include_filler (bool): Whether to include filler episodes.
    """
    def __init__(self, name, series_info, include_filler=True):
        self.name = name
        self.series_list = [Series(name, mal_id) for name, mal_id in series_info]
        self.all_episodes = []
        self.include_filler = include_filler

    def fetch_all_episodes(self, debug=False):
        """
        Fetch episodes for all series, filter by filler preference, and store them in the all_episodes attribute.
        """
        offset = 0

        for series in self.series_list:
            series.fetch_episodes(offset, debug=debug)
            self.all_episodes.extend(series.episodes)
            if series.episodes:
                offset = series.episodes[-1]["episode_number"]
    
    @staticmethod
    def make_link(episode_title):
        replacements = {
            " ": "_",
            "'s": "%27s",
            "?": "%3F",
        }
        for old, new in replacements.items():
            episode_title = episode_title.replace(old, new)
        return episode_title

    def get_episode_urls(self):
        """
        Generate URLs for each episode for the Fandom Wiki or any source.
        """
        base_url = f"https://{self.name.lower().replace(" ", "-")}.fandom.com/wiki/"
        if self.name == "Naruto":
            base_url = f"{base_url}"
            episode_urls = [
                {"episode": f"Episode {ep['episode_number']}", "url": f"{base_url}{self.make_link(ep['title'])}"}
                for ep in self.all_episodes
            ]
        elif self.name == "Jujutsu Kaisen":
            base_url = f"{base_url}Episode_"
            episode_urls = [
                {"episode": f"Episode {ep['episode_number']}", "url": f"{base_url}{ep['episode_number']}"}
                for ep in self.all_episodes
            ]
        else:
            raise NotImplementedError(f"Episode URL generation is not implemented for {self.name}.")
        return episode_urls

    def get_episode_characters(self, episode_url, debug=False, deep_debug=False):
        """
        Scrape characters from a given episode URL.

        Args:
            episode_url (str): The URL of the episode page.

        Returns:
            list: A list of characters appearing in the episode.
        """
        response = requests.get(episode_url)
        if response.status_code != 200:
            print(Fore.YELLOW + f"[WARNING]Failed to fetch episode page {episode_url}: {response.status_code}")
            print(Style.RESET_ALL)
            return []

        soup = BeautifulSoup(response.text, "html.parser")
        characters = []
        if self.name == "Naruto":
            tbodies = soup.find_all("tbody")  # Find all tbody elements
            for tbody in tbodies:
                if deep_debug:
                    print(f"[DEEP DEBUG] Checking tbody: {tbody}")

                # Check if the parent table matches the unwanted table
                parent_table = tbody.find_parent("table")
                if parent_table and "headnote" in parent_table.get("class", []):
                    if deep_debug:
                        print("[DEEP DEBUG] Skipping unwanted table")
                    continue  # Skip this table and move to the next one

                # Process the rows in the valid table
                rows = tbody.find_all("tr")
                for row in rows:
                    if deep_debug:
                        print(f"[DEEP DEBUG] Row is: {row}")
                    first_column = row.find("td")
                    if first_column:
                        link = first_column.find("a")
                        character_name = link.text.strip() if link else first_column.text.strip()
                        characters.append(character_name)
                        
        elif self.name == "Jujutsu Kaisen":
            heading = soup.find("span", id="Characters_in_Order_of_Appearance")
            if heading:
                h2 = heading.find_parent("h2")
                if h2:
                    next_element = h2.find_next_sibling()
                    ul = next_element if next_element.name == "ul" else next_element.find("ul") if next_element and next_element.name == "div" else None
                    if ul:
                        for li in ul.find_all("li"):
                            a_tag = li.find("a")
                            character_name = a_tag.text.strip() if a_tag else li.text.strip()
                            characters.append(character_name)
                    else:
                        print("Character list not found after heading.")
                else:
                    print("Parent <h2> not found for the heading.")
            else:
                print("Heading 'Characters in Order of Appearance' not found.")
        else:
            raise NotImplementedError(f"Character scraping is not implemented for {self.name}.")
        if debug or deep_debug:
            if characters==['']:
                print(f"\n[WARNING] No characters found in episode {episode_url}\n")
            else:
                print(f"[DEBUG] Characters in episode {episode_url}: {characters}")
        return characters

    def save_episodes(self, csv_file_path="./data/episodes.csv", limit=None, debug_ep=False, debug_ch=False):
        """
        Save all episodes and characters to a CSV file.

        Args:
            csv_file_path (str): Path to the output CSV file.
            limit (int): Limit the number of episodes processed.
        """
        self.fetch_all_episodes(debug=debug_ep)
        episode_urls = self.get_episode_urls()
        with open(csv_file_path, mode="w", newline="", encoding="utf-8") as file:
            csv_writer = csv.writer(file)
            csv_writer.writerow(["Episode", "Characters"])

            for ep in episode_urls[:limit]:
                characters = self.get_episode_characters(ep["url"], debug=debug_ch)
                csv_writer.writerow([ep["episode"], ", ".join(characters)])

        print(f"Data has been saved to {csv_file_path}")

    def print_episodes(self):
        for episode in self.all_episodes:
            print(episode)

if __name__ == "__main__":
    pass