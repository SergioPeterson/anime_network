'''
Compare relationship between two people between two series (naruto and shippuden)
Modulartiy - score between 0 and 1 1 means clear communties and 0 means no communties
1-modularity
the length between two characters (along with the path)
longest path in the network - network diametar
'''
from DataCollection import Anime
from data.Constants import JJK
from Network import Anime_Network
import community as community_louvain
import matplotlib.pyplot as plt
import networkx as nx


class Analysis:
    def __init__(self, anime):
        # Initialize Network and load or build the graph
        self.network = Anime_Network(anime)

        try:
            self.network = Anime_Network.load_network()
        except Exception as e:
            print(f"Failed to load existing network. Generating a new one... {e}")
            self.network = Anime_Network(anime)
            self.network.preProcessing()
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

if __name__ == "__main__":
    anime = Anime("Jujutsu Kaisen", JJK, include_filler=True)
    analysis = Analysis(anime)

    # print(f"Cutoff Value: {analysis.cutoff_val()}")
    # print(f"Cutoff Percentage: {analysis.cutoff_percentage():.2f}%")
    # print(f"Popularity Score of Yuji Itadori: {analysis.popularity_score('Yuji Itadori')}")
    
    # top_relationships = analysis.top_relationships("Yuji Itadori")
    # print(f"Top 3 Strongest Relationships for Yuji Itadori: {top_relationships}")

    # # Detect and display communities
    # communities = analysis.detect_communities()
    # print(f"Detected Communities: {communities}")

    # # Modularity and 1 - Modularity
    # modularity = analysis.modularity()
    # print(f"Modularity Score: {modularity:.2f}")
    # print(f"1 - Modularity Score: {analysis.one_minus_modularity():.2f}")

    # # Shortest path between two characters
    # path, length = analysis.shortest_path("Yuji Itadori", "Satoru Gojo")
    # print(f"Shortest Path between Yuji Itadori and Satoru Gojo': {path} (Length: {length:.2f})")

    # # Network diameter
    # diameter = analysis.network_diameter()
    # print(f"Network Diameter: {diameter}")

    # print(f"The neighbors of itadori {analysis.get_neighbors("Yuji Itadori")}")
    analysis.display_network()
