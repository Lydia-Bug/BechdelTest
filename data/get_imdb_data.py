import kagglehub

# Download latest version
path = kagglehub.dataset_download("adriankiezun/imdb-dataset-2023")

print("Path to dataset files:", path)