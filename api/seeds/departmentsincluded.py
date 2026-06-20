import click
from api.extensions import db
from api.models.departmentsincluded import DepartmentIncluded
from api.models.departments import Department
from api.models.users import User
from flask.cli import with_appcontext
from datetime import datetime, UTC

@click.command("seed_departmentsincluded")
@with_appcontext
def seed_departmentsincluded():
    """Seed the database with department-user associations."""
    if DepartmentIncluded.query.first():
        click.echo("⚠️  DepartmentIncluded records already exist in database. Skipping seeding.")
        return
    
    users = User.query.all()
    departments = Department.query.all()
    
    if not users or not departments:
        click.echo("❌ Required seed data missing. Please seed users and departments first.")
        return

    department_included = []
    for user in users:
        if user.role in ["Technical Admin", "UTLDO Admin"]:
            # Admins: all departments
            for department in departments:
                department_included.append({
                    "department_id": department.id,
                    "user_id": user.id
                })
        else:
            # Faculty/PIMEC: only 2 departments, rotating
            for i in range(2):
                department = departments[(user.id + i) % len(departments)]
                department_included.append({
                    "department_id": department.id,
                    "user_id": user.id
                })

    try:
        for di_data in department_included:
            if not DepartmentIncluded.query.filter_by(
                department_id=di_data["department_id"],
                user_id=di_data["user_id"]
            ).first():
                association = DepartmentIncluded(
                    department_id=di_data["department_id"],
                    user_id=di_data["user_id"]
                )
                db.session.add(association)
        
        db.session.commit()
        click.echo(f"✅ Successfully seeded {len(department_included)} DepartmentIncluded records!")
    except Exception as e:
        db.session.rollback()
        click.echo(f"❌ Error seeding DepartmentIncluded records: {str(e)}")

def register_commands(app):
    app.cli.add_command(seed_departmentsincluded)