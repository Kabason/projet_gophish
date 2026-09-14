import pandas as pd

df = pd.read_csv("../../data/processed/dataset_hybride_preprocessed.csv")

matches = df[df["clean_text"].str.contains(r"\baenf\b", case=False, na=False, regex=True)]
print(f"Lignes contenant 'aenf' : {len(matches)}")
print()
for idx, row in matches.head(3).iterrows():
    print("---")
    print("Type:", row["type"])
    print("Language:", row["language"])
    print("Texte original (non nettoye):")
    # On va chercher le texte original correspondant
    df_raw = pd.read_csv("../../data/processed/dataset_hybride_phishing_2026.csv")
    original = df_raw.loc[idx, "text"]
    print(original[:500])