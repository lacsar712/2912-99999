"""
备件库存服务
"""
from datetime import datetime, timedelta
import json
from flask import g
from database.db import db
from models.spare import SparePart, SpareInbound, SpareOutbound, SpareInventory
from models.maintenance import MaintenanceWorkOrder
from models.production import AlertRecord, Equipment
from models.log import Log
from utils.response import Response
from utils.validator import Validator


class SparePartService:
    """备件档案服务类"""

    @staticmethod
    def get_parts(page=1, size=10, equipment_type=None, keyword=None, low_stock_only=False):
        """获取备件列表"""
        query = SparePart.query.filter(SparePart.status == 1)

        if equipment_type:
            query = query.filter(SparePart.equipment_type == equipment_type)
        if keyword:
            query = query.filter(
                (SparePart.part_code.like(f'%{keyword}%')) |
                (SparePart.part_name.like(f'%{keyword}%'))
            )
        if low_stock_only:
            query = query.filter(SparePart.current_stock <= SparePart.safety_stock)

        pagination = query.order_by(SparePart.create_time.desc()).paginate(
            page=page, per_page=size, error_out=False
        )

        items = [item.to_dict() for item in pagination.items]
        return Response.paginate(items, pagination.total, page, size)

    @staticmethod
    def get_part_by_id(part_id):
        """获取备件详情"""
        part = SparePart.get_by_id(part_id)
        if not part:
            return Response.not_found('备件不存在')
        return Response.success(part.to_dict())

    @staticmethod
    def create_part(data):
        """创建备件"""
        validation = Validator.validate_form(data, {
            'part_code': ['required'],
            'part_name': ['required']
        })

        if not validation['valid']:
            return Response.bad_request(list(validation['errors'].values())[0])

        if SparePart.query.filter_by(part_code=data['part_code'], status=1).first():
            return Response.error('备件编号已存在', 409)

        part = SparePart(
            part_code=data['part_code'],
            part_name=data['part_name'],
            specification=data.get('specification'),
            unit=data.get('unit'),
            safety_stock=data.get('safety_stock', 0),
            current_stock=data.get('current_stock', 0),
            equipment_type=data.get('equipment_type'),
            equipment_id=data.get('equipment_id'),
            unit_price=data.get('unit_price', 0),
            location=data.get('location'),
            remark=data.get('remark')
        )

        try:
            part.save()
            Log.add_log(g.user_id, g.username, 'create', 'spare_part',
                       f'创建备件: {part.part_name}')
            SparePartService.check_and_create_low_stock_alert(part)
            return Response.created({'id': part.id, 'part_code': part.part_code}, '创建成功')
        except Exception as e:
            db.session.rollback()
            return Response.error(f'创建失败: {str(e)}')

    @staticmethod
    def update_part(part_id, data):
        """更新备件"""
        part = SparePart.get_by_id(part_id)
        if not part:
            return Response.not_found('备件不存在')

        if 'part_code' in data and data['part_code'] != part.part_code:
            if SparePart.query.filter(
                SparePart.part_code == data['part_code'],
                SparePart.status == 1,
                SparePart.id != part_id
            ).first():
                return Response.error('备件编号已存在', 409)

        update_fields = [
            'part_code', 'part_name', 'specification', 'unit',
            'safety_stock', 'current_stock', 'equipment_type',
            'equipment_id', 'unit_price', 'location', 'remark'
        ]

        for field in update_fields:
            if field in data:
                setattr(part, field, data[field])

        part.update_time = datetime.now()

        try:
            db.session.commit()
            Log.add_log(g.user_id, g.username, 'update', 'spare_part',
                       f'更新备件: {part.part_name}')
            SparePartService.check_and_create_low_stock_alert(part)
            return Response.success(part.to_dict(), '更新成功')
        except Exception as e:
            db.session.rollback()
            return Response.error(f'更新失败: {str(e)}')

    @staticmethod
    def delete_part(part_id):
        """删除备件"""
        part = SparePart.get_by_id(part_id)
        if not part:
            return Response.not_found('备件不存在')

        try:
            part.delete()
            Log.add_log(g.user_id, g.username, 'delete', 'spare_part',
                       f'删除备件: {part.part_name}')
            return Response.success(None, '删除成功')
        except Exception as e:
            db.session.rollback()
            return Response.error(f'删除失败: {str(e)}')

    @staticmethod
    def check_and_create_low_stock_alert(part):
        """检查并创建低库存告警"""
        if part.current_stock <= part.safety_stock:
            existing_alert = AlertRecord.query.filter(
                AlertRecord.alert_type == 'spare_low_stock',
                AlertRecord.equipment_id == part.id,
                AlertRecord.status == 'active'
            ).first()

            if not existing_alert:
                now = datetime.now()
                alert_code = f"ALERT-SPARE-{now.strftime('%Y%m%d%H%M%S')}"
                alert = AlertRecord(
                    alert_code=alert_code,
                    alert_type='spare_low_stock',
                    equipment_id=part.id,
                    severity='warning',
                    message=f'备件【{part.part_name}】库存不足，当前库存: {part.current_stock}，安全库存: {part.safety_stock}',
                    value=part.current_stock,
                    threshold=part.safety_stock,
                    status='active'
                )
                db.session.add(alert)
                db.session.commit()
                return alert
        return None

    @staticmethod
    def check_all_low_stock():
        """检查所有低库存备件并生成告警"""
        low_stock_parts = SparePart.query.filter(
            SparePart.status == 1,
            SparePart.current_stock <= SparePart.safety_stock
        ).all()

        alerts_created = []
        for part in low_stock_parts:
            alert = SparePartService.check_and_create_low_stock_alert(part)
            if alert:
                alerts_created.append(alert.to_dict())

        return Response.success({
            'low_stock_count': len(low_stock_parts),
            'alerts_created': alerts_created
        })

    @staticmethod
    def get_equipment_types():
        """获取所有设备类型（用于筛选）"""
        types = db.session.query(SparePart.equipment_type).filter(
            SparePart.status == 1,
            SparePart.equipment_type.isnot(None)
        ).distinct().all()
        type_list = [t[0] for t in types if t[0]]
        return Response.success(type_list)


class SpareInboundService:
    """备件入库服务类"""

    @staticmethod
    def get_inbounds(page=1, size=10, part_id=None, source_type=None, start_date=None, end_date=None):
        """获取入库列表"""
        query = SpareInbound.query.filter(SpareInbound.status == 1)

        if part_id:
            query = query.filter(SpareInbound.spare_part_id == part_id)
        if source_type:
            query = query.filter(SpareInbound.source_type == source_type)
        if start_date:
            query = query.filter(SpareInbound.inbound_time >= start_date)
        if end_date:
            query = query.filter(SpareInbound.inbound_time <= end_date)

        pagination = query.order_by(SpareInbound.create_time.desc()).paginate(
            page=page, per_page=size, error_out=False
        )

        items = [item.to_dict() for item in pagination.items]
        return Response.paginate(items, pagination.total, page, size)

    @staticmethod
    def create_inbound(data):
        """创建入库单"""
        validation = Validator.validate_form(data, {
            'spare_part_id': ['required'],
            'quantity': ['required']
        })

        if not validation['valid']:
            return Response.bad_request(list(validation['errors'].values())[0])

        part = SparePart.get_by_id(data['spare_part_id'])
        if not part:
            return Response.not_found('备件不存在')

        now = datetime.now()
        inbound_code = f"IN-{now.strftime('%Y%m%d%H%M%S')}-{SpareInbound.query.count() + 1}"

        quantity = int(data['quantity'])
        unit_price = float(data.get('unit_price', part.unit_price or 0))
        total_price = quantity * unit_price

        inbound = SpareInbound(
            inbound_code=inbound_code,
            spare_part_id=data['spare_part_id'],
            source_type=data.get('source_type', 'purchase'),
            batch_no=data.get('batch_no'),
            quantity=quantity,
            unit_price=unit_price,
            total_price=total_price,
            operator=g.username if hasattr(g, 'username') else data.get('operator'),
            inbound_time=data.get('inbound_time', now),
            remark=data.get('remark')
        )

        try:
            part.current_stock += quantity
            part.update_time = now
            db.session.add(inbound)
            db.session.commit()

            Log.add_log(g.user_id, g.username, 'create', 'spare_inbound',
                       f'备件入库: {part.part_name} +{quantity}')

            SparePartService.check_and_create_low_stock_alert(part)

            return Response.created(inbound.to_dict(), '入库成功')
        except Exception as e:
            db.session.rollback()
            return Response.error(f'入库失败: {str(e)}')

    @staticmethod
    def delete_inbound(inbound_id):
        """删除入库单"""
        inbound = SpareInbound.get_by_id(inbound_id)
        if not inbound:
            return Response.not_found('入库单不存在')

        part = SparePart.get_by_id(inbound.spare_part_id)
        if part:
            if part.current_stock < inbound.quantity:
                return Response.error('库存不足，无法撤销入库')
            part.current_stock -= inbound.quantity
            part.update_time = datetime.now()

        try:
            inbound.delete()
            db.session.commit()
            Log.add_log(g.user_id, g.username, 'delete', 'spare_inbound',
                       f'撤销入库: {inbound.inbound_code}')
            return Response.success(None, '删除成功')
        except Exception as e:
            db.session.rollback()
            return Response.error(f'删除失败: {str(e)}')


class SpareOutboundService:
    """备件领用服务类"""

    @staticmethod
    def get_outbounds(page=1, size=10, part_id=None, work_order_id=None, is_returned=None, start_date=None, end_date=None):
        """获取领用列表"""
        query = SpareOutbound.query.filter(SpareOutbound.status == 1)

        if part_id:
            query = query.filter(SpareOutbound.spare_part_id == part_id)
        if work_order_id:
            query = query.filter(SpareOutbound.work_order_id == work_order_id)
        if is_returned is not None:
            query = query.filter(SpareOutbound.is_returned == is_returned)
        if start_date:
            query = query.filter(SpareOutbound.outbound_time >= start_date)
        if end_date:
            query = query.filter(SpareOutbound.outbound_time <= end_date)

        pagination = query.order_by(SpareOutbound.create_time.desc()).paginate(
            page=page, per_page=size, error_out=False
        )

        items = [item.to_dict() for item in pagination.items]
        return Response.paginate(items, pagination.total, page, size)

    @staticmethod
    def create_outbound(data):
        """创建领用单"""
        validation = Validator.validate_form(data, {
            'spare_part_id': ['required'],
            'quantity': ['required'],
            'receiver': ['required']
        })

        if not validation['valid']:
            return Response.bad_request(list(validation['errors'].values())[0])

        part = SparePart.get_by_id(data['spare_part_id'])
        if not part:
            return Response.not_found('备件不存在')

        quantity = int(data['quantity'])
        if part.current_stock < quantity:
            return Response.error(f'库存不足，当前库存: {part.current_stock}')

        work_order = None
        work_order_id = data.get('work_order_id')
        if work_order_id:
            work_order = MaintenanceWorkOrder.get_by_id(work_order_id)
            if not work_order:
                return Response.not_found('维修工单不存在')

        now = datetime.now()
        outbound_code = f"OUT-{now.strftime('%Y%m%d%H%M%S')}-{SpareOutbound.query.count() + 1}"

        outbound = SpareOutbound(
            outbound_code=outbound_code,
            spare_part_id=data['spare_part_id'],
            work_order_id=work_order_id,
            reason=data.get('reason'),
            receiver=data['receiver'],
            quantity=quantity,
            outbound_time=data.get('outbound_time', now),
            is_returned=0,
            operator=g.username if hasattr(g, 'username') else data.get('operator'),
            remark=data.get('remark')
        )

        try:
            part.current_stock -= quantity
            part.update_time = now
            db.session.add(outbound)

            if work_order:
                SpareOutboundService._update_work_order_materials(work_order, part, quantity, 'add')

            db.session.commit()

            Log.add_log(g.user_id, g.username, 'create', 'spare_outbound',
                       f'备件领用: {part.part_name} -{quantity}')

            SparePartService.check_and_create_low_stock_alert(part)

            return Response.created(outbound.to_dict(), '领用成功')
        except Exception as e:
            db.session.rollback()
            return Response.error(f'领用失败: {str(e)}')

    @staticmethod
    def _update_work_order_materials(work_order, part, quantity, operation='add'):
        """更新工单耗材明细"""
        try:
            materials = json.loads(work_order.materials) if work_order.materials else []
        except Exception:
            materials = []

        unit_price = float(part.unit_price or 0)
        item_total = unit_price * quantity

        if operation == 'add':
            existing = next((m for m in materials if m.get('spare_part_id') == part.id), None)
            if existing:
                existing['quantity'] = existing.get('quantity', 0) + quantity
                existing['total_price'] = existing.get('quantity', 0) * unit_price
            else:
                materials.append({
                    'spare_part_id': part.id,
                    'part_code': part.part_code,
                    'part_name': part.part_name,
                    'specification': part.specification,
                    'unit': part.unit,
                    'quantity': quantity,
                    'unit_price': unit_price,
                    'total_price': item_total
                })
            work_order.materials_cost = (work_order.materials_cost or 0) + item_total
        elif operation == 'remove':
            materials = [m for m in materials if m.get('spare_part_id') != part.id]
            work_order.materials_cost = max(0, (work_order.materials_cost or 0) - item_total)

        work_order.materials = json.dumps(materials, ensure_ascii=False)
        work_order.total_cost = (work_order.materials_cost or 0) + (work_order.labor_cost or 0)
        work_order.update_time = datetime.now()

    @staticmethod
    def return_outbound(outbound_id):
        """归还备件"""
        outbound = SpareOutbound.get_by_id(outbound_id)
        if not outbound:
            return Response.not_found('领用单不存在')

        if outbound.is_returned:
            return Response.error('该备件已归还')

        part = SparePart.get_by_id(outbound.spare_part_id)
        if not part:
            return Response.not_found('备件不存在')

        now = datetime.now()

        try:
            outbound.is_returned = 1
            outbound.return_time = now
            part.current_stock += outbound.quantity
            part.update_time = now

            if outbound.work_order_id:
                work_order = MaintenanceWorkOrder.get_by_id(outbound.work_order_id)
                if work_order:
                    SpareOutboundService._update_work_order_materials(
                        work_order, part, outbound.quantity, 'remove'
                    )

            db.session.commit()
            Log.add_log(g.user_id, g.username, 'update', 'spare_outbound',
                       f'备件归还: {part.part_name} +{outbound.quantity}')
            return Response.success(outbound.to_dict(), '归还成功')
        except Exception as e:
            db.session.rollback()
            return Response.error(f'归还失败: {str(e)}')

    @staticmethod
    def delete_outbound(outbound_id):
        """删除领用单"""
        outbound = SpareOutbound.get_by_id(outbound_id)
        if not outbound:
            return Response.not_found('领用单不存在')

        if not outbound.is_returned:
            part = SparePart.get_by_id(outbound.spare_part_id)
            if part:
                part.current_stock += outbound.quantity
                part.update_time = datetime.now()

            if outbound.work_order_id:
                work_order = MaintenanceWorkOrder.get_by_id(outbound.work_order_id)
                if work_order:
                    try:
                        part = SparePart.get_by_id(outbound.spare_part_id)
                        if part:
                            SpareOutboundService._update_work_order_materials(
                                work_order, part, outbound.quantity, 'remove'
                            )
                    except Exception:
                        pass

        try:
            outbound.delete()
            db.session.commit()
            Log.add_log(g.user_id, g.username, 'delete', 'spare_outbound',
                       f'删除领用: {outbound.outbound_code}')
            return Response.success(None, '删除成功')
        except Exception as e:
            db.session.rollback()
            return Response.error(f'删除失败: {str(e)}')


class SpareInventoryService:
    """盘点服务类"""

    @staticmethod
    def get_inventories(page=1, size=10, part_id=None, inventory_month=None, has_difference=False):
        """获取盘点列表"""
        query = SpareInventory.query.filter(SpareInventory.status == 1)

        if part_id:
            query = query.filter(SpareInventory.spare_part_id == part_id)
        if inventory_month:
            query = query.filter(SpareInventory.inventory_month == inventory_month)
        if has_difference:
            query = query.filter(SpareInventory.difference != 0)

        pagination = query.order_by(SpareInventory.create_time.desc()).paginate(
            page=page, per_page=size, error_out=False
        )

        items = [item.to_dict() for item in pagination.items]
        return Response.paginate(items, pagination.total, page, size)

    @staticmethod
    def create_inventory(data):
        """创建盘点单"""
        validation = Validator.validate_form(data, {
            'spare_part_id': ['required'],
            'inventory_month': ['required'],
            'actual_stock': ['required']
        })

        if not validation['valid']:
            return Response.bad_request(list(validation['errors'].values())[0])

        part = SparePart.get_by_id(data['spare_part_id'])
        if not part:
            return Response.not_found('备件不存在')

        book_stock = int(data.get('book_stock', part.current_stock))
        actual_stock = int(data['actual_stock'])
        difference = actual_stock - book_stock

        existing = SpareInventory.query.filter(
            SpareInventory.spare_part_id == data['spare_part_id'],
            SpareInventory.inventory_month == data['inventory_month'],
            SpareInventory.status == 1
        ).first()

        if existing:
            return Response.error('该备件本月已盘点', 409)

        now = datetime.now()
        inventory_code = f"INV-{data['inventory_month'].replace('-', '')}-{SpareInventory.query.count() + 1}"

        inventory = SpareInventory(
            inventory_code=inventory_code,
            spare_part_id=data['spare_part_id'],
            inventory_month=data['inventory_month'],
            book_stock=book_stock,
            actual_stock=actual_stock,
            difference=difference,
            difference_reason=data.get('difference_reason'),
            operator=g.username if hasattr(g, 'username') else data.get('operator'),
            inventory_time=data.get('inventory_time', now),
            remark=data.get('remark')
        )

        try:
            db.session.add(inventory)
            db.session.commit()
            Log.add_log(g.user_id, g.username, 'create', 'spare_inventory',
                       f'盘点: {part.part_name} 差异:{difference}')
            return Response.created(inventory.to_dict(), '盘点成功')
        except Exception as e:
            db.session.rollback()
            return Response.error(f'盘点失败: {str(e)}')

    @staticmethod
    def batch_create_inventory(data):
        """批量创建盘点单"""
        inventory_month = data.get('inventory_month')
        operator = g.username if hasattr(g, 'username') else data.get('operator')

        if not inventory_month:
            return Response.bad_request('请指定盘点月份')

        parts = SparePart.query.filter_by(status=1).all()
        created_count = 0

        try:
            for part in parts:
                existing = SpareInventory.query.filter(
                    SpareInventory.spare_part_id == part.id,
                    SpareInventory.inventory_month == inventory_month,
                    SpareInventory.status == 1
                ).first()

                if existing:
                    continue

                now = datetime.now()
                inventory_code = f"INV-{inventory_month.replace('-', '')}-{SpareInventory.query.count() + created_count + 1}"

                inventory = SpareInventory(
                    inventory_code=inventory_code,
                    spare_part_id=part.id,
                    inventory_month=inventory_month,
                    book_stock=part.current_stock,
                    actual_stock=part.current_stock,
                    difference=0,
                    operator=operator,
                    inventory_time=now
                )
                db.session.add(inventory)
                created_count += 1

            db.session.commit()
            Log.add_log(g.user_id, g.username, 'batch_create', 'spare_inventory',
                       f'批量盘点: 创建{created_count}条盘点记录')
            return Response.success({'created_count': created_count}, '批量盘点成功')
        except Exception as e:
            db.session.rollback()
            return Response.error(f'批量盘点失败: {str(e)}')

    @staticmethod
    def update_inventory(inventory_id, data):
        """更新盘点单"""
        inventory = SpareInventory.get_by_id(inventory_id)
        if not inventory:
            return Response.not_found('盘点单不存在')

        if 'actual_stock' in data:
            inventory.actual_stock = int(data['actual_stock'])
            inventory.difference = inventory.actual_stock - inventory.book_stock

        if 'difference_reason' in data:
            inventory.difference_reason = data['difference_reason']

        inventory.update_time = datetime.now()

        try:
            db.session.commit()
            return Response.success(inventory.to_dict(), '更新成功')
        except Exception as e:
            db.session.rollback()
            return Response.error(f'更新失败: {str(e)}')

    @staticmethod
    def delete_inventory(inventory_id):
        """删除盘点单"""
        inventory = SpareInventory.get_by_id(inventory_id)
        if not inventory:
            return Response.not_found('盘点单不存在')

        try:
            inventory.delete()
            return Response.success(None, '删除成功')
        except Exception as e:
            db.session.rollback()
            return Response.error(f'删除失败: {str(e)}')


class SpareStatisticsService:
    """备件统计服务类"""

    @staticmethod
    def get_turnover_rate(start_date=None, end_date=None, top_n=10):
        """
        计算周转率: 周转率 = 出库量 / 平均库存
        平均库存 = (期初库存 + 期末库存) / 2
        """
        now = datetime.now()
        if not end_date:
            end_date = now
        if not start_date:
            start_date = now - timedelta(days=30)

        parts = SparePart.query.filter_by(status=1).all()
        turnover_rates = []

        for part in parts:
            outbound_total = db.session.query(
                db.func.sum(SpareOutbound.quantity)
            ).filter(
                SpareOutbound.spare_part_id == part.id,
                SpareOutbound.status == 1,
                SpareOutbound.is_returned == 0,
                SpareOutbound.outbound_time >= start_date,
                SpareOutbound.outbound_time <= end_date
            ).scalar() or 0

            inbound_total = db.session.query(
                db.func.sum(SpareInbound.quantity)
            ).filter(
                SpareInbound.spare_part_id == part.id,
                SpareInbound.status == 1,
                SpareInbound.inbound_time >= start_date,
                SpareInbound.inbound_time <= end_date
            ).scalar() or 0

            end_stock = part.current_stock
            start_stock = end_stock + outbound_total - inbound_total
            avg_stock = (start_stock + end_stock) / 2 if (start_stock + end_stock) > 0 else 1
            turnover_rate = round(outbound_total / avg_stock, 4) if avg_stock > 0 else 0

            turnover_rates.append({
                'spare_part_id': part.id,
                'part_code': part.part_code,
                'part_name': part.part_name,
                'specification': part.specification,
                'unit': part.unit,
                'outbound_quantity': outbound_total,
                'inbound_quantity': inbound_total,
                'start_stock': start_stock,
                'end_stock': end_stock,
                'avg_stock': round(avg_stock, 2),
                'turnover_rate': turnover_rate
            })

        turnover_rates.sort(key=lambda x: x['turnover_rate'], reverse=True)
        top_rates = turnover_rates[:top_n]

        return Response.success({
            'items': top_rates,
            'total': len(turnover_rates),
            'start_date': start_date.strftime('%Y-%m-%d'),
            'end_date': end_date.strftime('%Y-%m-%d')
        })

    @staticmethod
    def get_dashboard():
        """获取备件概览统计"""
        total_parts = SparePart.query.filter_by(status=1).count()
        low_stock_parts = SparePart.query.filter(
            SparePart.status == 1,
            SparePart.current_stock <= SparePart.safety_stock
        ).count()

        now = datetime.now()
        month_start = now.replace(day=1, hour=0, minute=0, second=0)

        this_month_inbound = db.session.query(
            db.func.sum(SpareInbound.quantity)
        ).filter(
            SpareInbound.status == 1,
            SpareInbound.inbound_time >= month_start
        ).scalar() or 0

        this_month_outbound = db.session.query(
            db.func.sum(SpareOutbound.quantity)
        ).filter(
            SpareOutbound.status == 1,
            SpareOutbound.is_returned == 0,
            SpareOutbound.outbound_time >= month_start
        ).scalar() or 0

        total_value = db.session.query(
            db.func.sum(SparePart.current_stock * SparePart.unit_price)
        ).filter(SparePart.status == 1).scalar() or 0

        return Response.success({
            'total_parts': total_parts,
            'low_stock_parts': low_stock_parts,
            'this_month_inbound': this_month_inbound,
            'this_month_outbound': this_month_outbound,
            'total_inventory_value': float(total_value)
        })
