import requests

# API endpoint
url = "https://naruto.fandom.com/api.php?action=parse&page=List_of_Animated_Media&format=json"

# Fetch the JSON data
response = requests.get(url)
data = response.json()

# Extract the links array
links = data["parse"]["links"]

# Extract the first 5 episode titles
episode_titles = [link["*"] for link in links[:5]]

# Print the episode titles
print("First 5 episodes:")
for i, title in enumerate(episode_titles, start=1):
    print(f"{i}: {title}")