"""
维修工单服务
"""
from datetime import datetime
from flask import g
from database.db import db
from models.maintenance import MaintenanceWorkOrder
from models.production import Equipment
from models.log import Log
from utils.response import Response
from utils.validator import Validator


class MaintenanceService:
    """维修工单服务类"""

    @staticmethod
    def get_work_orders(page=1, size=10, status=None, equipment_id=None, priority=None):
        """获取维修工单列表"""
        query = MaintenanceWorkOrder.query

        if status:
            query = query.filter(MaintenanceWorkOrder.status == status)
        if equipment_id:
            query = query.filter(MaintenanceWorkOrder.equipment_id == equipment_id)
        if priority:
            query = query.filter(MaintenanceWorkOrder.priority == priority)

        pagination = query.order_by(MaintenanceWorkOrder.create_time.desc()).paginate(
            page=page, per_page=size, error_out=False
        )

        items = [item.to_dict() for item in pagination.items]
        return Response.paginate(items, pagination.total, page, size)

    @staticmethod
    def get_work_order_by_id(order_id):
        """获取维修工单详情"""
        order = MaintenanceWorkOrder.get_by_id(order_id)
        if not order:
            return Response.not_found('维修工单不存在')

        order_dict = order.to_dict()
        try:
            order_dict['spare_usage'] = [item.to_dict() for item in order.spare_usage.all()]
        except Exception:
            order_dict['spare_usage'] = []

        return Response.success(order_dict)

    @staticmethod
    def create_work_order(data):
        """创建维修工单"""
        validation = Validator.validate_form(data, {
            'order_name': ['required'],
            'equipment_id': ['required']
        })

        if not validation['valid']:
            return Response.bad_request(list(validation['errors'].values())[0])

        now = datetime.now()
        order_code = f"WO-{now.strftime('%Y%m%d%H%M%S')}-{MaintenanceWorkOrder.query.count() + 1}"

        equipment = Equipment.get_by_id(data['equipment_id'])
        equipment_type = equipment.equipment_type if equipment else None

        order = MaintenanceWorkOrder(
            order_code=order_code,
            order_name=data['order_name'],
            equipment_id=data['equipment_id'],
            equipment_type=equipment_type,
            fault_description=data.get('fault_description'),
            work_type=data.get('work_type', 'corrective'),
            priority=data.get('priority', 'medium'),
            status=data.get('status', 'pending'),
            assigned_to=data.get('assigned_to'),
            plan_start_time=data.get('plan_start_time'),
            plan_end_time=data.get('plan_end_time'),
            remark=data.get('remark')
        )

        try:
            order.save()
            Log.add_log(g.user_id, g.username, 'create', 'maintenance_work_order',
                       f'创建维修工单: {order.order_name}')
            return Response.created({'id': order.id, 'order_code': order.order_code}, '创建成功')
        except Exception as e:
            db.session.rollback()
            return Response.error(f'创建失败: {str(e)}')

    @staticmethod
    def update_work_order(order_id, data):
        """更新维修工单"""
        order = MaintenanceWorkOrder.get_by_id(order_id)
        if not order:
            return Response.not_found('维修工单不存在')

        update_fields = [
            'order_name', 'equipment_id', 'fault_description', 'work_type',
            'priority', 'assigned_to', 'plan_start_time', 'plan_end_time',
            'work_content', 'materials', 'materials_cost', 'labor_cost',
            'total_cost', 'remark'
        ]

        for field in update_fields:
            if field in data:
                setattr(order, field, data[field])

        if 'equipment_id' in data:
            equipment = Equipment.get_by_id(data['equipment_id'])
            order.equipment_type = equipment.equipment_type if equipment else None

        order.update_time = datetime.now()

        try:
            db.session.commit()
            Log.add_log(g.user_id, g.username, 'update', 'maintenance_work_order',
                       f'更新维修工单: {order.order_name}')
            return Response.success(order.to_dict(), '更新成功')
        except Exception as e:
            db.session.rollback()
            return Response.error(f'更新失败: {str(e)}')

    @staticmethod
    def update_order_status(order_id, status):
        """更新工单状态"""
        order = MaintenanceWorkOrder.get_by_id(order_id)
        if not order:
            return Response.not_found('维修工单不存在')

        valid_status = ['pending', 'in_progress', 'completed', 'cancelled']
        if status not in valid_status:
            return Response.bad_request('无效的状态值')

        order.status = status
        now = datetime.now()

        if status == 'in_progress' and not order.actual_start_time:
            order.actual_start_time = now
        elif status == 'completed':
            order.actual_end_time = now
            total = (order.materials_cost or 0) + (order.labor_cost or 0)
            order.total_cost = total

        order.update_time = now

        try:
            db.session.commit()
            Log.add_log(g.user_id, g.username, 'status_update', 'maintenance_work_order',
                       f'工单 {order.order_code} 状态更新为 {status}')
            return Response.success(order.to_dict(), '状态更新成功')
        except Exception as e:
            db.session.rollback()
            return Response.error(f'状态更新失败: {str(e)}')

    @staticmethod
    def delete_work_order(order_id):
        """删除维修工单"""
        order = MaintenanceWorkOrder.get_by_id(order_id)
        if not order:
            return Response.not_found('维修工单不存在')

        try:
            order.delete()
            Log.add_log(g.user_id, g.username, 'delete', 'maintenance_work_order',
                       f'删除维修工单: {order.order_name}')
            return Response.success(None, '删除成功')
        except Exception as e:
            db.session.rollback()
            return Response.error(f'删除失败: {str(e)}')

    @staticmethod
    def get_work_order_statistics():
        """获取工单统计"""
        total = MaintenanceWorkOrder.query.count()
        pending = MaintenanceWorkOrder.query.filter_by(status='pending').count()
        in_progress = MaintenanceWorkOrder.query.filter_by(status='in_progress').count()
        completed = MaintenanceWorkOrder.query.filter_by(status='completed').count()
        cancelled = MaintenanceWorkOrder.query.filter_by(status='cancelled').count()

        return Response.success({
            'total': total,
            'pending': pending,
            'in_progress': in_progress,
            'completed': completed,
            'cancelled': cancelled
        })
