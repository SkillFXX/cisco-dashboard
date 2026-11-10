# Cisco Dashboard - Panel Étudiant Universitaire (BUT Réseaux & Télécoms)

Plateforme web centralisée moderne type *Pronote / Linear* conçue pour les étudiants en **BUT Réseaux et Télécommunications** (et adaptable à tous les BUT / IUT).

Elle agrège et synchronise automatiquement l'ensemble de vos outils du quotidien :
- **ScoDoc** : Moyenne générale, rang dans la promotion, moyennes par UE & Matières (Ressources R101, R102, R107... et SAÉ), dernières notes avec moyennes/min/max de promo, absences justifiées & non justifiées avec motifs et créneaux. Intégré via le paquet PyPI officiel [`scodoc-api`](https://pypi.org/project/scodoc-api/) (`pip install scodoc-api`, code source sur [GitHub](https://github.com/SkillFXX/scodoc-api)).
- **Moodle (Université de Montpellier / IUT)** : Récupération des cours inscrits, devoirs maison (DM), TP notés à rendre et échéances via l'API WebService Moodle Mobile.
- **Emploi du temps ADE Campus / UM Net** : Parsing en direct de votre flux iCal exporté (`.ics`), détection du cours en cours, salle, enseignant et vue calendrier jour / semaine.
- **Agenda & Échéancier unifié** : Ajout manuel de dates de devoirs surveillés (DS), contrôles, rendus de TP ou to-do list avec compte à rebours ("Dans 2 jours", "Demain", "Aujourd'hui") et archivage.

---

## Stack Technique

- **Backend** : [FastAPI](https://fastapi.tiangolo.com/) (Python 3.12+)
- **Connecteur ScoDoc** : [`scodoc-api`](https://pypi.org/project/scodoc-api/) disponible sur PyPI
- **Base de données** : SQLite avec [SQLAlchemy 2.0](https://www.sqlalchemy.org/)
- **Sécurité** : JWT (JSON Web Tokens), hachage sécurisé des mots de passe avec `bcrypt`
- **Frontend** : [SvelteKit](https://kit.svelte.dev/) (Svelte 5 avec Runes)
- **UI & Design** : [Tailwind CSS v4](https://tailwindcss.com/) + Design System [shadcn](https://shadcn-svelte.com/) + Icônes [Lucide Svelte](https://lucide.dev/)

---

## Démarrage Rapide

### 1. Lancer le Backend FastAPI

```bash
cd backend
# Activer l'environnement virtuel
.\.venv\Scripts\Activate.ps1   # (sur Windows PowerShell)
# ou source .venv/bin/activate (sur Linux/macOS)

# Lancer le serveur d'API
uvicorn app.main:app --reload --port 8000
```
L'API démarre sur : **`http://localhost:8000`** (Swagger sur `/docs` si `ENABLE_DOCS=true`).

### 2. Lancer le Frontend SvelteKit

Dans un second terminal :
```bash
cd frontend
npm run dev
```
L'application démarre sur : **`http://localhost:5173`**.

---

## ⚙️ Configuration des Services Tiers

Lors de la création de votre compte (ou dans l'onglet **Services & Paramètres**) :
1. **ScoDoc** :
   - URL : Ex. `https://wscodoc.iutbeziers.fr` (ou votre instance d'IUT)
   - Identifiant & Mot de passe CAS / ENT
2. **Moodle** :
   - URL : Ex. `https://moodle-but.iutbeziers.fr/moodle`
   - Identifiant & Mot de passe ou Jeton de sécurité WebService
3. **ADE Campus (iCal)** :
   - Copiez le lien de flux iCal exporté depuis votre espace ADE Campus / UM Net.

---

## 🛠️ Administration, notifications & PWA

### Variables d'environnement (backend)

| Variable | Rôle |
|---|---|
| `SECRET_KEY` | Clé de signature des sessions (générée et conservée à côté de la base si absente) |
| `ADMIN_EMAIL` | Email du compte administrateur (onglet **Administration**) |
| `ADMIN_PASSWORD` | Mot de passe de l'admin, appliqué à chaque démarrage |
| `PUBLIC_URL` | URL publique du site, utilisée dans les emails « mot de passe oublié » (sinon saisie dans l'onglet Administration) |
| `ENABLE_DOCS` | `true` pour exposer Swagger (`/docs`) |

### Fonctionnalités
- **Administration** : configuration du serveur SMTP, liste des utilisateurs, modification, changement de mot de passe et suppression de comptes.
- **Mot de passe oublié** : disponible dès qu'un SMTP et une URL publique sont configurés ; les utilisateurs peuvent aussi changer leur mot de passe dans *Paramètres*.
- **Notifications** : alertes personnalisées (nouvelle note, rappel X heures avant un devoir fait ou non, récapitulatif quotidien) par email ou webhook Discord.
- **Courbe d'évolution** de la moyenne et du rang (un point par jour), alimentée automatiquement.
- **Préchargement en arrière-plan** : toutes les 5 minutes, les données ScoDoc, Moodle et emploi du temps de chaque utilisateur sont renouvelées avant l'expiration du cache (15 min), pour un affichage instantané à l'ouverture.
- **Thème** clair, sombre ou automatique (réglable depuis l'en-tête et les Paramètres).
- **PWA** : l'application est installable sur mobile et responsive.
