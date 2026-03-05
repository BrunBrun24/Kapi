# 📈 StockTrack & Analytics Dashboard

> **Un screener boursier complet et un tracker de portefeuille haute performance.**
> Développé avec une architecture moderne découplée (Python/Django & Next.js).

---

## 🚀 Présentation du projet
Ce projet est une plateforme d'analyse financière permettant aux investisseurs de suivre leur portefeuille en temps réel et de screener le marché (Actions, ETF, Indices). L'outil offre une vision profonde des fondamentaux pour faciliter la prise de décision.

### 🔍 Fonctionnalités clés
* **Tracking de Portefeuille :** Suivi de la performance globale, plus-values latentes et pondération des lignes.
* **Screener Fondamental :** Analyse des métriques clés (Free Cash Flow, EPS, P/E Ratio, ROE, etc.).
* **Suivi Multi-Actifs :** Support complet pour les actions individuelles, les ETF et les indices mondiaux.
* **Visualisation de données :** Graphiques dynamiques pour l'évolution historique des prix et des indicateurs financiers.

---

## 🛠 Stack Technique

| Composant | Technologie | Rôle |
| :--- | :--- | :--- |
| **Backend** | ![Python](https://img.shields.io/badge/Python-3776AB?style=flat&logo=python&logoColor=white) **Django** | API REST, logique financière et authentification. |
| **Frontend** | ![Next.js](https://img.shields.io/badge/Next.js-000000?style=flat&logo=nextdotjs&logoColor=white) **React** | Interface utilisateur dynamique et Server-Side Rendering (SSR). |
| **Base de données**| ![PostgreSQL](https://img.shields.io/badge/PostgreSQL-336791?style=flat&logo=postgresql&logoColor=white) | Stockage robuste des historiques de cours et des profils utilisateurs. |
| **Styling** | **Tailwind CSS** | Design moderne et responsive (Mobile First). |

---

## 📊 Analyse des Métriques (Indicateurs Clés)
Le dashboard intègre un moteur d'analyse flexible permettant d'évaluer la santé financière des actifs. Voici quelques **exemples** de métriques calculées et suivies en temps réel :

* **Rentabilité (Earnings) :** Suivi de l'**EPS** (Earnings Per Share) pour mesurer le bénéfice net attribué à chaque action ordinaire.
* **Flux de Trésorerie :** Analyse du **Free Cash Flow (FCF)**, permettant d'évaluer la liquidité réelle disponible après investissements (CAPEX).
* **Valorisation :** Calcul du **P/E Ratio** (Price-to-Earnings) pour comparer le cours de bourse aux bénéfices générés.
* **Rendement Actionnaire :** Monitoring du **Dividend Yield** pour les stratégies basées sur les revenus passifs.
* **Performance Relative :** Comparaison dynamique entre les **Actions**, les **ETF** et leurs indices de référence (S&P 500, CAC 40, etc.).

---

## 🏗 Architecture du Projet
Le projet utilise une séparation stricte entre le client et le serveur :

1.  **Le Backend (Django REST Framework) :** Récupère les données de marché (via APIs financières), les traite et les expose via des endpoints sécurisés.
2.  **Le Frontend (Next.js) :** Consomme l'API, gère l'état global avec React et optimise le rendu pour une expérience fluide.
3.  **La Database (PostgreSQL) :** Gère les relations complexes entre les utilisateurs, leurs transactions et les actifs suivis.