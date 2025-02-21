# Anime Character Network Analysis

## Project Overview
This project provides tools to analyze and visualize relationships between characters in anime series. It builds a network graph where nodes represent characters and edges represent relationships based on shared episodes. Users can explore various network properties, such as popularity scores, communities, and shortest paths, while also visualizing the data in an interactive format.

### Key Features
- **Character Relationship Network**: Visualize relationships between characters as a network graph.
- **Community Detection**: Identify groups of characters with strong connections using the Louvain algorithm.
- **Network Metrics**: Calculate modularity, clustering coefficient, network diameter, and more.
- **Small-World Network Detection**: Analyze if the network exhibits small-world properties.
- **Interactive Visualization**: Explore the network using PyVis-generated interactive HTML.

---

## Project Structure

```
├── Analytics.py         # Main analysis script with network metrics and visualizations
├── DataCollection.py    # Script to collect and preprocess anime data
├── Network.py           # Builds and manages the character relationship network
├── README.md            # Project documentation (this file)
├── Schema.md            # Data schema and descriptions
├── TestingTools.py      # Tools for testing and validation
├── data                 # Directory for storing processed data
└── requirements.txt     # Python dependencies
```

---

## Getting Started

### Prerequisites
- Python 3.8+
- Libraries listed in `requirements.txt`

### Installation
1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/anime-character-network.git
   cd anime-character-network
   ```
2. Create and activate a virtual environment:
   ```bash
   python -m venv graph_env
   source graph_env/bin/activate  # On Windows, use `graph_env\Scripts\activate`
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

---

## Usage

### Running the Analysis
1. Update `Analytics.py` with the desired anime and series constants (e.g., `JJK`, `NARUTO`).
2. Run the script:
   ```bash
   python Analytics.py
   ```
3. The analysis results will be displayed in the console, and an interactive network visualization will be saved as `character_network.html`.

### Key Outputs
- **Cutoff Value**: Edge weight threshold for pruning weak connections.
- **Popularity Score**: Total edge weights connected to a character.
- **Top Relationships**: Strongest connections for a given character.
- **Community Visualization**: Groups of interconnected characters.
- **Network Metrics**: Diameter, modularity, clustering coefficient, and more.

---

## Example
Analyze relationships in "Naruto":
```python
anime = Anime("Naruto", NARUTO, include_filler=False)
analysis = Analysis(anime, save_preprocessing=True)
```
Output:
```
Cutoff Value: 0.27
Cutoff Percentage: 81.54%
Popularity Score of Naruto Uzumaki: 15.6
Top 3 Strongest Relationships for Naruto Uzumaki: [('Sasuke Uchiha', 0.85), ('Sakura Haruno', 0.8), ('Kakashi Hatake', 0.75)]
Modularity Score: 0.42
1 - Modularity Score: 0.58
Small-World Network: Yes
```

---

## Testing
Run `TestingTools.py` to validate functionality:
```bash
python TestingTools.py
```

---

## Future Work
- Add support for more anime datasets.
- Implement additional metrics (e.g., betweenness centrality).
- Optimize network generation for large datasets.

---

## License
This project is licensed under the MIT License. See the LICENSE file for details.

---

## Contributors
- **Your Name**: [GitHub Profile](https://github.com/SergioPeterson)


## References
[1] E. M. Gordon, T. O. Laumann, B. Adeyemo, J. F. Huckins, W. M. Kelley, and S. E. Petersen, “Generation and Evaluation of a Cortical Area Parcellation from Resting-State Correlations,” Cerebral Cortex, vol. 26, no. 1, pp. 288–303, Oct. 2014, doi: 10.1093/cercor/bhu239.

[2] E. M. Gordon et al., “Precision functional mapping of individual human brains,” Neuron, vol. 95, no. 4, pp. 791-807.e7, Jul. 2017, doi: 10.1016/j.neuron.2017.07.011.

[3] D. Papo, M. Zanin, J. H. Martínez, and J. M. Buldú, “Beware of the Small-World neuroscientist!,” Frontiers in Human Neuroscience, vol. 10, Mar. 2016, doi: 10.3389/fnhum.2016.00096.

[4] J. Hlinka, D. Hartman, N. Jajcay, D. Tomeček, J. Tintěra, and M. Paluš, “Small-world bias of correlation networks: From brain to climate,” Chaos an Interdisciplinary Journal of Nonlinear Science, vol. 27, no. 3, Mar. 2017, doi: 10.1063/1.4977951.
