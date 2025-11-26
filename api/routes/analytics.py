from flask import request, jsonify
from flask_smorest import Blueprint
from api.middleware import jwt_required, roles_required
from sqlalchemy import func, desc, and_, extract, or_
from api.extensions import db
from api.models.activitylog import ActivityLog
from api.models.instructionalmaterials import InstructionalMaterial
from api.models.users import User
from api.models.colleges import College
from api.models.departments import Department
from api.models.universityims import UniversityIM
from api.models.serviceims import ServiceIM
from datetime import datetime, timedelta

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
    """Get analytics by college"""
    try:
        college_id = request.args.get('college_id', type=int)
        
        # Base query for university IMs
        university_query = db.session.query(
            College.id,
            College.name,
            func.count(InstructionalMaterial.id).label('count')
        ).join(
            UniversityIM, College.id == UniversityIM.college_id
        ).join(
            InstructionalMaterial, 
            and_(
                InstructionalMaterial.university_im_id == UniversityIM.id,
                InstructionalMaterial.is_deleted == False
            )
        )
        
        if college_id:
            university_query = university_query.filter(College.id == college_id)
        
        university_im_counts = university_query.group_by(College.id, College.name).all()

        # Base query for service IMs
        service_query = db.session.query(
            College.id,
            College.name,
            func.count(InstructionalMaterial.id).label('count')
        ).join(
            ServiceIM, College.id == ServiceIM.college_id
        ).join(
            InstructionalMaterial,
            and_(
                InstructionalMaterial.service_im_id == ServiceIM.id,
                InstructionalMaterial.is_deleted == False
            )
        )
        
        if college_id:
            service_query = service_query.filter(College.id == college_id)
        
        service_im_counts = service_query.group_by(College.id, College.name).all()

        # Combine counts
        college_counts = {}
        for cid, cname, count in university_im_counts:
            if cid not in college_counts:
                college_counts[cid] = {'id': cid, 'name': cname, 'count': 0}
            college_counts[cid]['count'] += count

        for cid, cname, count in service_im_counts:
            if cid not in college_counts:
                college_counts[cid] = {'id': cid, 'name': cname, 'count': 0}
            college_counts[cid]['count'] += count

        # Get certified IMs per college
        certified_university_query = db.session.query(
            College.id,
            func.count(InstructionalMaterial.id).label('certified_count')
        ).join(
            UniversityIM, College.id == UniversityIM.college_id
        ).join(
            InstructionalMaterial,
            and_(
                InstructionalMaterial.university_im_id == UniversityIM.id,
                InstructionalMaterial.status == 'Certified',
                InstructionalMaterial.is_deleted == False
            )
        )
        
        if college_id:
            certified_university_query = certified_university_query.filter(College.id == college_id)
        
        certified_university = certified_university_query.group_by(College.id).all()

        certified_service_query = db.session.query(
            College.id,
            func.count(InstructionalMaterial.id).label('certified_count')
        ).join(
            ServiceIM, College.id == ServiceIM.college_id
        ).join(
            InstructionalMaterial,
            and_(
                InstructionalMaterial.service_im_id == ServiceIM.id,
                InstructionalMaterial.status == 'Certified',
                InstructionalMaterial.is_deleted == False
            )
        )
        
        if college_id:
            certified_service_query = certified_service_query.filter(College.id == college_id)
        
        certified_service = certified_service_query.group_by(College.id).all()

        # Add certified counts
        for cid, cert_count in certified_university:
            if cid in college_counts:
                college_counts[cid]['certified'] = college_counts[cid].get('certified', 0) + cert_count

        for cid, cert_count in certified_service:
            if cid in college_counts:
                college_counts[cid]['certified'] = college_counts[cid].get('certified', 0) + cert_count

        # Calculate completion rate
        for cid in college_counts:
            total = college_counts[cid]['count']
            certified = college_counts[cid].get('certified', 0)
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
        for date, action, count in activities_by_day:
            date_str = date.strftime('%Y-%m-%d')
            if date_str not in timeline_data:
                timeline_data[date_str] = {'date': date_str, 'CREATE': 0, 'UPDATE': 0}
            timeline_data[date_str][action] = count

        return jsonify({
            'timeline': list(timeline_data.values())
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
