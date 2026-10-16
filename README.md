# 🌐 CISCO STUDENT - Panel Étudiant Universitaire (BUT Réseaux & Télécoms)

Plateforme web centralisée moderne type *Pronote / Linear* conçue pour les étudiants en **BUT Réseaux et Télécommunications** (et adaptable à tous les BUT / IUT).

Elle agrège et synchronise automatiquement l'ensemble de vos outils du quotidien :
- 🎓 **ScoDoc** : Moyenne générale, rang dans la promotion, moyennes par UE & Matières (Ressources R101, R102, R107... et SAÉ), dernières notes avec moyennes/min/max de promo, absences justifiées & non justifiées avec motifs et créneaux. Intégré via le paquet PyPI officiel [`scodoc-api`](https://pypi.org/project/scodoc-api/) (`pip install scodoc-api`, code source sur [GitHub](https://github.com/SkillFXX/scodoc-api)).
- 📚 **Moodle (Université de Montpellier / IUT)** : Récupération des cours inscrits, devoirs maison (DM), TP notés à rendre et échéances via l'API WebService Moodle Mobile.
- 📅 **Emploi du temps ADE Campus / UM Net** : Parsing en direct de votre flux iCal exporté (`.ics`), détection du cours en cours, salle, enseignant et vue calendrier jour / semaine.
- 📝 **Agenda & Échéancier unifié** : Ajout manuel de dates de devoirs surveillés (DS), contrôles, rendus de TP ou to-do list avec compte à rebours ("Dans 2 jours", "Demain", "Aujourd'hui") et archivage.

---

## 🛠️ Stack Technique

- **Backend** : [FastAPI](https://fastapi.tiangolo.com/) (Python 3.12+)
- **Connecteur ScoDoc** : [`scodoc-api`](https://pypi.org/project/scodoc-api/) disponible sur PyPI
- **Base de données** : SQLite avec [SQLAlchemy 2.0](https://www.sqlalchemy.org/)
- **Sécurité** : JWT (JSON Web Tokens), hachage sécurisé des mots de passe avec `bcrypt`
- **Frontend** : [SvelteKit](https://kit.svelte.dev/) (Svelte 5 avec Runes)
- **UI & Design** : [Tailwind CSS v4](https://tailwindcss.com/) + Design System [shadcn](https://shadcn-svelte.com/) + Icônes [Lucide Svelte](https://lucide.dev/)

---

## 🚀 Démarrage Rapide

### 1. Lancer le Backend FastAPI

```bash
cd backend
# Activer l'environnement virtuel
.\.venv\Scripts\Activate.ps1   # (sur Windows PowerShell)
# ou source .venv/bin/activate (sur Linux/macOS)

# Lancer le serveur d'API
uvicorn app.main:app --reload --port 8000
```
L'API démarre sur : **`http://localhost:8000`** (Documentation Swagger interactive sur `http://localhost:8000/docs`).

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
   - URL : Ex. `https://moodle.umontpellier.fr`
   - Identifiant & Mot de passe ou Jeton de sécurité WebService
3. **ADE Campus (iCal)** :
   - Copiez le lien de flux iCal exporté depuis votre espace ADE Campus / UM Net.
