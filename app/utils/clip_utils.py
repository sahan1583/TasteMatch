import clip
import torch
from PIL import Image

device = "cuda" if torch.cuda.is_available() else "cpu"

# Load model once
model, preprocess = clip.load("ViT-B/32", device=device)

def encode_cuisine_labels(cuisine_list):
    with torch.no_grad():
        text_tokens = clip.tokenize(cuisine_list).to(device)
        text_embeddings = model.encode_text(text_tokens)
        text_embeddings = text_embeddings.to(dtype=torch.float32)  
        text_embeddings /= text_embeddings.norm(dim=-1, keepdim=True)
    return text_embeddings


def encode_image(image_path: str):
    with torch.no_grad():
        # Load the image using PIL 
        image = Image.open(image_path).convert("RGB")
        image_input = preprocess(image).unsqueeze(0).to(device)
        image_embedding = model.encode_image(image_input).to(dtype=torch.float32)
        image_embedding /= image_embedding.norm(dim=-1, keepdim=True)
    return image_embedding



def find_similar_cuisines(
    image_embedding: torch.Tensor,
    cuisine_embeddings: torch.Tensor,
    cuisine_names: list[str],
    top_k: int = 5,
    similarity_threshold: float = 0.2
) -> list[tuple[str, float]]:
    
    similarities = (image_embedding @ cuisine_embeddings.T).squeeze(0)
    similarities_np = similarities.cpu().numpy()

    cuisine_similarity_pairs = [
        (cuisine_names[i], float(score)) for i, score in enumerate(similarities_np)
    ]

    cuisine_similarity_pairs.sort(key=lambda x: x[1], reverse=True)

    filtered_cuisines = [
        (cuisine, score)
        for cuisine, score in cuisine_similarity_pairs
        if score >= similarity_threshold
    ][:top_k]

    return filtered_cuisines


def load_precomputed_cuisine_embeddings(path: str = "data/cuisine_embeddings.pt"):
    data = torch.load(path, map_location=device)
    embeddings = data["embeddings"].to(dtype=torch.float32, device=device)
    return data["cuisine_names"], data["embeddings"].to(device)
