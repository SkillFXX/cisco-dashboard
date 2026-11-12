# Cisco Dashboard

Panel étudiant auto-hébergeable pour les étudiants en **BUT**, quel que soit leur IUT ou leur spécialité : notes, absences, emploi du temps, devoirs, notifications et assistant IA, dans une seule interface.

> Projet non officiel, sans lien avec les universités ni avec les éditeurs de ScoDoc, Moodle ou des logiciels d'emploi du temps. Il stocke (chiffrés) des identifiants d'ENT : n'hébergez que pour des personnes qui vous font confiance, et à vos risques.

## Fonctionnalités

- **Notes (ScoDoc)** : moyenne générale, rang, moyennes par UE et par ressource/SAÉ, détail de chaque évaluation avec répartition de la promo, courbe d'évolution de la moyenne et du rang.
- **Absences** : justifiées / injustifiées, créneaux et motifs.
- **Emploi du temps (lien iCal `.ics` fourni par votre université)** : vues jour, semaine et mois, cours en cours, salle, enseignant, groupe, navigation sur toute l'année universitaire.
- **Devoirs** : DS, DM, TP, to-do, avec échéances, archivage et ajout direct depuis un cours.
- **Moodle** : cours inscrits et devoirs à rendre.
- **Ressources** : les cours Moodle et leurs documents directement dans l'application (sections, dossiers, liens), avec recherche, aperçu des PDF et images, et téléchargement sans passer par le site.
- **Notifications** : nouvelle note, rappel avant un devoir, récapitulatif quotidien, emploi du temps de la semaine suivante en image ; par email ou webhook Discord.
- **Assistant IA (Gemini)** : chaque utilisateur renseigne sa propre clé d'API dans les Paramètres, puis pose ses questions (cours, devoirs, notes, absences, liste des documents Moodle d'un cours) et peut lui demander d'ajouter un devoir. Le contexte envoyé est réduit aux rubriques utiles à la question, avec limites de débit pour rester dans le quota gratuit.
- **Thème** clair, sombre ou automatique, interface responsive et installable (PWA).
- **Administration** : serveur SMTP, gestion des utilisateurs, mot de passe oublié.
- **Préchargement en arrière-plan** : les données de chaque utilisateur sont rafraîchies toutes les 5 minutes pour un affichage instantané.

## Stack

- **Backend** : FastAPI (Python 3.12), SQLAlchemy 2 + SQLite, JWT, bcrypt, connecteur [`scodoc-api`](https://pypi.org/project/scodoc-api/)
- **Frontend** : SvelteKit (Svelte 5), Tailwind CSS v4, Lucide

## Déploiement (Docker Compose)

```bash
cp .env.example .env
# éditez .env : au minimum SECRET_KEY (openssl rand -hex 32)
docker compose up -d --build
```

L'application est servie sur `http://localhost:18420` (port modifiable avec `APP_PORT`). Les données sont conservées dans le volume `cisco-data`. Placez un reverse proxy HTTPS devant pour une utilisation publique.

### Variables d'environnement

| Variable | Rôle |
|---|---|
| `SECRET_KEY` | **Obligatoire** avec Docker Compose. Signe les sessions et dérive la clé de chiffrement des identifiants. Ne la changez pas après coup : les identifiants stockés deviendraient illisibles. |
| `ENCRYPTION_KEY` | Clé de chiffrement dédiée (par défaut dérivée de `SECRET_KEY`) |
| `ADMIN_EMAIL` | Email du compte administrateur (onglet **Administration**) |
| `ADMIN_PASSWORD` | Mot de passe de l'admin, appliqué à chaque démarrage |
| `PUBLIC_URL` | URL publique du site, utilisée dans les emails « mot de passe oublié » |
| `APP_PORT` | Port exposé sur l'hôte (défaut `18420`) |
| `DATABASE_URL` | URL SQLAlchemy de la base (défaut : SQLite) |
| `ENABLE_DOCS` | `true` pour exposer Swagger (`/docs`) |

## Développement local

Backend :

```bash
cd backend
python -m venv .venv && source .venv/bin/activate   # Windows : .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Frontend, dans un second terminal :

```bash
cd frontend
npm install
npm run dev
```

Frontend sur `http://localhost:5173`, API sur `http://localhost:8000`. Sous Windows, `start.bat` lance les deux.

## Configuration des services

À la création du compte ou dans **Paramètres** :

1. **ScoDoc** : URL de votre instance (l'adresse de ScoDoc de votre IUT), identifiant et mot de passe CAS / ENT.
2. **Moodle** : URL de la plateforme de votre IUT, identifiant et mot de passe, ou jeton WebService.
3. **Emploi du temps** : lien du flux iCal d'abonnement / d'export « iCal » du site où vous consultez votre emploi du temps.
4. **Assistant IA** (optionnel) : clé d'API Gemini gratuite, depuis [Google AI Studio](https://aistudio.google.com/apikey).

## Licence

Distribué sous licence [GNU AGPL v3](LICENSE). Si vous hébergez une version modifiée pour d'autres utilisateurs, vous devez leur fournir le code source de vos modifications.

Les polices DejaVu incluses dans `backend/app/assets/fonts/` conservent leur propre licence (voir `LICENSE.txt` dans ce dossier).
