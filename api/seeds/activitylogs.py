import click
import random
from api.extensions import db
from api.models.activitylog import ActivityLog
from api.models.users import User
from api.models.instructionalmaterials import InstructionalMaterial
from flask.cli import with_appcontext
from datetime import datetime, timedelta, UTC
import json


@click.command("seed_activitylogs")
@with_appcontext
def seed_activitylogs():
    """Seed the database with sample activity logs for analytics testing."""
    # Check if activity logs already exist
    existing_count = ActivityLog.query.count()
    if existing_count > 50:
        click.echo(f"⚠️  {existing_count} activity logs already exist. Skipping seeding.")
        return

    # Get existing users and IMs
    users = User.query.all()
    ims = InstructionalMaterial.query.filter_by(is_deleted=False).all()

    if not users:
        click.echo("❌ No users found. Please seed users first.")
        return

    if not ims:
        click.echo("❌ No instructional materials found. Please seed IMs first.")
        return

    click.echo(f"📊 Found {len(users)} users and {len(ims)} instructional materials.")
    click.echo("🔄 Generating activity logs...")

    actions = ['CREATE', 'UPDATE']
    statuses = ['For IMER Evaluation', 'For PIMEC Evaluation', 'For UTLDO Approval', 'For Certification', 'Certified']

    activity_logs = []
    
    # Generate logs spread over the last 90 days
    for day_offset in range(90):
        date = datetime.now(UTC) - timedelta(days=day_offset)
        
        # Generate 2-10 random activities per day
        daily_activities = random.randint(2, 10)
        
        for _ in range(daily_activities):
            user = random.choice(users)
            im = random.choice(ims)
            action = random.choice(actions)
            
            # Randomize time within the day
            hours = random.randint(8, 18)
            minutes = random.randint(0, 59)
            activity_time = date.replace(hour=hours, minute=minutes, second=random.randint(0, 59))
            
            if action == 'CREATE':
                description = f"Created instructional material ID {im.id}"
                old_values = None
                new_values = json.dumps({
                    'id': im.id,
                    'im_type': im.im_type,
                    'status': 'For IMER Evaluation'
                })
            else:  # UPDATE
                old_status = random.choice(statuses[:-1])  # Exclude last status for old
                new_status_idx = statuses.index(old_status) + 1
                new_status = statuses[min(new_status_idx, len(statuses) - 1)]
                
                description = f"Updated instructional material ID {im.id} status from {old_status} to {new_status}"
                old_values = json.dumps({'status': old_status})
                new_values = json.dumps({'status': new_status})
            
            activity_log = ActivityLog(
                user_id=user.id,
                action=action,
                table_name='instructionalmaterials',
                record_id=im.id,
                description=description,
                old_values=old_values,
                new_values=new_values
            )
            activity_log.created_at = activity_time
            activity_logs.append(activity_log)

    # Bulk insert
    db.session.bulk_save_objects(activity_logs)
    db.session.commit()

    click.echo(f"✅ Successfully created {len(activity_logs)} activity logs!")
    click.echo("📈 Activity log distribution:")
    
    # Show distribution by action
    create_count = sum(1 for log in activity_logs if log.action == 'CREATE')
    update_count = sum(1 for log in activity_logs if log.action == 'UPDATE')
    click.echo(f"   - CREATE actions: {create_count}")
    click.echo(f"   - UPDATE actions: {update_count}")


@click.command("clear_activitylogs")
@with_appcontext
def clear_activitylogs():
    """Clear all activity logs from the database."""
    count = ActivityLog.query.count()
    if count == 0:
        click.echo("ℹ️  No activity logs to clear.")
        return
    
    ActivityLog.query.delete()
    db.session.commit()
    click.echo(f"🗑️  Deleted {count} activity logs.")


def register_commands(app):
    app.cli.add_command(seed_activitylogs)
    app.cli.add_command(clear_activitylogs)
