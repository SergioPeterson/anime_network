import csv
import time
from bs4 import BeautifulSoup
import requests
from colorama import Fore, Back, Style
from data.Constants import NARUTO_FANDOM, JJK_FILLER, NARUTO_FILLER, SHIPPUDEN_FILLER, BORUTO_FILLER, JJK_FANDOM

class Series:
    """
    Represents a single anime series or season.

    Attributes:
        name (str): The name of the series.
        episodes (list[dict]): A list of episodes for the series.
        filler_episodes (list[int]): A list of filler episode numbers.
        fandom_link (str): The URL to the fandom page for the series.
    """

    def __init__(self, name: str, fandom_link: str, filler_link: str):
        self.name = name
        self.fandom_link = fandom_link
        self.filler_link = filler_link

    def fetch_episodes(self, include_filler=True) -> list[dict]:
        """Fetch episodes from the fandom link."""
        response = requests.get(self.fandom_link)
        soup = BeautifulSoup(response.text, 'html.parser')
        tables = soup.find_all('table', class_='box table coloured bordered innerbordered style-basic fill-horiz')
        episodes = []

        for table in tables:
            # Find the preceding headings
            sub_heading = table.find_previous('h3')  # Specific subcategory
            main_heading = table.find_previous('h2')  # Main category (e.g., Episodes, Movies)

            if sub_heading and main_heading:
                # Combine main and sub headings for unique categories like "Naruto: Original Movies"
                category_title = f"{main_heading.get_text(strip=True)} - {sub_heading.get_text(strip=True)}"
            elif main_heading:
                # Use the main heading if no subheading is found
                category_title = main_heading.get_text(strip=True)
            else:
                continue
            if category_title == "OVAs - Boruto: Naruto Next Generations":
                category_title = "OVAs"

            rows = table.find_all('tr')[1:]
            for idx, row in enumerate(rows, start=1):  # Use enumerate for dynamic numbering
                cells = row.find_all(['th', 'td'])
                if cells:
                    if category_title == "OVAs":
                        episodes.append({
                            "Number": idx,
                            "Title": cells[0].find('a').text.strip() if cells[0].find('a') else cells[0].text.strip(),
                            "Link": f"https://naruto.fandom.com{cells[0].find('a')['href']}" if cells[0].find('a') else None,
                        })
                    else:
                        episodes.append({
                            "Number": cells[0].text.strip(),
                            "Title": cells[1].find('a').text.strip() if cells[1].find('a') else cells[1].text.strip(),
                            "Link": f"https://naruto.fandom.com{cells[1].find('a')['href']}" if cells[1].find('a') else None,
                        })


        if not include_filler:
            return self.remove_filler(episodes)
        # return episodes

    def remove_filler(self, episodes) -> list[dict]:
        """Fetch filler episodes from the Anime Filler List."""
        response = requests.get(self.filler_link)
        soup = BeautifulSoup(response.text, 'html.parser')
        filler_section = soup.find('div', class_='filler')

        filler_episodes = []
        if filler_section:
            episode_text = filler_section.find('span', class_='Episodes').text.strip()
            for part in episode_text.split(','):
                part = part.strip()
                if '-' in part:
                    start, end = map(int, part.split('-'))
                    filler_episodes.extend(range(start, end + 1))
                else:
                    filler_episodes.append(int(part))
        filler_episodes = sorted(filler_episodes)
        episodes = [ep for ep in episodes if ep['Number'] not in filler_episodes]
        return episodes


class Anime:
    """
    Represents a collection of series, such as a multi-season anime.

    Attributes:
        name (str): The name of the anime.
        all_media (list[dict]): A combined list of all episodes from all series.
        include_filler (bool): Whether to include filler episodes.
    """

    def __init__(self, name: str, include_filler: bool = True):
        self.name = name
        self.all_media = []
        self.include_filler = include_filler

    def fetch_all_episodes(self):
        """Fetch all episodes for the anime based on the series name."""
        series = []
        series_names = self.name.split("-")
        for name in series_names:
            match name:
                case "naruto":
                    series.append(Series("Naruto", NARUTO_FANDOM, NARUTO_FILLER))
                case "shippuden":
                    series.append(Series("Shippuden", NARUTO_FANDOM, SHIPPUDEN_FILLER))
                case "boruto":
                    series.append(Series("Boruto", NARUTO_FANDOM, BORUTO_FILLER))
                case "jjk":
                    series.append(Series("Jujutsu Kaisen", JJK_FANDOM, JJK_FILLER))
                case _:
                    raise ValueError("Unsupported anime name")

        for serie in series:
            episodes = serie.fetch_episodes(self.include_filler)
            self.all_media.extend(episodes)

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
        self.fetch_all_episodes()
        with open(csv_file_path, mode="w", newline="", encoding="utf-8") as file:
            csv_writer = csv.writer(file)
            csv_writer.writerow(["Episode", "Characters"])

            for ep in self.all_media[:limit]:
                characters = self.get_episode_characters(ep["url"], debug=debug_ch)
                csv_writer.writerow([ep["episode"], ", ".join(characters)])

        print(f"Data has been saved to {csv_file_path}")

    def print_episodes(self):
        for episode in self.all_episodes:
            print(episode)
