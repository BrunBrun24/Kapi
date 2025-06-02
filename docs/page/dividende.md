# 🎯 Objectif de la page « Dividendes »

La page **Dividendes** permet à l'utilisateur de suivre, enregistrer et analyser les revenus générés par les actions détenues dans ses portefeuilles. Elle offre une vision claire des dividendes perçus, par action, par date ou par portefeuille.

---

## 🧭 Parcours utilisateur

### 1. Sélection d’un portefeuille  
L’utilisateur commence par sélectionner un portefeuille existant (préalablement créé sur la page Transactions).

### 2. Affichage des dividendes liés au portefeuille  
Une fois un portefeuille sélectionné, l’utilisateur peut consulter les dividendes associés aux actions présentes dans ce portefeuille. Ces données peuvent être visualisées dynamiquement avec des graphiques.

---

## 📊 Visualisation des dividendes

L’utilisateur dispose d’une visualisation graphique interactive, permettant de :
- voir l’évolution des dividendes **dans le temps** (graphique linéaire ou barres),
- filtrer par **ticker** (menu déroulant ou multi-sélecteur),
- comparer les **dividendes cumulés** par mois, trimestre ou année,
- afficher le **total par action** sur une période donnée (agrégation dynamique).

L’affichage repose sur les composants `shadcn/ui` combinés à une librairie de graphes comme `Recharts` ou `ECharts`, intégrée à React :

- **Graphique 1 : Dividendes par date (barres groupées ou ligne)**
- **Graphique 2 : Total cumulé par ticker**
- **Graphique 3 (optionnel) : Répartition des dividendes par devise ou secteur**

---

## 🧩 Comportement dynamique

- Le champ **ticker** est limité aux actions présentes dans le portefeuille sélectionné.
- Les dividendes peuvent être filtrés par :
  - **date** (sélecteur de plage),
  - **ticker** (multi-sélecteur),
  - **devise**.
- Tri possible par date ou montant décroissant.
- Les graphiques se mettent à jour en temps réel selon les filtres appliqués.

---
