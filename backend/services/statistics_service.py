"""
统计服务
"""
from flask import g
from datetime import datetime, timedelta
from database.db import db
from models.data import Data
from models.user import User
from models.log import Log
from utils.response import Response


class StatisticsService:
    """统计服务类"""

    @staticmethod
    def get_overview():
        """
        获取统计概览

        Returns:
            Response对象
        """
        # 总数据量
        total_count = Data.query.filter(Data.status == 1).count()

        # 今日新增
        today = datetime.now().date()
        today_count = Data.query.filter(
            Data.status == 1,
            db.func.date(Data.create_time) == today
        ).count()

        # 类型分布
        type_distribution = db.session.query(
            Data.type,
            db.func.count(Data.id)
        ).filter(
            Data.status == 1
        ).group_by(Data.type).all()

        type_dist = {t: c for t, c in type_distribution}

        # 近6个月趋势
        six_months_ago = datetime.now() - timedelta(days=180)
        monthly_data = db.session.query(
            db.func.strftime('%Y-%m', Data.create_time).label('month'),
            db.func.count(Data.id).label('count')
        ).filter(
            Data.status == 1,
            Data.create_time >= six_months_ago
        ).group_by('month').all()

        # 构建趋势数据
        months = []
        values = []
        for i in range(6):
            month = (datetime.now() - timedelta(days=30 * (5 - i))).strftime('%Y-%m')
            months.append(month)
            count = next((c for m, c in monthly_data if m == month), 0)
            values.append(count)

        return Response.success({
            'totalCount': total_count,
            'todayCount': today_count,
            'typeDistribution': type_dist,
            'trend': {
                'labels': months,
                'values': values
            }
        })

    @staticmethod
    def get_type_statistics():
        """
        获取类型统计

        Returns:
            Response对象
        """
        type_stats = db.session.query(
            Data.type,
            db.func.count(Data.id).label('count'),
            db.func.max(Data.update_time).label('last_update')
        ).filter(
            Data.status == 1
        ).group_by(Data.type).all()

        result = [{
            'type': t,
            'count': c,
            'lastUpdate': u.strftime('%Y-%m-%d %H:%M:%S') if u else None
        } for t, c, u in type_stats]

        return Response.success(result)

    @staticmethod
    def get_user_statistics():
        """
        获取用户统计

        Returns:
            Response对象
        """
        # 用户总数
        total_users = User.query.filter(User.status == 1).count()

        # 角色分布
        role_distribution = db.session.query(
            User.role,
            db.func.count(User.id)
        ).filter(
            User.status == 1
        ).group_by(User.role).all()

        # 活跃用户（近7天有操作）
        seven_days_ago = datetime.now() - timedelta(days=7)
        active_users = db.session.query(
            db.func.count(db.distinct(Log.user_id))
        ).filter(
            Log.create_time >= seven_days_ago
        ).scalar()

        return Response.success({
            'totalUsers': total_users,
            'roleDistribution': {r: c for r, c in role_distribution},
            'activeUsers': active_users or 0
        })

    @staticmethod
    def get_operation_log(page=1, size=20, user_id=None, action=None):
        """
        获取操作日志

        Args:
            page: 页码
            size: 每页条数
            user_id: 用户ID
            action: 操作类型

        Returns:
            Response对象
        """
        query = Log.query.filter(Log.status == 1)

        if user_id:
            query = query.filter(Log.user_id == user_id)

        if action:
            query = query.filter(Log.action == action)

        pagination = query.order_by(Log.create_time.desc()).paginate(
            page=page,
            per_page=size,
            error_out=False
        )

        return Response.paginate(
            [log.to_dict() for log in pagination.items],
            pagination.total,
            page,
            size
        )
