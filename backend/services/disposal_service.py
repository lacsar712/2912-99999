"""
不合格品处置服务
"""
from datetime import datetime, timedelta
from flask import g
from database.db import db
from models.disposal import DisposalOrder, DisposalApproval, DisposalResult
from models.production import Equipment, ProductionRecord
from models.log import Log
from utils.response import Response
from utils.validator import Validator


class DisposalOrderService:
    """待处置单服务类"""

    @staticmethod
    def _generate_order_code():
        """生成处置单号"""
        now = datetime.now()
        count = DisposalOrder.query.count() + 1
        return f"DIS-{now.strftime('%Y%m%d%H%M%S')}-{count}"

    @staticmethod
    def get_orders(page=1, size=10, status=None, disposal_type=None, source_type=None,
                   keyword=None, start_date=None, end_date=None):
        """获取待处置单列表"""
        query = DisposalOrder.query

        if status and status != 'all':
            query = query.filter(DisposalOrder.status == status)
        if disposal_type:
            query = query.filter(DisposalOrder.suggested_disposal == disposal_type)
        if source_type:
            query = query.filter(DisposalOrder.source_type == source_type)
        if keyword:
            query = query.filter(
                (DisposalOrder.order_code.like(f'%{keyword}%')) |
                (DisposalOrder.related_name.like(f'%{keyword}%')) |
                (DisposalOrder.defect_description.like(f'%{keyword}%'))
            )
        if start_date:
            query = query.filter(DisposalOrder.apply_time >= start_date)
        if end_date:
            query = query.filter(DisposalOrder.apply_time <= end_date)

        pagination = query.order_by(DisposalOrder.create_time.desc()).paginate(
            page=page, per_page=size, error_out=False
        )

        items = [item.to_dict() for item in pagination.items]
        return Response.paginate(items, pagination.total, page, size)

    @staticmethod
    def get_my_pending_approvals(page=1, size=10):
        """获取我待审的列表"""
        user_id = g.user_id if hasattr(g, 'user_id') else None
        username = g.username if hasattr(g, 'username') else ''

        query = DisposalOrder.query.filter(
            DisposalOrder.status == 'pending_approval',
            DisposalOrder.current_approval_level.in_([1, 2])
        )

        pagination = query.order_by(DisposalOrder.create_time.asc()).paginate(
            page=page, per_page=size, error_out=False
        )

        items = [item.to_dict() for item in pagination.items]
        return Response.paginate(items, pagination.total, page, size)

    @staticmethod
    def get_order_by_id(order_id):
        """获取待处置单详情"""
        order = DisposalOrder.query.filter(DisposalOrder.id == order_id).first()
        if not order:
            return Response.not_found('待处置单不存在')
        return Response.success(order.to_dict())

    @staticmethod
    def create_order(data):
        """创建待处置单"""
        validation = Validator.validate_form(data, {
            'related_type': ['required'],
            'quantity': ['required'],
            'defect_description': ['required'],
            'suggested_disposal': ['required']
        })

        if not validation['valid']:
            return Response.bad_request(list(validation['errors'].values())[0])

        now = datetime.now()
        order_code = DisposalOrderService._generate_order_code()

        related_id = data.get('related_id')
        related_code = data.get('related_code', '')
        related_name = data.get('related_name', '')

        if related_id and data.get('related_type') == 'equipment':
            equipment = Equipment.get_by_id(related_id)
            if equipment:
                related_code = equipment.equipment_code
                related_name = equipment.equipment_name

        order = DisposalOrder(
            order_code=order_code,
            source_type=data.get('source_type', 'manual'),
            source_id=data.get('source_id'),
            source_code=data.get('source_code'),
            related_type=data.get('related_type'),
            related_id=related_id,
            related_code=related_code,
            related_name=related_name,
            quantity=int(data.get('quantity', 1)),
            unit=data.get('unit', '件'),
            unit_price=float(data.get('unit_price', 0)),
            defect_description=data.get('defect_description'),
            suggested_disposal=data.get('suggested_disposal'),
            applicant_id=g.user_id if hasattr(g, 'user_id') else None,
            applicant=g.username if hasattr(g, 'username') else data.get('applicant', ''),
            apply_time=now,
            current_approval_level=0,
            status='draft',
            attachment=data.get('attachment'),
            remark=data.get('remark')
        )

        try:
            order.save()
            Log.add_log(
                g.user_id if hasattr(g, 'user_id') else None,
                g.username if hasattr(g, 'username') else '',
                'create', 'disposal_order',
                f'创建设置单: {order_code}'
            )
            return Response.created({'id': order.id, 'order_code': order_code}, '创建成功')
        except Exception as e:
            db.session.rollback()
            return Response.error(f'创建失败: {str(e)}')

    @staticmethod
    def update_order(order_id, data):
        """更新待处置单"""
        order = DisposalOrder.query.filter(DisposalOrder.id == order_id).first()
        if not order:
            return Response.not_found('待处置单不存在')

        if order.status not in ['draft', 'returned']:
            return Response.error('只能编辑草稿或被退回的处置单')

        update_fields = [
            'source_type', 'source_id', 'source_code',
            'related_type', 'related_id', 'related_code', 'related_name',
            'quantity', 'unit', 'unit_price', 'defect_description',
            'suggested_disposal', 'attachment', 'remark'
        ]

        for field in update_fields:
            if field in data:
                if field == 'quantity':
                    setattr(order, field, int(data[field]))
                elif field == 'unit_price':
                    setattr(order, field, float(data[field]))
                else:
                    setattr(order, field, data[field])

        order.update_time = datetime.now()

        try:
            db.session.commit()
            Log.add_log(g.user_id, g.username, 'update', 'disposal_order',
                       f'更新处置单: {order.order_code}')
            return Response.success(order.to_dict(), '更新成功')
        except Exception as e:
            db.session.rollback()
            return Response.error(f'更新失败: {str(e)}')

    @staticmethod
    def delete_order(order_id):
        """删除待处置单"""
        order = DisposalOrder.query.filter(DisposalOrder.id == order_id).first()
        if not order:
            return Response.not_found('待处置单不存在')

        if order.status not in ['draft', 'rejected']:
            return Response.error('只能删除草稿或已驳回的处置单')

        try:
            order.delete()
            Log.add_log(g.user_id, g.username, 'delete', 'disposal_order',
                       f'删除处置单: {order.order_code}')
            return Response.success(None, '删除成功')
        except Exception as e:
            db.session.rollback()
            return Response.error(f'删除失败: {str(e)}')

    @staticmethod
    def submit_order(order_id):
        """提交审批"""
        order = DisposalOrder.query.filter(DisposalOrder.id == order_id).first()
        if not order:
            return Response.not_found('待处置单不存在')

        if order.status not in ['draft', 'returned']:
            return Response.error('当前状态不允许提交')

        order.status = 'pending_approval'
        order.current_approval_level = 1
        order.update_time = datetime.now()

        try:
            db.session.commit()
            Log.add_log(g.user_id, g.username, 'submit', 'disposal_order',
                       f'提交处置单审批: {order.order_code}')
            return Response.success(order.to_dict(), '提交成功')
        except Exception as e:
            db.session.rollback()
            return Response.error(f'提交失败: {str(e)}')

    @staticmethod
    def quick_create_from_quality(record_id, data):
        """从质检不合格记录快速创建"""
        record = ProductionRecord.get_by_id(record_id) if record_id else None

        if record and record.defect_count and record.defect_count > 0:
            data['source_type'] = 'quality_check'
            data['source_id'] = record_id
            data['source_code'] = f'PR-{record.id}'
            data['quantity'] = record.defect_count

        return DisposalOrderService.create_order(data)


class DisposalApprovalService:
    """审批服务类"""

    @staticmethod
    def _check_approval_permission(order):
        """检查审批权限"""
        return True

    @staticmethod
    def approve_order(order_id, data):
        """审批通过"""
        order = DisposalOrder.query.filter(DisposalOrder.id == order_id).first()
        if not order:
            return Response.not_found('待处置单不存在')

        if order.status != 'pending_approval':
            return Response.error('当前状态不允许审批')

        if not DisposalApprovalService._check_approval_permission(order):
            return Response.forbidden('无审批权限')

        current_level = order.current_approval_level
        opinion = data.get('opinion', '')
        now = datetime.now()

        approval = DisposalApproval(
            disposal_order_id=order_id,
            approval_level=current_level,
            approval_role='班组长' if current_level == 1 else '部门主管',
            approver_id=g.user_id if hasattr(g, 'user_id') else None,
            approver=g.username if hasattr(g, 'username') else data.get('approver', ''),
            approval_time=now,
            action='approve',
            opinion=opinion
        )

        try:
            db.session.add(approval)

            if current_level == 1:
                order.current_approval_level = 2
            elif current_level == 2:
                order.current_approval_level = 3
                order.status = 'approved'

            order.update_time = now
            db.session.commit()

            Log.add_log(g.user_id, g.username, 'approve', 'disposal_order',
                       f'审批通过处置单: {order.order_code}, 级别: {current_level}')
            return Response.success(order.to_dict(), '审批通过')
        except Exception as e:
            db.session.rollback()
            return Response.error(f'审批失败: {str(e)}')

    @staticmethod
    def reject_order(order_id, data):
        """审批驳回"""
        order = DisposalOrder.query.filter(DisposalOrder.id == order_id).first()
        if not order:
            return Response.not_found('待处置单不存在')

        if order.status != 'pending_approval':
            return Response.error('当前状态不允许审批')

        opinion = data.get('opinion', '')
        if not opinion:
            return Response.bad_request('请填写驳回意见')

        now = datetime.now()
        current_level = order.current_approval_level

        approval = DisposalApproval(
            disposal_order_id=order_id,
            approval_level=current_level,
            approval_role='班组长' if current_level == 1 else '部门主管',
            approver_id=g.user_id if hasattr(g, 'user_id') else None,
            approver=g.username if hasattr(g, 'username') else data.get('approver', ''),
            approval_time=now,
            action='reject',
            opinion=opinion
        )

        try:
            db.session.add(approval)
            order.status = 'rejected'
            order.current_approval_level = 0
            order.update_time = now
            db.session.commit()

            Log.add_log(g.user_id, g.username, 'reject', 'disposal_order',
                       f'审批驳回处置单: {order.order_code}')
            return Response.success(order.to_dict(), '已驳回')
        except Exception as e:
            db.session.rollback()
            return Response.error(f'操作失败: {str(e)}')

    @staticmethod
    def return_order(order_id, data):
        """审批退回（退回修改）"""
        order = DisposalOrder.query.filter(DisposalOrder.id == order_id).first()
        if not order:
            return Response.not_found('待处置单不存在')

        if order.status != 'pending_approval':
            return Response.error('当前状态不允许退回')

        opinion = data.get('opinion', '')
        if not opinion:
            return Response.bad_request('请填写退回意见')

        now = datetime.now()
        current_level = order.current_approval_level

        approval = DisposalApproval(
            disposal_order_id=order_id,
            approval_level=current_level,
            approval_role='班组长' if current_level == 1 else '部门主管',
            approver_id=g.user_id if hasattr(g, 'user_id') else None,
            approver=g.username if hasattr(g, 'username') else data.get('approver', ''),
            approval_time=now,
            action='return',
            opinion=opinion
        )

        try:
            db.session.add(approval)
            order.status = 'returned'
            order.current_approval_level = 0
            order.update_time = now
            db.session.commit()

            Log.add_log(g.user_id, g.username, 'return', 'disposal_order',
                       f'退回处置单修改: {order.order_code}')
            return Response.success(order.to_dict(), '已退回')
        except Exception as e:
            db.session.rollback()
            return Response.error(f'操作失败: {str(e)}')

    @staticmethod
    def record_disposal_result(order_id, data):
        """记录处置结果"""
        order = DisposalOrder.query.filter(DisposalOrder.id == order_id).first()
        if not order:
            return Response.not_found('待处置单不存在')

        if order.status != 'approved':
            return Response.error('请先完成审批')

        validation = Validator.validate_form(data, {
            'final_decision': ['required'],
            'operation_record': ['required']
        })

        if not validation['valid']:
            return Response.bad_request(list(validation['errors'].values())[0])

        now = datetime.now()
        final_decision = data.get('final_decision')
        loss_estimate = float(data.get('loss_estimate', 0))

        if final_decision == 'scrap':
            loss_estimate = order.quantity * float(order.unit_price or 0)
        elif final_decision == 'rework':
            loss_estimate = float(data.get('loss_estimate', order.quantity * 20))
        elif final_decision == 'concession':
            loss_estimate = float(data.get('loss_estimate', 0))

        result = DisposalResult(
            disposal_order_id=order_id,
            final_decision=final_decision,
            operator_id=g.user_id if hasattr(g, 'user_id') else None,
            operator=g.username if hasattr(g, 'username') else data.get('operator', ''),
            operate_time=now,
            loss_estimate=loss_estimate,
            operation_record=data.get('operation_record'),
            remark=data.get('remark')
        )

        try:
            db.session.add(result)
            order.status = 'completed'
            order.update_time = now
            db.session.commit()

            Log.add_log(g.user_id, g.username, 'complete', 'disposal_order',
                       f'完成处置单: {order.order_code}, 处置方式: {final_decision}')
            return Response.success(order.to_dict(), '处置完成')
        except Exception as e:
            db.session.rollback()
            return Response.error(f'操作失败: {str(e)}')


class DisposalStatisticsService:
    """统计服务类"""

    @staticmethod
    def get_monthly_statistics(year=None, month=None):
        """按月统计返工/让步/报废的数量与对应损失估算"""
        now = datetime.now()
        if not year:
            year = now.year
        if not month:
            month = now.month

        start_date = datetime(year, month, 1)
        if month == 12:
            end_date = datetime(year + 1, 1, 1)
        else:
            end_date = datetime(year, month + 1, 1)

        results = db.session.query(
            DisposalResult.final_decision,
            db.func.sum(DisposalOrder.quantity),
            db.func.sum(DisposalResult.loss_estimate),
            db.func.count(DisposalResult.id)
        ).join(
            DisposalOrder, DisposalResult.disposal_order_id == DisposalOrder.id
        ).filter(
            DisposalResult.operate_time >= start_date,
            DisposalResult.operate_time < end_date
        ).group_by(
            DisposalResult.final_decision
        ).all()

        stats = {
            'rework': {'count': 0, 'quantity': 0, 'loss': 0},
            'concession': {'count': 0, 'quantity': 0, 'loss': 0},
            'scrap': {'count': 0, 'quantity': 0, 'loss': 0}
        }

        for decision, qty, loss, cnt in results:
            if decision in stats:
                stats[decision]['count'] = cnt
                stats[decision]['quantity'] = float(qty or 0)
                stats[decision]['loss'] = float(loss or 0)

        total_count = sum(s['count'] for s in stats.values())
        total_quantity = sum(s['quantity'] for s in stats.values())
        total_loss = sum(s['loss'] for s in stats.values())

        return Response.success({
            'year': year,
            'month': month,
            'statistics': stats,
            'total': {
                'count': total_count,
                'quantity': total_quantity,
                'loss': total_loss
            }
        })

    @staticmethod
    def get_trend_statistics(months=6):
        """获取月度趋势统计"""
        now = datetime.now()
        trend_data = []

        for i in range(months - 1, -1, -1):
            month_date = now - timedelta(days=i * 30)
            year = month_date.year
            month = month_date.month

            start_date = datetime(year, month, 1)
            if month == 12:
                end_date = datetime(year + 1, 1, 1)
            else:
                end_date = datetime(year, month + 1, 1)

            results = db.session.query(
                DisposalResult.final_decision,
                db.func.sum(DisposalOrder.quantity),
                db.func.sum(DisposalResult.loss_estimate)
            ).join(
                DisposalOrder, DisposalResult.disposal_order_id == DisposalOrder.id
            ).filter(
                DisposalResult.operate_time >= start_date,
                DisposalResult.operate_time < end_date
            ).group_by(
                DisposalResult.final_decision
            ).all()

            month_stats = {
                'month': f'{year}-{month:02d}',
                'rework': {'quantity': 0, 'loss': 0},
                'concession': {'quantity': 0, 'loss': 0},
                'scrap': {'quantity': 0, 'loss': 0}
            }

            for decision, qty, loss in results:
                if decision in month_stats:
                    month_stats[decision]['quantity'] = float(qty or 0)
                    month_stats[decision]['loss'] = float(loss or 0)

            trend_data.append(month_stats)

        return Response.success({
            'months': months,
            'trend': trend_data
        })

    @staticmethod
    def get_dashboard():
        """获取处置概览统计"""
        total_orders = DisposalOrder.query.count()
        pending_orders = DisposalOrder.query.filter_by(status='pending_approval').count()
        completed_orders = DisposalOrder.query.filter_by(status='completed').count()
        rejected_orders = DisposalOrder.query.filter_by(status='rejected').count()

        total_loss = db.session.query(
            db.func.sum(DisposalResult.loss_estimate)
        ).scalar() or 0

        now = datetime.now()
        month_start = now.replace(day=1, hour=0, minute=0, second=0)

        month_results = db.session.query(
            DisposalResult.final_decision,
            db.func.sum(DisposalOrder.quantity)
        ).join(
            DisposalOrder, DisposalResult.disposal_order_id == DisposalOrder.id
        ).filter(
            DisposalResult.operate_time >= month_start
        ).group_by(
            DisposalResult.final_decision
        ).all()

        month_stats = {
            'rework': 0,
            'concession': 0,
            'scrap': 0
        }

        for decision, qty in month_results:
            if decision in month_stats:
                month_stats[decision] = float(qty or 0)

        return Response.success({
            'total_orders': total_orders,
            'pending_orders': pending_orders,
            'completed_orders': completed_orders,
            'rejected_orders': rejected_orders,
            'total_loss': float(total_loss),
            'monthly_statistics': month_stats
        })
