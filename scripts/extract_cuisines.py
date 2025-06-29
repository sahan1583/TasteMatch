import pandas as pd

df = pd.read_csv("data/zomato.csv", encoding="latin-1")
df = df.rename(columns=lambda x: x.strip().lower().replace(" ", "_"))

df = df.dropna(subset=["cuisines"])

cuisine_set = set()

for item in df["cuisines"]:
    cuisines = [c.strip() for c in item.split(",")]
    cuisine_set.update(cuisines)

all_cuisines = sorted(cuisine_set)

print(f"Total unique cuisines: {len(all_cuisines)}")
print(all_cuisines)

with open("data/unique_cuisines.txt", "w") as f:
    for c in all_cuisines:
        f.write(c + "\n")
