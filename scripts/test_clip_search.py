from app.utils.clip_utils import encode_image, find_similar_cuisines, load_precomputed_cuisine_embeddings

cuisine_names, cuisine_embeddings = load_precomputed_cuisine_embeddings()
image_embedding = encode_image("data/sample_icecream.png")

top_matches = find_similar_cuisines(image_embedding, cuisine_embeddings, cuisine_names)
print("Top matches:", top_matches)
