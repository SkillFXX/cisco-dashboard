from app.database import SessionLocal, Base, engine
from app.models import User, UserCredentials, PersonalTask
from app.auth import get_password_hash
import datetime

def seed():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    # Check if demo user exists
    user = db.query(User).filter(User.username == "etudiant").first()
    if not user:
        user = User(
            username="etudiant",
            email="alexandre.dupont@etu.umontpellier.fr",
            hashed_password=get_password_hash("cisco123"),
            full_name="Alexandre Dupont (BUT R&T)"
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        creds = UserCredentials(
            user_id=user.id,
            scodoc_url="https://wscodoc.iutbeziers.fr",
            scodoc_username="alexandre.dupont",
            scodoc_password="", # simulated
            moodle_url="https://moodle.umontpellier.fr",
            moodle_username="adupont",
            moodle_password="",
            ical_url="https://edt.umontpellier.fr/ade/custom/modules/Views/fetch.jsp?data=...",
            use_mock_fallback=True
        )
        db.add(creds)

        # Add sample student tasks & DS
        today = datetime.datetime.now()
        tasks = [
            PersonalTask(
                user_id=user.id,
                title="DS 2 : Architecture Réseaux & Routage RIP/OSPF",
                description="Réviser les tables de routage, les métriques et les masques /24, /28, /30.",
                subject="R101 - Réseaux",
                due_date=today + datetime.timedelta(days=3, hours=10),
                event_type="ds",
                status="todo"
            ),
            PersonalTask(
                user_id=user.id,
                title="Préparation TP Linux : Permissions chmod et chown avancées",
                description="Tester les SGID, SUID et Sticky bit sur machine virtuelle.",
                subject="R107 - Linux",
                due_date=today + datetime.timedelta(days=4, hours=14),
                event_type="tp",
                status="todo"
            ),
            PersonalTask(
                user_id=user.id,
                title="Fiches de révision : Modulation d'amplitude et de fréquence",
                description="Apprendre les formules de Shannon et de Nyquist.",
                subject="R102 - Télécoms",
                due_date=today + datetime.timedelta(days=6, hours=18),
                event_type="todo",
                status="todo"
            ),
            PersonalTask(
                user_id=user.id,
                title="Rendu Maquette Packet Tracer SAÉ 1.1",
                description="Vérifier le ping entre le VLAN Comptabilité et le serveur Web.",
                subject="SAÉ 1.1 - Réseau PME",
                due_date=today + datetime.timedelta(days=10, hours=23, minutes=59),
                event_type="dm",
                status="todo"
            )
        ]
        db.add_all(tasks)
        db.commit()
        print("Demo user created: username='etudiant', password='cisco123'")
    else:
        print("Demo user already exists.")
    db.close()

if __name__ == "__main__":
    seed()

