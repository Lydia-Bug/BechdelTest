import requests
from bs4 import BeautifulSoup
import re
import csv
from collections import defaultdict

# Gets all individual year page links 
URL = "https://bechdeltest.com/year/"
page = requests.get(URL)
soup = BeautifulSoup(page.content, "html.parser")
content = soup.find(id="content")
links = [a.get("href") for a in content.find_all("a")]


# Gets movie data from each page
all_movies = []

for link in links:
    year_link = "https://bechdeltest.com" + link
    year_page = requests.get(year_link)
    year_soup = BeautifulSoup(year_page.content, "html.parser")
    year_content = year_soup.find(id="content")

    movies = year_content.find_all("div", class_="movie")

    for movie in movies:
        a_tags = movie.find_all("a")

        first_a = a_tags[0]
        second_a = a_tags[1]

        imdb_href = first_a.get("href", "")
        imdb_match = re.search(r"tt\d+", imdb_href)
        # If theres no imdb id, then I can't use the datapoint with the imdb dataset
        if not imdb_match:
            continue
        imdb_id = imdb_match.group(0)

        name = second_a.text.strip()

        img = first_a.find("img")
        score = int(img.get("alt").strip("[]"))
        explanation = img.get("title").strip("[]")

        all_movies.append({
            "imdb_id": imdb_id,
            "score": score,
            "explanation": explanation,
            "name": name
        })

# Dedupe by imdb_id:
#   - if all rows for an imdb_id share the same score, keep just one of them
#   - if they disagree on score, drop all rows for that imdb_id (can't tell
#     which one is correct)
by_id = defaultdict(list)
for movie in all_movies:
    by_id[movie["imdb_id"]].append(movie)

deduped_movies = []
n_collapsed = 0
n_dropped = 0

for imdb_id, rows in by_id.items():
    if len(rows) == 1:
        deduped_movies.append(rows[0])
        continue

    scores = {row["score"] for row in rows}
    if len(scores) == 1:
        # Same score across all duplicates - keep just the first one
        deduped_movies.append(rows[0])
        n_collapsed += len(rows) - 1
    else:
        # Conflicting scores for the same movie - drop them all
        n_dropped += len(rows)

all_movies = deduped_movies

print(f"Collapsed {n_collapsed} duplicate rows with matching scores")
print(f"Dropped {n_dropped} rows with conflicting scores for the same imdb_id")

# Save to CSV
with open("data/bechdel_movies.csv", "w", newline="", encoding="utf-8") as f:
    fieldnames = ["imdb_id", "score", "explanation", "name"]
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(all_movies)

print("Saved to bechdel_movies.csv")