from pathlib import Path

# Contenu du fichier Markdown
markdown_content = """# 🎯 Objectif de la page « Transactions »

La page **Transactions** permet à l'utilisateur de gérer et visualiser l'historique des mouvements financiers (achats/ventes) effectués au sein d'un portefeuille d’actions.

## 🧭 Parcours utilisateur

### Création d’un portefeuille
L’utilisateur peut d’abord créer un ou plusieurs portefeuilles. Un portefeuille représente une collection d’actions que l’utilisateur souhaite suivre ou gérer.

### Ajout d’actions dans un portefeuille sélectionné
Une fois un portefeuille créé et sélectionné, l’utilisateur peut y ajouter des actions (tickers) — ce sont les titres dans lesquels il souhaite investir ou qu’il souhaite suivre.

### Ajout de transactions liées aux actions du portefeuille
Ensuite, l’utilisateur peut enregistrer des transactions (opérations d’achat ou de vente). Ces transactions sont liées uniquement aux actions ajoutées dans le portefeuille sélectionné.

## 👁️ Visualisation des données

Lorsqu’un portefeuille est sélectionné, deux blocs d’informations s’affichent :

- La liste des actions ajoutées à ce portefeuille.
- L’historique des transactions (filtrable, triable) pour ce portefeuille.

L'utilisateur peut ainsi analyser son activité par date, ticker, type d’opération, montant, frais, etc.

## 🧩 Comportement dynamique

- Les transactions proposées sont contextualisées : seules les actions présentes dans le portefeuille sélectionné peuvent être choisies lors de l’ajout d’une nouvelle transaction.
- Les filtres permettent de naviguer efficacement dans l’historique : par date, ticker, type d'opération, etc.
"""

name_file = "transaction"

# Chemin du fichier de sortie
output_path = Path(f"/docs/page/{name_file}.md")

# Écriture du contenu dans le fichier
output_path.write_text(markdown_content, encoding="utf-8")

# Retourner le chemin du fichier généré
output_path.name
