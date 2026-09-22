import matplotlib.pyplot as plt
import numpy as np

# Taux de clic GoPhish par tactique (campagne IA-Protocole-V1)
# Note : le protocole ne distingue pas les tactiques individuellement,
# on utilise le taux global 62.5% pour toutes les tactiques
# (affine si tu as le detail par tactique dans tes CSV GoPhish)
tactics = ["urgence", "autorite", "curiosite", "reciprocite", "routine"]

taux_clic = {
    "urgence": 62.5,
    "autorite": 62.5,
    "curiosite": 62.5,
    "reciprocite": 62.5,
    "routine": 62.5,
}

taux_detection = {
    "urgence": 100.0,
    "autorite": 100.0,
    "curiosite": 100.0,
    "reciprocite": 100.0,
    "routine": 100.0,
}

n_detection = {
    "urgence": 9,
    "autorite": 10,
    "curiosite": 8,
    "reciprocite": 3,
    "routine": 7,
}

x = np.arange(len(tactics))
width = 0.35

fig, ax = plt.subplots(figsize=(10, 6))

bars1 = ax.bar(x - width/2, [taux_clic[t] for t in tactics],
               width, label="Taux de clic humain (GoPhish)", color="#C44E52", alpha=0.85)
bars2 = ax.bar(x + width/2, [taux_detection[t] for t in tactics],
               width, label="Taux de détection NLP (modèle)", color="#4C72B0", alpha=0.85)

# Valeurs au-dessus des barres
for bar in bars1:
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1,
            f"{bar.get_height():.0f}%", ha="center", va="bottom", fontsize=9, fontweight="bold")

for i, bar in enumerate(bars2):
    n = n_detection[tactics[i]]
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1,
            f"{bar.get_height():.0f}%\n(n={n})", ha="center", va="bottom", fontsize=8)

ax.set_xticks(x)
ax.set_xticklabels(tactics, fontsize=11)
ax.set_ylabel("Taux (%)", fontsize=12)
ax.set_ylim(0, 120)
ax.set_title(
    "Synthèse croisée : Efficacité humaine vs Détectabilité automatique par tactique\n"
    "Taux de clic GoPhish (protocole Jagatic 2007) · Détection NLP sur test set uniquement",
    fontsize=11, pad=12
)
ax.legend(fontsize=11)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.grid(axis="y", linestyle="--", alpha=0.4)

# Note méthodologique
ax.text(0.5, -0.13,
        "* Taux de clic uniforme : le protocole pré-enregistré ne distingue pas les tactiques individuellement.\n"
        "  Taux de détection NLP sur échantillons petits (n=3 à 10) — à interpréter avec prudence.",
        transform=ax.transAxes, ha="center", fontsize=8, color="gray", style="italic")

plt.tight_layout()
plt.savefig("figure19_synthese_croisee.png", dpi=200, bbox_inches="tight")
print("Figure 19 sauvegardée : figure19_synthese_croisee.png")