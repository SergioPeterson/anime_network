'''
TODO:
Add and check meta data
    make sure that if re run with slightly diff perams it will warn you and re run not just give you the old one
'''

import csv
import os
from DataCollection import Anime
import matplotlib.pyplot as plt
import numpy as np
import networkx as nx
from tqdm import tqdm
from data.Constants import ALL_NARUTO, JJK, NETWORK_FILE
import pickle


class Network:
    def __init__(self, anime) -> None:
        self.cutoff_weight = None
        self.percentage_removed = None
        self.characters_episodes = {}
        self.anime_network = None
        self.anime = anime

    def preProcessing(self, save_results=False):
        """
        Process the episodes CSV file and generate a binary representation of characters' appearances per episode.

        Args:
            save_results (bool): Whether to save the resulting dictionary to a CSV file.

        Saves:
            A CSV file where each row represents a character and their binary appearances across episodes.
        """
        # Step 1: Read the input CSV and extract episode and character data
        all_episode_characters = {}
        if not os.path.exists("./data/episodes.csv"):
            self.anime.save_episodes()

        with open("./data/episodes.csv", mode="r", encoding="utf-8") as file:
            csv_reader = csv.reader(file)
            next(csv_reader)  # Skip the header
            for row in csv_reader:
                episode = row[0]
                characters = row[1].split(", ") if row[1].strip() else []  # Handle empty character lists
                if characters:  # Skip episodes with no characters
                    all_episode_characters[episode] = characters

        # Step 2: Get a sorted list of all episode numbers
        all_episode_numbers = sorted(
            int(episode.split("Episode ")[1]) for episode in all_episode_characters.keys()
        )

        # Step 3: Create a dictionary to store binary representation for each character
        for episode, characters in all_episode_characters.items():
            episode_number = int(episode.split("Episode ")[1])
            for character in characters:
                if character not in self.characters_episodes:
                    self.characters_episodes[character] = [0] * len(all_episode_numbers)
                # Mark the character as present (1) in the current episode
                self.characters_episodes[character][all_episode_numbers.index(episode_number)] = 1

        # Step 4: Filter out characters who appear in fewer than three episodes
        filtered_characters_episodes = {
            character: appearances
            for character, appearances in self.characters_episodes.items()
            if sum(appearances) >= 3
        }
        self.characters_episodes = filtered_characters_episodes

        # Step 5: Save the results if requested
        if save_results:
            with open("./data/characters.csv", mode="w", newline="", encoding="utf-8") as file:
                csv_writer = csv.writer(file)
                for character, appearances in self.characters_episodes.items():
                    csv_writer.writerow([character] + appearances)

    def network(self, trimmed=True, save=True):
        """
        Build a graph where nodes represent characters and edges represent relationships
        based on their appearances in episodes.

        Args:
            trimmed (bool): If True, trim the graph using max_cutoff_for_connected_graph to remove weaker edges 
                            while keeping the graph connected.
        """
        if not self.characters_episodes:
            print("No character data found. Please run preProcessing first.")
            return

        # Initialize the graph
        self.anime_network = nx.Graph()

        # Add nodes for each character
        for character in self.characters_episodes.keys():
            self.anime_network.add_node(character)

        # Add edges with weights (dot products) between all pairs of characters
        characters = list(self.characters_episodes.keys())
        for i, char1 in tqdm(enumerate(characters), desc="Building Graph"):
            for j, char2 in enumerate(characters):
                if i < j:  # Avoid duplicate edges and self-loops
                    # Compute the dot product of their episode lists
                    weight = np.dot(
                        self.characters_episodes[char1], self.characters_episodes[char2]
                    ) / max(sum(self.characters_episodes[char1]), sum(self.characters_episodes[char2]))
                    self.anime_network.add_edge(char1, char2, weight=weight)

        # Trim the graph if required
        if trimmed:
            cutoff_weight, percentage_removed = self.max_cutoff_for_connected_graph()
            print(f"Graph trimmed. Maximum cutoff weight: {cutoff_weight}")
            print(f"Percentage of edges removed: {percentage_removed:.2f}%")

        if save:
            self.save_network()

    def max_cutoff_for_connected_graph(self):
        """
        Calculate the maximum weight cutoff such that removing all edges with weight <= cutoff
        keeps the graph connected but not fully connected, and update the graph accordingly.
        Returns:
            float: The maximum weight cutoff.
            float: Percentage of edges removed.
            nx.Graph: The updated graph with edges removed.
        """
        if not self.anime_network:
            print("No network data found. Please run network first.")
            return None, None, None
        # Sort edges by weight in ascending order
        edges_sorted = sorted(self.anime_network.edges(data=True), key=lambda x: x[2]["weight"])
        total_edges = len(edges_sorted)
        for i, (u, v, data) in enumerate(edges_sorted):
            # Create a copy of the graph to test edge removal
            graph_copy = self.anime_network.copy()
            # Remove edges with weight <= current edge weight
            edges_to_remove = [(x, y) for x, y, d in edges_sorted[:i + 1]]
            graph_copy.remove_edges_from(edges_to_remove)
            # Check if the graph is still connected
            if not nx.is_connected(graph_copy):
                # Return the weight of the last edge before disconnection
                cutoff_weight = edges_sorted[i - 1][2]["weight"] if i > 0 else 0
                edges_to_keep = [(x, y) for x, y, d in edges_sorted if d["weight"] > cutoff_weight]
                updated_graph = self.anime_network.edge_subgraph(edges_to_keep).copy()
                edges_removed = len(edges_to_remove) - 1
                percentage_removed = (float(edges_removed) / float(total_edges)) * 100.00
                # Update the main network graph
                self.anime_network = updated_graph
                self.cutoff_weight = cutoff_weight
                self.percentage_removed = percentage_removed
                return cutoff_weight, percentage_removed
        # If all edges are removed and the graph is still connected
        cutoff_weight = edges_sorted[-1][2]["weight"]
        return cutoff_weight, 0
    
    def display_network(self, min_edge=0):
        """
        Visualize the character relationship network as a graph with edges filtered by a minimum weight.

        Args:
            min_edge (float): The minimum weight for edges to be displayed.
        """
        if not self.anime_network:
            print("No network data found. Please run network first.")
            return

        # Filter edges by the minimum weight
        filtered_edges = [
            (u, v, d) for u, v, d in self.anime_network.edges(data=True) if d["weight"] >= min_edge
        ]
        # Create a subgraph with filtered edges
        H = nx.Graph()
        H.add_edges_from(filtered_edges)
        # Add isolated nodes to ensure all characters are displayed
        H.add_nodes_from(self.anime_network.nodes)

        # Visualize the subgraph with filtered edges
        plt.figure(figsize=(15, 15))  # Adjust the figure size
        pos = nx.spring_layout(H)  # Generate a layout for the graph
        nx.draw(
            H,
            pos,
            with_labels=True,
            node_color="lightblue",
            node_size=500,
            font_size=8,
            edge_color="gray",
        )

        # Add edge labels (weights)
        edge_labels = nx.get_edge_attributes(H, "weight")
        nx.draw_networkx_edge_labels(H, pos, edge_labels=edge_labels, font_size=7)

        # Title and display
        plt.title(f"Character Relationship Network (min_edge={min_edge})", fontsize=16)
        plt.show()

    def display_relationship(self):
        """
        Visualize the relationship between characters and their appearances across episodes using a heatmap.
        """
        # Step 1: Extract characters and their binary appearance data
        data = self.characters_episodes
        if not data:
            print("No character data found. Please run preProcessing first.")
            return

        characters = list(data.keys())
        episodes = range(1, len(next(iter(data.values()))) + 1)
        matrix = np.array([data[char] for char in characters])

        # Step 2: Plot the heatmap
        fig, ax = plt.subplots(figsize=(15, 12))
        im = ax.imshow(matrix, cmap="Blues", aspect="auto")

        # Set ticks and labels
        ax.set_xticks(np.arange(len(episodes)))
        ax.set_yticks(np.arange(len(characters)))
        ax.set_xticklabels([f"{ep}" for ep in episodes], fontsize=8)
        ax.set_yticklabels(characters, fontsize=6)

        # Rotate the tick labels for better readability
        plt.setp(ax.get_xticklabels(), rotation=45, ha="right", rotation_mode="anchor")

        # Add a colorbar
        plt.colorbar(im, label="Appearance (1 = Present, 0 = Absent)")

        # Set titles and labels
        plt.title("Character Appearances Across Episodes", fontsize=14)
        plt.xlabel("Episodes", fontsize=12)
        plt.ylabel("Characters", fontsize=12)

        # Adjust layout for better spacing
        plt.tight_layout()

        # Show the heatmap
        plt.show()

    def relation_val(self, char1, char2):
        return self.anime_network[char1][char2]['weight']

    def get_top_largest_edges(self, top_n=5):
        """
        Returns the top `top_n` largest edges by weight in the graph.

        Args:
            graph (nx.Graph): The input graph with weighted edges.
            top_n (int): Number of largest edges to return.

        Returns:
            List[Tuple[str, str, int]]: A list of tuples where each tuple contains
                                        two nodes and the weight of the edge.
        """
        # Extract edges with weights and sort by weight in descending order
        edges = [(u, v, d["weight"]) for u, v, d in self.anime_network.edges(data=True)]
        edges_sorted = sorted(edges, key=lambda x: x[2], reverse=True)

        # Return the top `top_n` edges
        return edges_sorted[:top_n]

    def top_friends(self,character, top_n=5):
        edges = [(u, v, d["weight"]) for u, v, d in self.anime_network.edges(character, data=True)]
        edges_sorted = sorted(edges, key=lambda x: x[2], reverse=True)
        return edges_sorted[:top_n]

    def save_network(self):
        """
        Save the graph and characters_episodes to a file using pickle.
        """
        if not self.anime_network:
            print("No network to save. Please run network first.")
            return
        if not self.characters_episodes:
            print("No character data to save. Please run preProcessing first.")
            return

        with open(NETWORK_FILE, 'wb') as f:
            pickle.dump(self, f)
        print(f"Graph and character data saved to {NETWORK_FILE}")

    @staticmethod
    def load_network():
        """
        Load the graph and characters_episodes from a file.

        Returns:
            Network: The loaded Network object.
        """
        with open(NETWORK_FILE, 'rb') as f:
            data = pickle.load(f)
        print(f"Graph and character data loaded from {NETWORK_FILE}")
        return data

if __name__ == "__main__":
    # NARUTO
    anime = Anime("Jujutsu Kaisen", JJK, include_filler=True)
    network = Network(anime)

    try:
        network.load_network()
    except Exception:
        network.preProcessing()
        network.network()

    network.display_network()
