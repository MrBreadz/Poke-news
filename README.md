# ⚡ Pokémon TCG Daily

> Dashboard bento + newsletter quotidienne sur l'actualité Pokémon TCG — **100 % gratuit, automatique**.

---

## Ce que c'est

Chaque matin, un pipeline Python récupère automatiquement les news Pokémon TCG (RSS, Reddit, YouTube, cartes/prix…), les résume en français, et génère :
- un **site web bento** glassmorphism (fond sombre, cartes visuelles)
- une **newsletter HTML** envoyée par e-mail

Tout est gratuit. Rien à payer, jamais.

---

## Démarrage rapide (5 étapes)

### Étape 1 — Avoir Python installé

Tu as besoin de Python 3.10 ou plus récent. Pour vérifier, ouvre un terminal et tape :
```
python --version
```
Si Python n'est pas installé, télécharge-le sur [python.org](https://python.org) (bouton "Download Python").

---

### Étape 2 — Télécharger / cloner le projet

Si tu as Git :
```bash
git clone https://github.com/TON_COMPTE/poke-news.git
cd poke-news
```

Sinon, télécharge le ZIP depuis GitHub et décompresse-le.

---

### Étape 3 — Installer les dépendances Python

Dans le dossier du projet, ouvre un terminal et tape :
```bash
pip install -r requirements.txt
```
(Ça installe toutes les bibliothèques automatiquement — ça prend 1-2 minutes)

---

### Étape 4 — Configurer tes clés (optionnel mais recommandé)

Copie le fichier `.env.example` en `.env` :
```bash
cp .env.example .env
```

Puis ouvre `.env` dans un éditeur (Notepad ou VS Code) et remplis les clés que tu veux :

| Variable | Obligatoire ? | Où l'obtenir |
|---|---|---|
| `GEMINI_API_KEY` | Non (résumés plus beaux avec) | [aistudio.google.com](https://aistudio.google.com/app/apikey) → gratuit, sans CB |
| `POKEMONTCG_API_KEY` | Non (améliore les prix USD) | [dev.pokemontcg.io](https://dev.pokemontcg.io/) → gratuit |
| `GMAIL_USER` + `GMAIL_APP_PASSWORD` | Seulement pour l'email | [Voir § Email](#email) |
| `NEWSLETTER_RECIPIENTS` | Seulement pour l'email | Ton adresse e-mail |

**Sans aucune clé**, le pipeline tourne quand même en mode dégradé (titres bruts au lieu de résumés traduits).

---

### Étape 5 — Lancer le pipeline

```bash
# Voir le rendu immédiatement (depuis les données de démo, 0 réseau)
python run.py --demo

# Run complet (fetch toutes les sources + génère le site)
python run.py --no-email

# Run complet + envoi email
python run.py
```

Ensuite, ouvre le fichier `docs/index.html` dans ton navigateur — tu verras le bento !

---

## Personnaliser les sources

Tu n'as qu'un seul fichier à éditer : **`config/sources.yaml`**

Tu peux y :
- **Ajouter un fil RSS** : copie-colle une ligne sous `rss:` avec le nom, l'URL et la langue
- **Activer/désactiver un subreddit** : commente ou décommente la ligne avec `#`
- **Ajouter une chaîne YouTube** : renseigne le `channel_id` (visible dans l'URL de la chaîne)
- **Coller des URLs de tweets JP** : ajoute l'URL sous `x_manual_seed:`
- **Changer les cartes surveillées** : modifie `watchlist_cards:`

Pas besoin de toucher au code.

---

## Déploiement sur GitHub Pages (site public gratuit)

1. Crée un repo GitHub (public ou privé)
2. Pousse le code : `git push`
3. Va dans **Settings → Pages** → Source : `main` branch, dossier `/docs`
4. Ton site est en ligne sur `https://TON_COMPTE.github.io/poke-news/`

---

## Automatisation quotidienne (GitHub Actions)

Le fichier `.github/workflows/daily.yml` configure le pipeline automatique :
- Lance tous les jours à 06h15 heure de Paris
- Peut être déclenché manuellement depuis **GitHub → Actions → "Run workflow"**

### Ajouter les secrets dans GitHub

Pour que le pipeline ait accès à tes clés API :
1. Sur GitHub, va dans ton repo → **Settings → Secrets and variables → Actions**
2. Clique **"New repository secret"**
3. Ajoute chaque variable de ton `.env` (même noms : `GEMINI_API_KEY`, `GMAIL_USER`, etc.)

---

## Email newsletter {#email}

### Option A — Gmail (le plus simple)

1. Connecte-toi à ton compte Gmail
2. Va sur [myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords)
3. Crée un "Mot de passe d'application" pour "Autre (PokeNews)"
4. Copie le mot de passe généré dans `.env` :
   ```
   GMAIL_USER=ton.adresse@gmail.com
   GMAIL_APP_PASSWORD=xxxx-xxxx-xxxx-xxxx
   NEWSLETTER_RECIPIENTS=ton.adresse@gmail.com
   ```

### Option B — Brevo (pour une vraie liste d'abonnés)

1. Crée un compte gratuit sur [brevo.com](https://www.brevo.com) (300 emails/jour gratuits)
2. Va dans **Paramètres → Clés API** et copie ta clé
3. Renseigne `BREVO_API_KEY` dans ton `.env`

---

## Tableau des quotas gratuits

| Service | Quota gratuit | Limite atteinte ? |
|---|---|---|
| **GitHub Actions** | 2 000 min/mois (repo privé), illimité (public) | Non — le pipeline prend ~2 min/jour |
| **GitHub Pages** | Illimité (sites statiques publics) | Non |
| **Gemini Flash Lite** | ~1 500 req/jour, 1M tokens/min | Non — ~20 req/run |
| **TCGdex API** | Sans quota, sans clé | — |
| **pokemontcg.io** | 1 000 req/jour sans clé, illimité avec clé gratuite | Non |
| **Reddit JSON** | Lecture publique sans clé | Non |
| **YouTube RSS** | Illimité, sans clé | — |
| **Brevo email** | 300 emails/jour | Non (usage perso) |
| **Gmail SMTP** | ~500 emails/jour | Non (usage perso) |

**Total facture mensuelle : 0 €**

---

## Architecture du pipeline

```
[1] INGEST    → RSS, Reddit, YouTube, TCGdex, tweets manuels
[2] NORMALIZE → schéma unifié
[3] DEDUPE    → fusion des doublons (similarité titre)
[5] CLASSIFY  → 7 catégories (nouveaux_sets, nouvelles_cartes, leaks…)
[8] RANK/CUT  → top N par score pertinence + fraîcheur
[6] SUMMARIZE → résumé FR via Gemini ou mode dégradé
[7] VISUAL    → fallback image par catégorie si absent
[9] PERSIST   → /data/YYYY-MM-DD.json (historique versionné Git)
[10] BUILD    → /docs/*.html (site statique, Jinja2)
[11] EMAIL    → /newsletters/YYYY-MM-DD.html + envoi
[12] DEPLOY   → commit + push → GitHub Pages redéploie
```

---

## Structure du projet

```
poke-news/
├── config/sources.yaml        ← TON fichier de config (seul fichier à éditer)
├── pipeline/                  ← Code Python du pipeline
│   ├── adapters/              ← Sources (RSS, Reddit, YouTube…)
│   ├── classify.py            ← Catégorisation 7 catégories
│   ├── summarize.py           ← Résumés FR (Gemini ou dégradé)
│   └── build.py               ← Génération HTML
├── site/
│   ├── templates/             ← Templates Jinja2 (HTML bento, newsletter)
│   └── assets/                ← CSS glassmorphism + JS filtres
├── data/                      ← Éditions JSON (historique)
├── docs/                      ← Site statique généré (GitHub Pages)
├── newsletters/               ← Archives HTML newsletter
├── .github/workflows/         ← GitHub Actions (cron quotidien)
├── run.py                     ← Point d'entrée
└── .env.example               ← Template de configuration
```
