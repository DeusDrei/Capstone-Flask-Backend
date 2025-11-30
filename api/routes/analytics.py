from flask import request, jsonify, Response
from flask_smorest import Blueprint
from api.middleware import jwt_required, roles_required
from api.services.analytics_service import AnalyticsService
from sqlalchemy import func, desc, and_, extract
from api.extensions import db
from api.models.activitylog import ActivityLog
from api.models.instructionalmaterials import InstructionalMaterial
from api.models.im_submissions import IMSubmission
from api.models.users import User
from api.models.colleges import College
from api.models.departments import Department
from api.models.universityims import UniversityIM
from api.models.serviceims import ServiceIM
from datetime import datetime, timedelta, date

analytics_blueprint = Blueprint('analytics', __name__, url_prefix="/analytics")


def get_filtered_im_query(college_id=None, department_id=None):
    """Helper to build filtered IM subquery based on college/department"""
    filters = [InstructionalMaterial.is_deleted == False]
    
    if college_id or department_id:
        # Build subquery for matching IM ids
        university_subq = db.session.query(InstructionalMaterial.id).join(
            UniversityIM, InstructionalMaterial.university_im_id == UniversityIM.id
        )
        service_subq = db.session.query(InstructionalMaterial.id).join(
            ServiceIM, InstructionalMaterial.service_im_id == ServiceIM.id
        )
        
        if department_id:
            university_subq = university_subq.filter(UniversityIM.department_id == department_id)
            # Service IMs don't have department_id, so we filter by college instead
            service_subq = service_subq.join(
                Department, Department.id == department_id
            ).filter(ServiceIM.college_id == Department.college_id)
        elif college_id:
            university_subq = university_subq.filter(UniversityIM.college_id == college_id)
            service_subq = service_subq.filter(ServiceIM.college_id == college_id)
        
        matching_ids = university_subq.union(service_subq).subquery()
        filters.append(InstructionalMaterial.id.in_(db.session.query(matching_ids.c.id)))
    
    return filters


@analytics_blueprint.route('/overview', methods=['GET'])
@jwt_required
@roles_required('Technical Admin', 'UTLDO Admin', 'PIMEC')
def get_overview():
    """Get overall analytics overview with optional college/department filters"""
    try:
        college_id = request.args.get('college_id', type=int)
        department_id = request.args.get('department_id', type=int)
        
        im_filters = get_filtered_im_query(college_id, department_id)
        
        # Total IMs by status
        im_status_counts = db.session.query(
            InstructionalMaterial.status,
            func.count(InstructionalMaterial.id)
        ).filter(*im_filters).group_by(InstructionalMaterial.status).all()

        # Total activities in last 30 days (filtered by college/department if provided)
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        activity_query = ActivityLog.query.filter(
            ActivityLog.created_at >= thirty_days_ago,
            ActivityLog.table_name == 'instructionalmaterials'
        )
        
        if college_id or department_id:
            # Get matching IM ids for activity filtering
            matching_im_ids = db.session.query(InstructionalMaterial.id).filter(*im_filters).subquery()
            activity_query = activity_query.filter(
                ActivityLog.record_id.in_(db.session.query(matching_im_ids.c.id))
            )
        
        recent_activity_count = activity_query.count()

        # Total users by role (can optionally filter by college)
        user_query = db.session.query(
            User.role,
            func.count(User.id)
        )
        if college_id:
            user_query = user_query.filter(User.college_id == college_id)
        user_role_counts = user_query.group_by(User.role).all()

        # Total IMs created by month (last 6 months)
        six_months_ago = datetime.utcnow() - timedelta(days=180)
        month_filters = im_filters + [InstructionalMaterial.created_at >= six_months_ago]
        ims_by_month = db.session.query(
            extract('year', InstructionalMaterial.created_at).label('year'),
            extract('month', InstructionalMaterial.created_at).label('month'),
            func.count(InstructionalMaterial.id)
        ).filter(*month_filters).group_by('year', 'month').order_by('year', 'month').all()

        return jsonify({
            'status_distribution': [{'status': s, 'count': c} for s, c in im_status_counts],
            'recent_activity_count': recent_activity_count,
            'user_role_distribution': [{'role': r, 'count': c} for r, c in user_role_counts],
            'ims_by_month': [{'year': int(y), 'month': int(m), 'count': c} for y, m, c in ims_by_month]
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@analytics_blueprint.route('/colleges', methods=['GET'])
@jwt_required
@roles_required('Technical Admin', 'UTLDO Admin', 'PIMEC')
def get_college_analytics():
    """Get analytics by college - counts IMs per college correctly"""
    try:
        college_id = request.args.get('college_id', type=int)
        
        # Get all non-deleted IMs with their college info
        ims = InstructionalMaterial.query.filter(
            InstructionalMaterial.is_deleted == False
        ).all()
        
        # Aggregate by college
        college_counts = {}
        
        for im in ims:
            # Determine college from either university_im or service_im
            cid = None
            cname = None
            
            if im.university_im_id and im.university_im:
                cid = im.university_im.college_id
                cname = im.university_im.college.name if im.university_im.college else None
            elif im.service_im_id and im.service_im:
                cid = im.service_im.college_id
                cname = im.service_im.college.name if im.service_im.college else None
            
            if cid is None:
                continue
                
            # Filter by college if specified
            if college_id and cid != college_id:
                continue
            
            if cid not in college_counts:
                college_counts[cid] = {
                    'id': cid, 
                    'name': cname, 
                    'count': 0, 
                    'certified': 0
                }
            
            college_counts[cid]['count'] += 1
            
            if im.status == 'Certified':
                college_counts[cid]['certified'] += 1

        # Calculate completion rate
        for cid in college_counts:
            total = college_counts[cid]['count']
            certified = college_counts[cid]['certified']
            college_counts[cid]['completion_rate'] = round((certified / total * 100) if total > 0 else 0, 2)

        return jsonify({
            'colleges': list(college_counts.values())
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@analytics_blueprint.route('/departments', methods=['GET'])
@jwt_required
@roles_required('Technical Admin', 'UTLDO Admin', 'PIMEC')
def get_department_analytics():
    """Get analytics by department"""
    try:
        college_id = request.args.get('college_id', type=int)
        
        query = db.session.query(
            Department.id,
            Department.name,
            College.name.label('college_name'),
            func.count(InstructionalMaterial.id).label('count')
        ).join(
            College, Department.college_id == College.id
        ).join(
            UniversityIM, Department.id == UniversityIM.department_id
        ).join(
            InstructionalMaterial,
            and_(
                InstructionalMaterial.university_im_id == UniversityIM.id,
                InstructionalMaterial.is_deleted == False
            )
        )

        if college_id:
            query = query.filter(Department.college_id == college_id)

        departments = query.group_by(
            Department.id, Department.name, College.name
        ).all()

        return jsonify({
            'departments': [
                {
                    'id': d_id,
                    'name': d_name,
                    'college_name': c_name,
                    'count': count
                } for d_id, d_name, c_name, count in departments
            ]
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@analytics_blueprint.route('/users/contributions', methods=['GET'])
@jwt_required
@roles_required('Technical Admin', 'UTLDO Admin', 'PIMEC')
def get_user_contributions():
    """Get user contribution analytics with optional college/department filters"""
    try:
        limit = request.args.get('limit', 10, type=int)
        college_id = request.args.get('college_id', type=int)
        department_id = request.args.get('department_id', type=int)
        
        # Base query for top contributors
        query = db.session.query(
            User.id,
            User.first_name,
            User.last_name,
            User.role,
            College.name.label('college_name'),
            func.count(ActivityLog.id).label('activity_count')
        ).join(
            ActivityLog, User.id == ActivityLog.user_id
        ).outerjoin(
            College, User.college_id == College.id
        ).filter(
            ActivityLog.table_name == 'instructionalmaterials'
        )
        
        # Filter by college if provided
        if college_id:
            query = query.filter(User.college_id == college_id)
        
        # Filter by department - need to check if activity relates to an IM in that department
        if department_id:
            im_filters = get_filtered_im_query(department_id=department_id)
            matching_im_ids = db.session.query(InstructionalMaterial.id).filter(*im_filters).subquery()
            query = query.filter(ActivityLog.record_id.in_(db.session.query(matching_im_ids.c.id)))
        
        top_contributors = query.group_by(
            User.id, User.first_name, User.last_name, User.role, College.name
        ).order_by(
            desc('activity_count')
        ).limit(limit).all()

        return jsonify({
            'top_contributors': [
                {
                    'user_id': uid,
                    'name': f"{fname} {lname}",
                    'role': role,
                    'college': college or 'N/A',
                    'contributions': count
                } for uid, fname, lname, role, college, count in top_contributors
            ]
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@analytics_blueprint.route('/activity/timeline', methods=['GET'])
@jwt_required
@roles_required('Technical Admin', 'UTLDO Admin', 'PIMEC')
def get_activity_timeline():
    """Get activity timeline data with optional college/department filters"""
    try:
        days = request.args.get('days', 30, type=int)
        college_id = request.args.get('college_id', type=int)
        department_id = request.args.get('department_id', type=int)
        
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Base query for activities by day
        query = db.session.query(
            func.date(ActivityLog.created_at).label('date'),
            ActivityLog.action,
            func.count(ActivityLog.id).label('count')
        ).filter(
            ActivityLog.created_at >= start_date,
            ActivityLog.table_name == 'instructionalmaterials'
        )
        
        # Filter by college/department if provided
        if college_id or department_id:
            im_filters = get_filtered_im_query(college_id, department_id)
            matching_im_ids = db.session.query(InstructionalMaterial.id).filter(*im_filters).subquery()
            query = query.filter(ActivityLog.record_id.in_(db.session.query(matching_im_ids.c.id)))
        
        activities_by_day = query.group_by(
            func.date(ActivityLog.created_at),
            ActivityLog.action
        ).order_by('date').all()

        # Format for frontend
        timeline_data = {}
        for date_val, action, count in activities_by_day:
            date_str = date_val.strftime('%Y-%m-%d')
            if date_str not in timeline_data:
                timeline_data[date_str] = {'date': date_str, 'CREATE': 0, 'UPDATE': 0}
            timeline_data[date_str][action] = count

        return jsonify({
            'timeline': list(timeline_data.values())
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@analytics_blueprint.route('/submissions/by-user', methods=['GET'])
@jwt_required
@roles_required('Technical Admin', 'UTLDO Admin', 'PIMEC')
def get_submissions_by_user():
    """Get submission counts per user with optional college/department filters"""
    try:
        limit = request.args.get('limit', 10, type=int)
        college_id = request.args.get('college_id', type=int)
        department_id = request.args.get('department_id', type=int)
        
        # Base query for submission counts per user
        query = db.session.query(
            User.id,
            User.first_name,
            User.last_name,
            User.role,
            College.name.label('college_name'),
            func.count(IMSubmission.id).label('submission_count')
        ).join(
            IMSubmission, User.id == IMSubmission.user_id
        ).outerjoin(
            College, User.college_id == College.id
        )
        
        # Filter by college if provided
        if college_id:
            query = query.filter(User.college_id == college_id)
        
        # Filter by department - check if submission relates to an IM in that department
        if department_id:
            im_filters = get_filtered_im_query(department_id=department_id)
            matching_im_ids = db.session.query(InstructionalMaterial.id).filter(*im_filters).subquery()
            query = query.filter(IMSubmission.im_id.in_(db.session.query(matching_im_ids.c.id)))
        
        user_submissions = query.group_by(
            User.id, User.first_name, User.last_name, User.role, College.name
        ).order_by(
            desc('submission_count')
        ).limit(limit).all()

        return jsonify({
            'user_submissions': [
                {
                    'user_id': uid,
                    'name': f"{fname} {lname}",
                    'role': role,
                    'college': college or 'N/A',
                    'submissions': count
                } for uid, fname, lname, role, college, count in user_submissions
            ]
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@analytics_blueprint.route('/submissions/timeline', methods=['GET'])
@jwt_required
@roles_required('Technical Admin', 'UTLDO Admin', 'PIMEC')
def get_submissions_timeline():
    """Get submission frequency over time"""
    try:
        days = request.args.get('days', 30, type=int)
        college_id = request.args.get('college_id', type=int)
        department_id = request.args.get('department_id', type=int)
        
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Base query for submissions by day
        query = db.session.query(
            func.date(IMSubmission.date_submitted).label('date'),
            func.count(IMSubmission.id).label('count')
        ).filter(
            IMSubmission.date_submitted >= start_date
        )
        
        # Filter by college/department if provided
        if college_id or department_id:
            im_filters = get_filtered_im_query(college_id, department_id)
            matching_im_ids = db.session.query(InstructionalMaterial.id).filter(*im_filters).subquery()
            query = query.filter(IMSubmission.im_id.in_(db.session.query(matching_im_ids.c.id)))
        
        submissions_by_day = query.group_by(
            func.date(IMSubmission.date_submitted)
        ).order_by('date').all()

        return jsonify({
            'timeline': [
                {'date': d.strftime('%Y-%m-%d'), 'submissions': c}
                for d, c in submissions_by_day
            ]
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@analytics_blueprint.route('/deadlines', methods=['GET'])
@jwt_required
@roles_required('Technical Admin', 'UTLDO Admin', 'PIMEC')
def get_deadline_analytics():
    """Get deadline-related analytics: upcoming, overdue, on-track IMs"""
    try:
        college_id = request.args.get('college_id', type=int)
        department_id = request.args.get('department_id', type=int)
        
        today = date.today()
        
        # Active statuses (not yet completed)
        active_statuses = ['Assigned to Faculty', 'For PIMEC Evaluation', 'For UTLDO Evaluation', 
                          'For Resubmission', 'For IMER Evaluation']
        
        # Get all non-deleted IMs
        all_ims = InstructionalMaterial.query.filter(
            InstructionalMaterial.is_deleted == False
        ).all()
        
        # Filter by college/department if needed and categorize
        overdue_list = []
        due_soon_list = []
        overdue_count = 0
        due_soon_count = 0
        due_month_count = 0
        on_track_count = 0
        no_deadline_count = 0
        
        for im in all_ims:
            # Get college info for filtering
            im_college_id = None
            im_department_id = None
            subject_name = None
            college_name = None
            
            if im.university_im_id and im.university_im:
                im_college_id = im.university_im.college_id
                im_department_id = im.university_im.department_id
                subject_name = im.university_im.subject.name if im.university_im.subject else None
                college_name = im.university_im.college.name if im.university_im.college else None
            elif im.service_im_id and im.service_im:
                im_college_id = im.service_im.college_id
                subject_name = im.service_im.subject.name if im.service_im.subject else None
                college_name = im.service_im.college.name if im.service_im.college else None
            
            # Apply college/department filters
            if college_id and im_college_id != college_id:
                continue
            if department_id and im_department_id != department_id:
                continue
            
            # Skip completed IMs
            if im.status not in active_statuses:
                continue
            
            # Check deadline status
            if im.due_date is None:
                no_deadline_count += 1
                continue
            
            if im.due_date < today:
                # Overdue
                overdue_count += 1
                days_overdue = (today - im.due_date).days
                if len(overdue_list) < 10:
                    overdue_list.append({
                        'im_id': im.id,
                        'subject': subject_name,
                        'college': college_name,
                        'status': im.status,
                        'due_date': im.due_date.isoformat(),
                        'days_overdue': days_overdue
                    })
            elif im.due_date <= today + timedelta(days=7):
                # Due soon (within 7 days)
                due_soon_count += 1
                days_remaining = (im.due_date - today).days
                if len(due_soon_list) < 10:
                    due_soon_list.append({
                        'im_id': im.id,
                        'subject': subject_name,
                        'college': college_name,
                        'status': im.status,
                        'due_date': im.due_date.isoformat(),
                        'days_remaining': days_remaining
                    })
                due_month_count += 1
            elif im.due_date <= today + timedelta(days=30):
                # Due this month
                due_month_count += 1
                on_track_count += 1
            else:
                # On track (due > 30 days away)
                on_track_count += 1

        return jsonify({
            'summary': {
                'overdue': overdue_count,
                'due_soon': due_soon_count,
                'due_this_month': due_month_count,
                'on_track': on_track_count,
                'no_deadline': no_deadline_count
            },
            'overdue_ims': overdue_list,
            'due_soon_ims': due_soon_list
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@analytics_blueprint.route('/workflow', methods=['GET'])
@jwt_required
@roles_required('Technical Admin', 'UTLDO Admin', 'PIMEC')
def get_workflow_analytics():
    """Get workflow analytics: IMs by status stage, bottlenecks"""
    try:
        college_id = request.args.get('college_id', type=int)
        department_id = request.args.get('department_id', type=int)
        
        # Get all non-deleted IMs
        all_ims = InstructionalMaterial.query.filter(
            InstructionalMaterial.is_deleted == False
        ).all()
        
        # Define workflow stages
        workflow_stages = [
            'Assigned to Faculty',
            'For IMER Evaluation',
            'For PIMEC Evaluation',
            'For UTLDO Evaluation',
            'For Resubmission',
            'Certified',
            'Published'
        ]
        
        # Initialize stage data
        stage_data = {s: {'count': 0, 'name': s} for s in workflow_stages}
        
        # Count IMs by status with proper filtering
        for im in all_ims:
            # Get college/department for filtering
            im_college_id = None
            im_department_id = None
            
            if im.university_im_id and im.university_im:
                im_college_id = im.university_im.college_id
                im_department_id = im.university_im.department_id
            elif im.service_im_id and im.service_im:
                im_college_id = im.service_im.college_id
            
            # Apply filters
            if college_id and im_college_id != college_id:
                continue
            if department_id and im_department_id != department_id:
                continue
            
            # Count by status
            status = im.status
            if status in stage_data:
                stage_data[status]['count'] += 1
            else:
                # Add new status if not in predefined list
                stage_data[status] = {'count': 1, 'name': status}
        
        # Get IMs stuck at each stage (no activity in last 14 days)
        fourteen_days_ago = datetime.utcnow() - timedelta(days=14)
        evaluation_stages = ['For IMER Evaluation', 'For PIMEC Evaluation', 'For UTLDO Evaluation', 'For Resubmission']
        stuck_counts = {stage: 0 for stage in evaluation_stages}
        
        # Get recent activity IM ids
        recent_activity_im_ids = set(
            r[0] for r in db.session.query(ActivityLog.record_id).filter(
                ActivityLog.table_name == 'instructionalmaterials',
                ActivityLog.created_at >= fourteen_days_ago
            ).all()
        )
        
        # Check each IM for being stuck
        for im in all_ims:
            if im.status in evaluation_stages:
                # Apply same college/department filters
                im_college_id = None
                im_department_id = None
                
                if im.university_im_id and im.university_im:
                    im_college_id = im.university_im.college_id
                    im_department_id = im.university_im.department_id
                elif im.service_im_id and im.service_im:
                    im_college_id = im.service_im.college_id
                
                if college_id and im_college_id != college_id:
                    continue
                if department_id and im_department_id != department_id:
                    continue
                
                # Check if stuck (no recent activity)
                if im.id not in recent_activity_im_ids:
                    stuck_counts[im.status] += 1

        # Calculate totals
        completed_statuses = ['Certified', 'Published']
        total_active = sum(stage_data[s]['count'] for s in stage_data if s not in completed_statuses)
        total_completed = sum(stage_data.get(s, {}).get('count', 0) for s in completed_statuses)

        return jsonify({
            'stages': list(stage_data.values()),
            'stuck_ims': stuck_counts,
            'total_active': total_active,
            'total_completed': total_completed
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@analytics_blueprint.route('/export', methods=['GET'])
@jwt_required
@roles_required('Technical Admin', 'UTLDO Admin', 'PIMEC')
def export_analytics():
    """Export analytics data as CSV"""
    try:
        college_id = request.args.get('college_id', type=int)
        department_id = request.args.get('department_id', type=int)

        csv_data = AnalyticsService.export_overview_to_csv(college_id, department_id)

        return Response(
            csv_data,
            mimetype='text/csv',
            headers={
                'Content-Disposition': 'attachment; filename=analytics_report.csv'
            }
        )
    except Exception as e:
        return jsonify({'error': str(e)}), 500
