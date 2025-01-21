'''
Compare relationship between two people between two series (naruto and shippuden)
'''
from DataCollection import Anime
from data.Constants import JJK, NARUTO
from Network import Anime_Network
import community as community_louvain
import matplotlib.pyplot as plt
import networkx as nx
import pandas as pd


class Analysis:
    def __init__(self, anime, save_preprocessing=False):
        # Initialize Network and load or build the graph
        self.network = Anime_Network(anime)

        try:
            self.network = Anime_Network.load_network()
        except Exception as e:
            print(f"Failed to load existing network. Generating a new one... {e}")
            self.network = Anime_Network(anime)
            self.network.preProcessing(save_results=save_preprocessing)
            self.network.network()
        
        # Ensure the network is loaded
        if not self.network.anime_network:
            raise ValueError("Network graph not initialized correctly.")
    
    def cutoff_val(self):
        return self.network.cutoff_weight

    def cutoff_percentage(self):
        return self.network.percentage_removed

    def popularity_score(self, character):
        if character not in self.network.anime_network:
            raise ValueError(f"Character '{character}' not found in the network.")
        
        # Sum up the weights of all edges connected to the character
        return sum(
            d["weight"] for _, _, d in self.network.anime_network.edges(character, data=True)
        )

    def top_relationships(self, character, top_n=3):
        if character not in self.network.anime_network:
            raise ValueError(f"Character '{character}' not found in the network.")
        
        # Get all edges connected to the character
        edges = [
            (neighbor, data["weight"])
            for _, neighbor, data in self.network.anime_network.edges(character, data=True)
        ]
        
        # Sort by weight in descending order and take the top N
        return sorted(edges, key=lambda x: x[1], reverse=True)[:top_n]

    def display_network(self):
        self.network.display_network()

    def display_relationship(self):
        self.network.display_relationship()

    def detect_communities(self):
        if not self.network.anime_network:
            raise ValueError("Network graph not initialized.")
        
        # Compute the best partition using Louvain
        partition = community_louvain.best_partition(self.network.anime_network)
        return partition

    def modularity(self):
        """
        Calculate the modularity score for the detected communities.

        Returns:
            float: The modularity score (0 to 1).
        """
        if not self.network.anime_network:
            raise ValueError("Network graph not initialized.")
        
        partition = self.detect_communities()
        score = community_louvain.modularity(partition, self.network.anime_network)
        return score

    def one_minus_modularity(self):
        """
        Calculate 1 - modularity.

        Returns:
            float: The complementary modularity score.
        """
        return 1 - self.modularity()

    def shortest_path(self, char1, char2):
        """
        Calculate the shortest path and its length between two characters.

        Args:
            char1 (str): First character.
            char2 (str): Second character.

        Returns:
            Tuple[List[str], int]: The shortest path and its length.
        """
        if char1 not in self.network.anime_network or char2 not in self.network.anime_network:
            raise ValueError(f"One or both characters not found in the network.")
        
        path = nx.shortest_path(self.network.anime_network, source=char1, target=char2)
        length = nx.shortest_path_length(self.network.anime_network, source=char1, target=char2)
        return path, length

    def network_diameter(self):
        """
        Calculate the diameter of the network (longest shortest path).

        Returns:
            int: The network diameter.
        """
        if not self.network.anime_network:
            raise ValueError("Network graph not initialized.")
        
        diameter = nx.diameter(self.network.anime_network)
        return diameter

    def visualize_communities(self):
        if not self.network.anime_network:
            raise ValueError("Network graph not initialized.")
        
        # Detect communities
        partition = self.detect_communities()

        # Assign colors to nodes based on their community
        pos = nx.spring_layout(self.network.anime_network)  # Generate a layout for the graph
        cmap = plt.get_cmap("viridis")
        communities = set(partition.values())
        colors = {node: cmap(community / max(communities)) for node, community in partition.items()}

        # Draw the network with node colors based on communities
        plt.figure(figsize=(15, 15))
        nx.draw(
            self.network.anime_network,
            pos,
            node_color=[colors[node] for node in self.network.anime_network.nodes()],
            with_labels=True,
            node_size=500,
            font_size=8,
            edge_color="gray",
        )

        plt.title("Louvain Community Detection", fontsize=16)
        plt.show()

    def get_neighbors(self, character):
        """
        Get all neighbors of a character and their relationship values.

        Args:
            character (str): The name of the character.

        Returns:
            List[Tuple[str, float]]: A list of tuples where each tuple contains
                                    a neighbor and the weight of the edge (relationship value).
        """
        if character not in self.network.anime_network:
            raise ValueError(f"Character '{character}' not found in the network.")
        
        # Retrieve all neighbors and their edge weights
        neighbors = [
            (neighbor, data["weight"])
            for _, neighbor, data in self.network.anime_network.edges(character, data=True)
        ]
        return neighbors

    def longest_path(self):
        """
        Calculate the longest path (network diameter) and return the path, its length, 
        and the two endpoint characters.

        Returns:
            Tuple[List[str], int, str, str]: A tuple containing the longest path (list of characters), 
                                            its length, and the two endpoint characters.
        """
        if not self.network.anime_network:
            raise ValueError("Network graph not initialized.")
        
        if not nx.is_connected(self.network.anime_network):
            raise ValueError("The network graph is not connected, so no single diameter exists.")

        # Find all-pairs shortest paths
        all_pairs_shortest_paths = dict(nx.all_pairs_shortest_path(self.network.anime_network))
        longest_path = []
        max_length = 0
        char1, char2 = None, None

        # Iterate through all shortest paths to find the longest one
        for source, paths in all_pairs_shortest_paths.items():
            for target, path in paths.items():
                if len(path) - 1 > max_length:  # Subtract 1 because length includes nodes, not edges
                    max_length = len(path) - 1
                    longest_path = path
                    char1, char2 = path[0], path[-1]

        return longest_path, max_length, char1, char2

    def weighted_network_diameter(self):
        """
        Calculate the weighted network diameter, which is 1 / network diameter.

        Returns:
            float: Weighted network diameter.
        """
        diameter = self.network_diameter()
        return 1 / diameter if diameter > 0 else float("inf")

    def is_small_world_network(self):
        """
        Check if the network is a small-world network.

        Returns:
            bool: True if the network is small-world, False otherwise.
        """
        if not nx.is_connected(self.network.anime_network):
            raise ValueError("The network graph is not connected.")
        
        avg_shortest_path_length = nx.average_shortest_path_length(self.network.anime_network)
        clustering_coeff = nx.average_clustering(self.network.anime_network)

        # Small-world networks typically have:
        # - High clustering coefficient
        # - Low average shortest path length
        # These thresholds can be adjusted based on the dataset
        return clustering_coeff > 0.5 and avg_shortest_path_length < 6

    def average_shortest_path_length(self):
        """
        Calculate the average shortest path length across all nodes.

        Returns:
            float: Average shortest path length.
        """
        if not nx.is_connected(self.network.anime_network):
            raise ValueError("The network graph is not connected.")
        
        return nx.average_shortest_path_length(self.network.anime_network)

    def clustering_coefficient(self):
        """
        Calculate the clustering coefficient, the percentage of all possible triangles that are complete.

        Returns:
            float: Clustering coefficient.
        """
        return nx.average_clustering(self.network.anime_network)

if __name__ == "__main__":

    anime = Anime("Naruto", NARUTO, include_filler=True)
    analysis = Analysis(anime, save_preprocessing=True)

    print(f"Cutoff Value: {analysis.cutoff_val()}")
    print(f"Cutoff Percentage: {analysis.cutoff_percentage():.2f}%\n")
    print(f"Popularity Score of Naruto Uzumaki: {analysis.popularity_score('Naruto Uzumaki')}\n")
    
    top_relationships = analysis.top_relationships("Naruto Uzumaki")
    print(f"Top 3 Strongest Relationships for Naruto Uzumaki: {top_relationships}\n")

    # Modularity and 1 - Modularity
    modularity = analysis.modularity()
    print(f"Modularity Score: {modularity:.2f}")
    print(f"1 - Modularity Score: {analysis.one_minus_modularity():.2f}\n")

    # Shortest path between two characters
    path, length = analysis.shortest_path("Naruto Uzumaki", "Rock Lee")
    print(f"Shortest Path between Naruto Uzumaki and Rock Lee: {path} (Length: {length:.2f})\n")

    # # Network diameter and longest path
    # longest_path, diameter, char1, char2 = analysis.longest_path()
    # print(f"Longest Path in the Network (Diameter): {longest_path} (Length: {diameter})")
    # print(f"The farthest characters are {char1} and {char2}.\n")

    # Weighted network diameter
    # weighted_diameter = analysis.weighted_network_diameter()
    # print(f"Weighted Network Diameter: {weighted_diameter:.5f}\n")

    # Average shortest path length
    # avg_path_length = analysis.average_shortest_path_length()
    # print(f"Average Shortest Path Length: {avg_path_length:.2f}\n")

    # # Clustering coefficient
    # clustering_coeff = analysis.clustering_coefficient()
    # print(f"Clustering Coefficient: {clustering_coeff:.2f}\n")

    # # Small world network detection
    # is_small_world = analysis.is_small_world_network()
    # print(f"Is the network a small-world network? {'Yes' if is_small_world else 'No'}\n")


    analysis.display_network()

    analysis.visualize_communities()

    analysis.display_relationship()
