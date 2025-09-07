import click
from api.extensions import db
from api.models.instructionalmaterials import InstructionalMaterial
from flask.cli import with_appcontext
from datetime import datetime, UTC

@click.command("seed_instructionalmaterials")
@with_appcontext
def seed_instructionalmaterials():
	"""Seed the database with initial instructional materials."""
	if InstructionalMaterial.query.first():
		click.echo("⚠️  Instructional Materials already exist in database. Skipping seeding.")
		return

	current_time = datetime.now(UTC)
	admin_user = "system"

	ims = [
		{
			"im_type": "university",  # or "service" if appropriate
			"status": "For Resubmission",
			"validity": "2026",
			"version": "v1.0",
			"s3_link": "instructional_materials/a542efa1-f009-4a82-8277-02ec74db0439/INTE 30033 Systems Integration and Architecture 1.pdf",
			"created_by": admin_user,
			"updated_by": admin_user,
			"notes": "Missing sections: The VMGOP, Preface",
			"university_im_id": 16,
			"service_im_id": 16,
		}
	]

	try:
		for im_data in ims:
			im = InstructionalMaterial(**im_data)
			db.session.add(im)
		db.session.commit()
		click.echo("✅ Successfully seeded instructional materials!")
	except Exception as e:
		db.session.rollback()
		click.echo(f"❌ Error seeding instructional materials: {str(e)}")

def register_commands(app):
	app.cli.add_command(seed_instructionalmaterials)
