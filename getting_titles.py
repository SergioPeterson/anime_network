from gogoanime import get_search_results, get_anime_details

# Search for the anime
search_results = get_search_results(query="Naruto Shippuden", page=1)

# Assuming the first result is the desired anime
anime_id = search_results[0]['id']

# Get anime details, including episodes
anime_details = get_anime_details(id=anime_id)
total_episodes = anime_details[0]['total_episode']
print(f"Total episodes: {total_episodes}")