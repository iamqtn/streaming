# 🌐 Site Status Checker (Streaming)

Une mini-webapp en **Python + Flask**, conçue pour surveiller l'état de plusieurs sites web.  
Elle propose un design **mode sombre total**, une fonction **copie dans le presse-papier** (iOS/Safari compatible), et un **auto-refresh intelligent**.

---

##  Aperçu

| Fonctionnalité             | Description |
|----------------------------|-------------|
| Vérifie l'état de sites    | `OK` (2xx, 3xx), `KO` (4xx, 5xx), ou `DOWN` (erreur réseau) |
| Design moderne             | Thème sombre poussé avec Bulma & style « glass » |
| Copie rapide               | Un clic sur le nom du site le copie dans le presse-papier |
| Compatibilité mobile       | Adapté iOS & Safari |
| Auto-refresh optimisé      | Ne se rafraîchit que si l'onglet est actif |
| Vérification en parallèle  | Utilise `ThreadPoolExecutor` pour la rapidité |

---

##  Installation & usage

1. Clone ce dépôt :
```bash
git clone https://github.com/iamqtn/streaming.git
cd streaming
```

2. Crée un environnement virtuel (optionnel mais recommandé) :
```bash
python -m venv venv
source venv/bin/activate  # (Linux / macOS)
venv\Scripts\activate     # (Windows)
```

3. Installe les dépendances :
```bash
pip install -r requirements.txt
```

4. Lance l’application :
```bash
python app.py
```

Puis ouvre **http://localhost:8000** dans ton navigateur.

---

##  Déploiement sur Render (gratuit)

1. Crée un compte sur [Render.com](https://render.com)
2. Crée un nouveau service **Web Service**, connecte-le à ce dépôt.
3. Configurations requises :
   - **Build Command** : `pip install -r requirements.txt`
   - **Start Command** : `gunicorn app:app`
   - **Plan** : `Free`

4. Déploie ton application. URL disponible en 2 min.

**Astuce** : Utilise [UptimeRobot](https://uptimerobot.com) pour "pinguer" ton app toutes les 5 min et éviter les délais de mise en route.

---

##  Configuration

Modifie la liste de domaines directement dans `app.py` :

```python
DOMAINS = [
    "example.com",
    "mon-site.fr",
    "autre-site.net",
]
```

---

##  Fichiers importants

- `app.py` : code principal de l’application Flask
- `requirements.txt` : dépendances à installer (`Flask`, `requests`, `gunicorn`)
- `.render.yaml` : configuration optionnelle pour déploiement Render

---

##  À venir (idées)

- Ajouter un champ **formulaire dynamique** pour saisir de nouveaux domaines
- Enregistrer les domaines ajoutés avec un stockage simple (`.json` ou `sqlite`)
- Ajouter une **favicon** personnalisée
- Permettre des **alertes ou notifications** en cas de domaine `DOWN`

---

##  Auteur

Développé par **[iamqtn](https://github.com/iamqtn)**

---

##  Licence

Ce projet est sous licence **MIT** — libre à toi d’adapter et d’utiliser ce code.
