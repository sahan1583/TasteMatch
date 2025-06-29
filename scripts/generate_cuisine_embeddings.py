import torch
from app.utils.clip_utils import encode_cuisine_labels
from pathlib import Path


cuisine_path = Path("data/unique_cuisines.txt")
cuisine_list = cuisine_path.read_text().splitlines()

embeddings = encode_cuisine_labels(cuisine_list)

embeddings = embeddings.to(dtype=torch.float32)

torch.save({
    "cuisine_names": cuisine_list,
    "embeddings": embeddings.cpu()
}, "data/cuisine_embeddings.pt")

print("Saved cuisine embeddings to data/cuisine_embeddings.pt")