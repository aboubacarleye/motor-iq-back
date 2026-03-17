## MotorIQ Backend (FastAPI + Streamlit)

Backend de démonstration pour l’application MotorIQ.  
Il expose une API REST FastAPI et un petit dashboard Streamlit utilisant la même couche de données in‑memory.

### 1. Prérequis

- Python 3.10+
- `pip` ou `pipx`

### 2. Installation

Depuis la racine du projet (`motor-iq-back`) :

```bash
python -m venv .venv
.\.venv\Scripts\activate  # Windows PowerShell
# source .venv/bin/activate  # macOS / Linux

pip install --upgrade pip
pip install -r requirements.txt
```

### 3. Lancer l’API FastAPI (local)

Toujours depuis la racine du projet :

```bash
uvicorn app.main:app --reload
```

L’API sera disponible sur `http://127.0.0.1:8000` avec la documentation interactive sur `http://127.0.0.1:8000/docs`.

Endpoints principaux implémentés :

- `POST /auth/register`
- `POST /auth/login` (token factice, pas d’auth réelle)
- `GET /drivers/{driver_id}`
- `PUT /drivers/{driver_id}`
- `GET /drivers/{driver_id}/vehicles`
- `POST /drivers/{driver_id}/vehicles`
- `POST /claims`
- `GET /claims/driver/{driver_id}`
- `GET /claims/{claim_id}`
- `PATCH /claims/{claim_id}`

Les données sont stockées en mémoire (`app/repositories/memory_db.py`) avec un driver par défaut :

- `id = 1`
- `name = "Amira Mensah"`
- 2 véhicules et quelques sinistres de démo.

### 4. Lancer le dashboard Streamlit (local)

Dans le même environnement virtuel :

```bash
streamlit run app/streamlit_app.py
```

Le dashboard permet de :

- Visualiser la liste des drivers (dans la démo : Amira).
- Voir les véhicules du driver sélectionné.
- Lister les sinistres, filtrer par statut.
- Consulter le détail d’un sinistre (timeline, description, dates).
- Mettre à jour le statut d’un sinistre.
- Recalculer un `fraud_risk_score` simple (aléatoire).

### 5. Déploiement sur Streamlit Cloud

Pour déployer sur Streamlit Cloud (ou équivalent) :

- Pousser ce repo sur GitHub.
- Créer une nouvelle app Streamlit en pointant sur le fichier `app/streamlit_app.py`.

Important: le dossier `app/` est un package Python (présence de `app/__init__.py`). Si vous copiez des fichiers à la main, gardez bien ces `__init__.py`.

Le script Streamlit:

- démarre automatiquement l’API FastAPI (`app.main:app`) via `uvicorn` dans un thread séparé (port `8000`),
- et intègre la doc Swagger de l’API dans une iframe.

Une fois l’app Streamlit déployée, vous verrez:

- en haut de page: un encadré expliquant que l’API tourne sur `http://localhost:8000` à l’intérieur du même conteneur,
- juste en dessous: **Swagger UI** embarqué, ce qui permet de tester tous les endpoints directement “depuis Streamlit”.

Vous pouvez donc:

- manipuler les données via Swagger (`/auth/register`, `/drivers/{id}`, `/claims`, etc.),
- et voir les mêmes données reflétées dans le dashboard en dessous (drivers, vehicles, claims).

### 6. Notes sur l’authentification

Pour ce MVP, l’authentification n’est **pas réellement gérée**.  
Les endpoints `/auth/register` et `/auth/login` existent pour compatibilité avec le front, mais le backend fonctionne avec un driver par défaut et ne vérifie pas les tokens.

