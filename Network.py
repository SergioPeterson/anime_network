'''
TODO:
Add testing tools
'''

import csv
from DataCollection import Anime
import matplotlib.pyplot as plt
import numpy as np
import networkx as nx
from tqdm import tqdm


class Network:
    def __init__(self) -> None:
        self.characters_episodes = {}
        self.anime_network = None

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

    def network(self, trimmed=False):
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
                    if (sum(self.characters_episodes[char1]) + sum(self.characters_episodes[char2])) > 2:
                        weight = np.dot(
                            self.characters_episodes[char1], self.characters_episodes[char2]
                        ) / max(sum(self.characters_episodes[char1]), sum(self.characters_episodes[char2]))
                    else:
                        weight = 0
                    # Add the edge with the computed weight
                    self.anime_network.add_edge(char1, char2, weight=weight)

        # Trim the graph if required
        if trimmed:
            cutoff_weight, percentage_removed = self.max_cutoff_for_connected_graph()
            print(f"Graph trimmed. Maximum cutoff weight: {cutoff_weight}")
            print(f"Percentage of edges removed: {percentage_removed:.2f}%")

    def max_cutoff_for_connected_graph(self, print=False):
        """
        Optimized calculation of the maximum weight cutoff such that removing all edges with weight <= cutoff
        keeps the graph connected but not fully connected. Updates the graph accordingly.

        Returns:
            float: The maximum weight cutoff.
            float: Percentage of edges removed.
        """
        if not self.anime_network:
            print("No network data found. Please run network first.")
            return None, None

        # Sort edges by weight in ascending order
        edges_sorted = sorted(self.anime_network.edges(data=True), key=lambda x: x[2]["weight"])
        total_edges = len(edges_sorted)

        # Initialize a Union-Find structure for connectivity checks
        parent = {node: node for node in self.anime_network.nodes}
        rank = {node: 0 for node in self.anime_network.nodes}

        def find(node):
            """Find the representative of the set containing 'node'."""
            if parent[node] != node:
                parent[node] = find(parent[node])  # Path compression
            return parent[node]

        def union(node1, node2):
            """Union of two sets containing 'node1' and 'node2'."""
            root1 = find(node1)
            root2 = find(node2)
            if root1 != root2:
                if rank[root1] > rank[root2]:
                    parent[root2] = root1
                elif rank[root1] < rank[root2]:
                    parent[root1] = root2
                else:
                    parent[root2] = root1
                    rank[root1] += 1

        # Initially, union all nodes connected by an edge
        for u, v, data in edges_sorted:
            union(u, v)

        # Track removed edges
        edges_removed = 0

        for i, (u, v, data) in tqdm(enumerate(edges_sorted), desc="Cutting Graph"):
            # Remove edge by checking connectivity before and after
            if find(u) == find(v):
                edges_removed += 1
                parent[v] = v  # Disconnect u and v

            # Check if the graph is still connected
            connected_components = len(set(find(node) for node in self.anime_network.nodes))
            if connected_components > 1:
                # Return the weight of the last edge before disconnection
                cutoff_weight = edges_sorted[i - 1][2]["weight"] if i > 0 else 0
                percentage_removed = (float(edges_removed) / float(total_edges)) * 100.0

                # Update the graph by keeping edges with weight > cutoff_weight
                edges_to_keep = [
                    (x, y, d) for x, y, d in edges_sorted if d["weight"] > cutoff_weight
                ]
                self.anime_network = self.anime_network.edge_subgraph(edges_to_keep).copy()
                return cutoff_weight, percentage_removed

        # If all edges are removed and the graph is still connected
        cutoff_weight = edges_sorted[-1][2]["weight"]
        if print:
            print(f"The maximum weight cutoff to keep the graph connected: {cutoff_weight}")
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

if __name__ == "__main__":
    # NARUTO
    naruto_series = [
        ["Naruto", 20],
        ["Naruto Shippuden", 1735]
        # ["Boruto", 34566],
    ]
    anime = Anime("Naruto", naruto_series, include_filler=False)

    # # Fetch and save episodes
    # anime.save_episodes()

    # Process the saved episodes and save the character binary matrix
    network = Network()
    network.preProcessing()
    network.network(trimmed=True)

    print(network.get_top_largest_edges())
    print(network.top_friends("Jiraiya"))