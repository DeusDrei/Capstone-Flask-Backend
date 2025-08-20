import click
from api.extensions import db
from api.models.subjects import Subject
from flask.cli import with_appcontext
from datetime import datetime, UTC

@click.command("seed_subjects")
@with_appcontext
def seed_subjects():
    """Seed the database with initial subjects."""
    if Subject.query.first():
        click.echo("⚠️  Subjects already exist in database. Skipping seeding.")
        return
    
    current_time = datetime.now(UTC)
    admin_user = "system"
    
    subjects = [
        # CAF
        {"code": "ACC101", "name": "Fundamentals of Accounting", "created_by": admin_user, "updated_by": admin_user},
        {"code": "ACC201", "name": "Intermediate Accounting", "created_by": admin_user, "updated_by": admin_user},
        {"code": "FIN101", "name": "Financial Management", "created_by": admin_user, "updated_by": admin_user},
        # CADBE
        {"code": "ARCH101", "name": "Architectural Design", "created_by": admin_user, "updated_by": admin_user},
        {"code": "ID101", "name": "Interior Design Principles", "created_by": admin_user, "updated_by": admin_user},
        {"code": "ENVP101", "name": "Environmental Planning", "created_by": admin_user, "updated_by": admin_user},
        # CAL
        {"code": "ENG201", "name": "English Language Studies", "created_by": admin_user, "updated_by": admin_user},
        {"code": "FIL101", "name": "Filipinology", "created_by": admin_user, "updated_by": admin_user},
        {"code": "LIT201", "name": "Literary and Cultural Studies", "created_by": admin_user, "updated_by": admin_user},
        # CBA
        {"code": "HRM101", "name": "Human Resource Management", "created_by": admin_user, "updated_by": admin_user},
        {"code": "MKT101", "name": "Marketing Management", "created_by": admin_user, "updated_by": admin_user},
        {"code": "ENT101", "name": "Entrepreneurship", "created_by": admin_user, "updated_by": admin_user},
        # COC
        {"code": "ADV101", "name": "Advertising Principles", "created_by": admin_user, "updated_by": admin_user},
        {"code": "BROAD101", "name": "Broadcasting", "created_by": admin_user, "updated_by": admin_user},
        {"code": "JOUR101", "name": "Journalism", "created_by": admin_user, "updated_by": admin_user},
        # CCIS
        {"code": "CS101", "name": "Computer Science Fundamentals", "created_by": admin_user, "updated_by": admin_user},
        {"code": "IT101", "name": "Information Technology Basics", "created_by": admin_user, "updated_by": admin_user},
        # COED
        {"code": "EDM101", "name": "Education Management", "created_by": admin_user, "updated_by": admin_user},
        {"code": "LIB101", "name": "Library Science", "created_by": admin_user, "updated_by": admin_user},
        # CE
        {"code": "CIV101", "name": "Civil Engineering Principles", "created_by": admin_user, "updated_by": admin_user},
        {"code": "MECH101", "name": "Mechanical Engineering", "created_by": admin_user, "updated_by": admin_user},
        # CHK
        {"code": "PE101", "name": "Physical Education", "created_by": admin_user, "updated_by": admin_user},
        # CL
        {"code": "LAW101", "name": "Introduction to Law", "created_by": admin_user, "updated_by": admin_user},
        # CPSPA
        {"code": "PA101", "name": "Public Administration", "created_by": admin_user, "updated_by": admin_user},
        # CSSD
        {"code": "SOC101", "name": "Sociology", "created_by": admin_user, "updated_by": admin_user},
        # CS
        {"code": "BIO101", "name": "General Biology", "created_by": admin_user, "updated_by": admin_user},
        {"code": "CHEM101", "name": "General Chemistry", "created_by": admin_user, "updated_by": admin_user},
        {"code": "MATH101", "name": "Mathematics", "created_by": admin_user, "updated_by": admin_user},
        # CTHTM
        {"code": "HM101", "name": "Hospitality Management", "created_by": admin_user, "updated_by": admin_user},
        {"code": "TM101", "name": "Tourism Management", "created_by": admin_user, "updated_by": admin_user},
        {"code": "TRM101", "name": "Transportation Management", "created_by": admin_user, "updated_by": admin_user}
    ]

    try:
        for subject_data in subjects:
            subject = Subject(
                code=subject_data["code"],
                name=subject_data["name"],
                created_by=subject_data["created_by"],
                updated_by=subject_data["updated_by"]
            )
            db.session.add(subject)
        
        db.session.commit()
        click.echo("✅ Successfully seeded subjects!")
    except Exception as e:
        db.session.rollback()
        click.echo(f"❌ Error seeding subjects: {str(e)}")

def register_commands(app):
    app.cli.add_command(seed_subjects)