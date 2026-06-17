"""
成本核算服务
"""
from flask import g
from datetime import datetime, date, timedelta
from database.db import db
from models.cost import CostElement, CostRecord, CostSummary
from models.production import ProductionTask, ProductionLine, ProductionRecord, Equipment
from models.log import Log
from utils.response import Response
from utils.validator import Validator
import random


class CostElementService:
    """成本要素字典服务"""

    @staticmethod
    def get_elements(page=1, size=10, element_type=None, keyword=None):
        """获取成本要素列表"""
        query = CostElement.query.filter(CostElement.status == 1)

        if element_type:
            query = query.filter(CostElement.element_type == element_type)
        if keyword:
            query = query.filter(
                db.or_(
                    CostElement.element_name.like(f'%{keyword}%'),
                    CostElement.element_code.like(f'%{keyword}%')
                )
            )

        pagination = query.order_by(CostElement.sort_order.asc(), CostElement.create_time.desc()).paginate(
            page=page, per_page=size, error_out=False
        )

        return Response.paginate(
            [e.to_dict() for e in pagination.items],
            pagination.total, page, size
        )

    @staticmethod
    def get_all_elements():
        """获取所有可用成本要素（用于下拉选择）"""
        elements = CostElement.query.filter(
            CostElement.status == 1
        ).order_by(CostElement.sort_order.asc(), CostElement.element_name.asc()).all()
        return Response.success([e.to_dict() for e in elements])

    @staticmethod
    def get_element_by_id(element_id):
        """获取成本要素详情"""
        element = CostElement.get_by_id(element_id)
        if not element:
            return Response.not_found('成本要素不存在')
        return Response.success(element.to_dict())

    @staticmethod
    def create_element(data):
        """创建成本要素"""
        validation = Validator.validate_form(data, {
            'element_code': ['required'],
            'element_name': ['required'],
            'element_type': ['required']
        })

        if not validation['valid']:
            return Response.bad_request(list(validation['errors'].values())[0])

        if CostElement.query.filter_by(element_code=data['element_code'], status=1).first():
            return Response.error('要素编码已存在', 409)

        element = CostElement(
            element_code=data['element_code'],
            element_name=data['element_name'],
            element_type=data['element_type'],
            unit=data.get('unit'),
            price=data.get('price', 0),
            description=data.get('description'),
            sort_order=data.get('sort_order', 0)
        )

        try:
            element.save()
            Log.add_log(g.user_id, g.username, 'create', 'cost_element',
                       f'创建成本要素: {element.element_name}')
            return Response.created({'id': element.id}, '创建成功')
        except Exception as e:
            db.session.rollback()
            return Response.error(f'创建失败: {str(e)}')

    @staticmethod
    def update_element(element_id, data):
        """更新成本要素"""
        element = CostElement.get_by_id(element_id)
        if not element:
            return Response.not_found('成本要素不存在')

        if 'element_code' in data and data['element_code'] != element.element_code:
            if CostElement.query.filter(
                CostElement.element_code == data['element_code'],
                CostElement.status == 1,
                CostElement.id != element_id
            ).first():
                return Response.error('要素编码已存在', 409)

        allowed = ['element_code', 'element_name', 'element_type', 'unit', 'price', 'description', 'sort_order']
        update_data = {k: v for k, v in data.items() if k in allowed}

        element.update(**update_data)
        Log.add_log(g.user_id, g.username, 'update', 'cost_element',
                   f'更新成本要素: {element.element_name}')

        return Response.success(element.to_dict(), '更新成功')

    @staticmethod
    def delete_element(element_id):
        """删除成本要素"""
        element = CostElement.get_by_id(element_id)
        if not element:
            return Response.not_found('成本要素不存在')

        if CostRecord.query.filter_by(element_id=element_id, status=1).first():
            return Response.error('该要素已有成本登记记录，无法删除', 400)

        element.delete()
        Log.add_log(g.user_id, g.username, 'delete', 'cost_element',
                   f'删除成本要素: {element.element_name}')

        return Response.success(message='删除成功')

    @staticmethod
    def init_default_elements():
        """初始化默认成本要素"""
        default_elements = [
            {'element_code': 'MAT001', 'element_name': '钢材', 'element_type': 'material', 'unit': 'kg', 'price': 5.5, 'sort_order': 1},
            {'element_code': 'MAT002', 'element_name': '塑料颗粒', 'element_type': 'material', 'unit': 'kg', 'price': 12.0, 'sort_order': 2},
            {'element_code': 'MAT003', 'element_name': '电子元件', 'element_type': 'material', 'unit': '个', 'price': 8.5, 'sort_order': 3},
            {'element_code': 'MAT004', 'element_name': '润滑油', 'element_type': 'material', 'unit': 'L', 'price': 45.0, 'sort_order': 4},
            {'element_code': 'LAB001', 'element_name': '操作工人工时', 'element_type': 'labor', 'unit': '小时', 'price': 35.0, 'sort_order': 10},
            {'element_code': 'LAB002', 'element_name': '技术员工时', 'element_type': 'labor', 'unit': '小时', 'price': 60.0, 'sort_order': 11},
            {'element_code': 'LAB003', 'element_name': '管理人员工时', 'element_type': 'labor', 'unit': '小时', 'price': 80.0, 'sort_order': 12},
            {'element_code': 'DEP001', 'element_name': '设备折旧-机器人', 'element_type': 'depreciation', 'unit': '小时', 'price': 25.0, 'sort_order': 20},
            {'element_code': 'DEP002', 'element_name': '设备折旧-包装机', 'element_type': 'depreciation', 'unit': '小时', 'price': 15.0, 'sort_order': 21},
            {'element_code': 'DEP003', 'element_name': '设备折旧-检测仪', 'element_type': 'depreciation', 'unit': '小时', 'price': 10.0, 'sort_order': 22},
            {'element_code': 'ENG001', 'element_name': '电力消耗', 'element_type': 'energy', 'unit': 'kWh', 'price': 0.85, 'sort_order': 30},
            {'element_code': 'ENG002', 'element_name': '水资源消耗', 'element_type': 'energy', 'unit': 'm³', 'price': 5.2, 'sort_order': 31},
            {'element_code': 'ENG003', 'element_name': '天然气消耗', 'element_type': 'energy', 'unit': 'm³', 'price': 3.5, 'sort_order': 32},
            {'element_code': 'OTH001', 'element_name': '包装材料', 'element_type': 'other', 'unit': '套', 'price': 2.5, 'sort_order': 40},
            {'element_code': 'OTH002', 'element_name': '运输费用', 'element_type': 'other', 'unit': '次', 'price': 200.0, 'sort_order': 41},
        ]

        created_count = 0
        for elem_data in default_elements:
            if not CostElement.query.filter_by(element_code=elem_data['element_code'], status=1).first():
                elem = CostElement(**elem_data)
                elem.save()
                created_count += 1

        return Response.success({'created': created_count}, '默认成本要素初始化完成')


class CostRecordService:
    """成本登记服务"""

    @staticmethod
    def generate_record_code():
        """生成登记编号"""
        today = datetime.now().strftime('%Y%m%d')
        count = CostRecord.query.filter(
            db.func.date(CostRecord.create_time) == date.today()
        ).count() + 1
        return f'CR{today}{count:04d}'

    @staticmethod
    def get_records(page=1, size=10, task_id=None, element_id=None, element_type=None, start_date=None, end_date=None):
        """获取成本登记列表"""
        query = CostRecord.query.filter(CostRecord.status == 1)

        if task_id:
            query = query.filter(CostRecord.task_id == task_id)
        if element_id:
            query = query.filter(CostRecord.element_id == element_id)
        if element_type:
            query = query.join(CostElement).filter(CostElement.element_type == element_type)
        if start_date:
            query = query.filter(CostRecord.record_date >= start_date)
        if end_date:
            query = query.filter(CostRecord.record_date <= end_date)

        pagination = query.order_by(CostRecord.record_date.desc(), CostRecord.create_time.desc()).paginate(
            page=page, per_page=size, error_out=False
        )

        return Response.paginate(
            [r.to_dict() for r in pagination.items],
            pagination.total, page, size
        )

    @staticmethod
    def get_record_by_id(record_id):
        """获取成本登记详情"""
        record = CostRecord.get_by_id(record_id)
        if not record:
            return Response.not_found('成本登记不存在')
        return Response.success(record.to_dict())

    @staticmethod
    def create_record(data):
        """创建成本登记"""
        validation = Validator.validate_form(data, {
            'task_id': ['required'],
            'element_id': ['required'],
            'amount': ['required']
        })

        if not validation['valid']:
            return Response.bad_request(list(validation['errors'].values())[0])

        task = ProductionTask.get_by_id(data['task_id'])
        if not task:
            return Response.not_found('生产任务不存在')

        element = CostElement.get_by_id(data['element_id'])
        if not element:
            return Response.not_found('成本要素不存在')

        quantity = data.get('quantity', 0)
        unit_price = data.get('unit_price', element.price)
        amount = data.get('amount', 0)

        if amount == 0 and quantity > 0 and unit_price > 0:
            amount = quantity * unit_price

        record = CostRecord(
            record_code=CostRecordService.generate_record_code(),
            task_id=data['task_id'],
            element_id=data['element_id'],
            quantity=quantity,
            unit_price=unit_price,
            amount=amount,
            remark=data.get('remark'),
            register_by=g.username,
            record_date=data.get('record_date') or date.today(),
            source=data.get('source', 'manual')
        )

        try:
            record.save()
            Log.add_log(g.user_id, g.username, 'create', 'cost_record',
                       f'创建成本登记: {record.record_code} - {element.element_name} - {amount}元')

            CostRecordService.update_task_summary(data['task_id'])

            return Response.created({'id': record.id}, '登记成功')
        except Exception as e:
            db.session.rollback()
            return Response.error(f'登记失败: {str(e)}')

    @staticmethod
    def batch_create_records(data):
        """批量创建成本登记"""
        task_id = data.get('task_id')
        records = data.get('records', [])

        if not task_id:
            return Response.bad_request('请指定生产任务')
        if not records or len(records) == 0:
            return Response.bad_request('请至少录入一条成本记录')

        task = ProductionTask.get_by_id(task_id)
        if not task:
            return Response.not_found('生产任务不存在')

        created_ids = []
        try:
            for item in records:
                element = CostElement.get_by_id(item.get('element_id'))
                if not element:
                    continue

                quantity = item.get('quantity', 0)
                unit_price = item.get('unit_price', element.price)
                amount = item.get('amount', 0)

                if amount == 0 and quantity > 0 and unit_price > 0:
                    amount = quantity * unit_price

                record = CostRecord(
                    record_code=CostRecordService.generate_record_code(),
                    task_id=task_id,
                    element_id=item['element_id'],
                    quantity=quantity,
                    unit_price=unit_price,
                    amount=amount,
                    remark=item.get('remark'),
                    register_by=g.username,
                    record_date=item.get('record_date') or date.today(),
                    source=item.get('source', 'manual')
                )
                record.save()
                created_ids.append(record.id)

            CostRecordService.update_task_summary(task_id)
            Log.add_log(g.user_id, g.username, 'batch_create', 'cost_record',
                       f'批量创建成本登记: {len(created_ids)}条')

            return Response.created({'ids': created_ids}, '批量登记成功')
        except Exception as e:
            db.session.rollback()
            return Response.error(f'批量登记失败: {str(e)}')

    @staticmethod
    def update_record(record_id, data):
        """更新成本登记"""
        record = CostRecord.get_by_id(record_id)
        if not record:
            return Response.not_found('成本登记不存在')

        if record.source == 'auto':
            return Response.error('自动折算的记录不允许修改', 400)

        allowed = ['element_id', 'quantity', 'unit_price', 'amount', 'remark', 'record_date']
        update_data = {k: v for k, v in data.items() if k in allowed}

        if 'element_id' in update_data:
            element = CostElement.get_by_id(update_data['element_id'])
            if not element:
                return Response.not_found('成本要素不存在')

        if 'quantity' in update_data or 'unit_price' in update_data:
            quantity = update_data.get('quantity', record.quantity)
            unit_price = update_data.get('unit_price', record.unit_price)
            update_data['amount'] = quantity * unit_price

        old_amount = record.amount
        record.update(**update_data)

        Log.add_log(g.user_id, g.username, 'update', 'cost_record',
                   f'更新成本登记: {record.record_code} - 金额{old_amount}->{record.amount}')

        CostRecordService.update_task_summary(record.task_id)

        return Response.success(record.to_dict(), '更新成功')

    @staticmethod
    def delete_record(record_id):
        """删除成本登记"""
        record = CostRecord.get_by_id(record_id)
        if not record:
            return Response.not_found('成本登记不存在')

        if record.source == 'auto':
            return Response.error('自动折算的记录不允许删除', 400)

        task_id = record.task_id
        record.delete()

        Log.add_log(g.user_id, g.username, 'delete', 'cost_record',
                   f'删除成本登记: {record.record_code}')

        CostRecordService.update_task_summary(task_id)

        return Response.success(message='删除成功')

    @staticmethod
    def update_task_summary(task_id):
        """更新任务成本汇总"""
        records = CostRecord.query.filter_by(task_id=task_id, status=1).all()

        totals = {
            'material': 0, 'labor': 0, 'depreciation': 0, 'energy': 0, 'other': 0
        }
        for record in records:
            if record.element:
                totals[record.element.element_type] += float(record.amount)

        total_amount = sum(totals.values())

        task = ProductionTask.get_by_id(task_id)
        unit_cost = total_amount / task.quantity if task and task.quantity and task.quantity > 0 else 0

        summary = CostSummary.query.filter_by(task_id=task_id).first()
        if not summary:
            summary = CostSummary(task_id=task_id)

        summary.total_material = totals['material']
        summary.total_labor = totals['labor']
        summary.total_depreciation = totals['depreciation']
        summary.total_energy = totals['energy']
        summary.total_other = totals['other']
        summary.total_amount = total_amount
        summary.unit_cost = unit_cost

        try:
            summary.save()
        except Exception as e:
            db.session.rollback()

    @staticmethod
    def calculate_task_cost(task_id):
        """任务完成时自动初算成本 - 从关联模块拉数据折算"""
        task = ProductionTask.get_by_id(task_id)
        if not task:
            return Response.not_found('生产任务不存在')

        auto_records = []
        missing_elements = []

        duration_hours = 0
        if task.actual_start_time and task.actual_end_time:
            duration_hours = (task.actual_end_time - task.actual_start_time).total_seconds() / 3600

        production_records = ProductionRecord.query.filter_by(task_id=task_id).all()
        total_duration_seconds = sum(r.duration or 0 for r in production_records)
        total_duration_hours = total_duration_seconds / 3600 if total_duration_seconds > 0 else duration_hours

        equipment_ids = set(r.equipment_id for r in production_records)
        equipments = Equipment.query.filter(Equipment.id.in_(equipment_ids)).all() if equipment_ids else []

        material_element = CostElement.query.filter_by(element_code='MAT001', status=1).first()
        if material_element and task.completed_quantity:
            quantity = task.completed_quantity * 2.5
            amount = quantity * float(material_element.price)
            auto_records.append({
                'element_id': material_element.id,
                'quantity': quantity,
                'unit_price': float(material_element.price),
                'amount': amount,
                'remark': f'自动折算: 生产{task.completed_quantity}件产品耗用原材料',
                'source': 'auto'
            })
        else:
            missing_elements.append('原材料耗用(未配置或无产量数据)')

        labor_element = CostElement.query.filter_by(element_code='LAB001', status=1).first()
        if labor_element and total_duration_hours > 0:
            worker_count = 3
            quantity = total_duration_hours * worker_count
            amount = quantity * float(labor_element.price)
            auto_records.append({
                'element_id': labor_element.id,
                'quantity': round(quantity, 2),
                'unit_price': float(labor_element.price),
                'amount': round(amount, 2),
                'remark': f'自动折算: {worker_count}名操作工*{total_duration_hours:.1f}小时',
                'source': 'auto'
            })
        else:
            missing_elements.append('人工工时(未配置或无工时数据)')

        if equipments:
            for equipment in equipments:
                if '机器人' in equipment.equipment_name:
                    dep_element = CostElement.query.filter_by(element_code='DEP001', status=1).first()
                elif '包装机' in equipment.equipment_name:
                    dep_element = CostElement.query.filter_by(element_code='DEP002', status=1).first()
                elif '检测仪' in equipment.equipment_name:
                    dep_element = CostElement.query.filter_by(element_code='DEP003', status=1).first()
                else:
                    dep_element = CostElement.query.filter_by(element_code='DEP002', status=1).first()

                if dep_element and total_duration_hours > 0:
                    eq_duration = total_duration_hours / len(equipments)
                    amount = eq_duration * float(dep_element.price)
                    auto_records.append({
                        'element_id': dep_element.id,
                        'quantity': round(eq_duration, 2),
                        'unit_price': float(dep_element.price),
                        'amount': round(amount, 2),
                        'remark': f'自动折算: {equipment.equipment_name}折旧*{eq_duration:.1f}小时',
                        'source': 'auto'
                    })

        energy_element = CostElement.query.filter_by(element_code='ENG001', status=1).first()
        if energy_element and total_duration_hours > 0:
            power_kw = 15
            quantity = total_duration_hours * power_kw * len(equipments) if equipments else total_duration_hours * 10
            amount = quantity * float(energy_element.price)
            auto_records.append({
                'element_id': energy_element.id,
                'quantity': round(quantity, 2),
                'unit_price': float(energy_element.price),
                'amount': round(amount, 2),
                'remark': f'自动折算: 电力消耗*{quantity:.1f}kWh',
                'source': 'auto'
            })
        else:
            missing_elements.append('能源消耗(未配置或无工时数据)')

        try:
            CostRecord.query.filter_by(task_id=task_id, source='auto').update({'status': 0})
            db.session.commit()

            created_ids = []
            for item in auto_records:
                record = CostRecord(
                    record_code=CostRecordService.generate_record_code(),
                    task_id=task_id,
                    element_id=item['element_id'],
                    quantity=item['quantity'],
                    unit_price=item['unit_price'],
                    amount=item['amount'],
                    remark=item['remark'],
                    register_by=g.username,
                    record_date=date.today(),
                    source='auto'
                )
                record.save()
                created_ids.append(record.id)

            CostRecordService.update_task_summary(task_id)

            summary = CostSummary.query.filter_by(task_id=task_id).first()
            if summary:
                summary.auto_calculated = True
                summary.missing_elements = ','.join(missing_elements) if missing_elements else None
                summary.save()

            Log.add_log(g.user_id, g.username, 'auto_calculate', 'cost_record',
                       f'任务{task.task_code}自动初算成本: {len(created_ids)}条记录')

            return Response.success({
                'created_count': len(created_ids),
                'missing_elements': missing_elements,
                'total_amount': summary.total_amount if summary else sum(r['amount'] for r in auto_records)
            }, '自动初算完成' + (', 请手工补录: ' + ','.join(missing_elements) if missing_elements else ''))
        except Exception as e:
            db.session.rollback()
            return Response.error(f'自动初算失败: {str(e)}')

    @staticmethod
    def get_task_cost(task_id):
        """获取任务成本详情（用于前端Tab显示）"""
        task = ProductionTask.get_by_id(task_id)
        if not task:
            return Response.not_found('生产任务不存在')

        records = CostRecord.query.filter_by(task_id=task_id, status=1).all()
        summary = CostSummary.query.filter_by(task_id=task_id).first()

        records_by_type = {
            'material': [], 'labor': [], 'depreciation': [], 'energy': [], 'other': []
        }
        for r in records:
            if r.element and r.element.element_type in records_by_type:
                records_by_type[r.element.element_type].append(r.to_dict())

        summary_dict = summary.to_dict() if summary else {
            'total_material': 0, 'total_labor': 0, 'total_depreciation': 0,
            'total_energy': 0, 'total_other': 0, 'total_amount': 0, 'unit_cost': 0,
            'auto_calculated': False, 'missing_elements': None
        }

        summary_dict['material_amount'] = summary_dict.get('total_material', 0)
        summary_dict['labor_amount'] = summary_dict.get('total_labor', 0)
        summary_dict['depreciation_amount'] = summary_dict.get('total_depreciation', 0)
        summary_dict['energy_amount'] = summary_dict.get('total_energy', 0)
        summary_dict['other_amount'] = summary_dict.get('total_other', 0)
        summary_dict['is_calculated'] = summary_dict.get('auto_calculated', False) or len(records) > 0
        summary_dict['is_auto'] = summary_dict.get('auto_calculated', False)

        missing = summary_dict.get('missing_elements')
        if missing:
            summary_dict['missing_elements'] = [x for x in missing.split(',') if x]
        else:
            summary_dict['missing_elements'] = []

        return Response.success({
            'task': task.to_dict(),
            'records': [r.to_dict() for r in records],
            'records_by_type': records_by_type,
            'summary': summary_dict
        })

    @staticmethod
    def init_sample_data():
        """初始化示例成本数据（用于测试和演示）"""
        if CostRecord.query.count() > 0:
            return Response.success({'created': 0}, '已有数据，跳过初始化')

        from services.production_service import TaskService

        sample_tasks = [
            {'task_code': 'T202501001', 'task_name': '智能手表A系列生产', 'product_name': '智能手表A1', 'quantity': 1000, 'priority': 8, 'status': 'completed'},
            {'task_code': 'T202501002', 'task_name': '智能手环B系列生产', 'product_name': '智能手环B2', 'quantity': 2000, 'priority': 6, 'status': 'completed'},
            {'task_code': 'T202501003', 'task_name': '蓝牙耳机C系列生产', 'product_name': '蓝牙耳机C3', 'quantity': 1500, 'priority': 7, 'status': 'completed'},
            {'task_code': 'T202502001', 'task_name': '智能手表A系列生产-2月', 'product_name': '智能手表A1', 'quantity': 1200, 'priority': 8, 'status': 'completed'},
            {'task_code': 'T202502002', 'task_name': '智能手环B系列生产-2月', 'product_name': '智能手环B2', 'quantity': 1800, 'priority': 5, 'status': 'completed'},
            {'task_code': 'T202503001', 'task_name': '智能手表A系列生产-3月', 'product_name': '智能手表A1', 'quantity': 1100, 'priority': 9, 'status': 'in_progress'},
        ]

        created_task_ids = []
        for task_data in sample_tasks:
            existing = ProductionTask.query.filter_by(task_code=task_data['task_code']).first()
            if not existing:
                task = ProductionTask(**task_data)
                task.completed_quantity = task_data['quantity'] if task_data['status'] == 'completed' else int(task_data['quantity'] * 0.6)
                if task_data['status'] == 'completed':
                    task.actual_start_time = datetime.now() - timedelta(days=5)
                    task.actual_end_time = datetime.now() - timedelta(days=1)
                task.save()
                created_task_ids.append(task.id)
            else:
                created_task_ids.append(existing.id)

        elements = CostElement.query.filter_by(status=1).all()
        element_map = {e.element_code: e for e in elements}

        created_records = 0
        today = date.today()
        for i, task_id in enumerate(created_task_ids[:5]):
            task = ProductionTask.get_by_id(task_id)
            month_offset = i // 2
            record_date = date(today.year, today.month - month_offset, 15) if today.month > month_offset else date(today.year - 1, 12 - month_offset, 15)

            sample_records = [
                {'element_code': 'MAT001', 'quantity': task.quantity * 2.5, 'source': 'auto', 'remark': '自动折算: 原材料耗用'},
                {'element_code': 'LAB001', 'quantity': 40 * 3, 'source': 'auto', 'remark': '自动折算: 操作工人时'},
                {'element_code': 'DEP001', 'quantity': 40, 'source': 'auto', 'remark': '自动折算: 设备折旧'},
                {'element_code': 'ENG001', 'quantity': 40 * 15, 'source': 'auto', 'remark': '自动折算: 电力消耗'},
                {'element_code': 'OTH001', 'quantity': task.quantity, 'source': 'manual', 'remark': '手工录入: 包装材料'},
            ]

            for sr in sample_records:
                element = element_map.get(sr['element_code'])
                if not element:
                    continue

                quantity = sr['quantity']
                unit_price = float(element.price)
                amount = quantity * unit_price

                record = CostRecord(
                    record_code=CostRecordService.generate_record_code(),
                    task_id=task_id,
                    element_id=element.id,
                    quantity=quantity,
                    unit_price=unit_price,
                    amount=amount,
                    remark=sr['remark'],
                    register_by='系统管理员',
                    record_date=record_date,
                    source=sr['source']
                )
                record.save()
                CostRecordService.update_task_summary(task_id)
                created_records += 1

        return Response.success({'created': created_records}, '示例数据初始化完成')


class CostReportService:
    """成本报表服务"""

    @staticmethod
    def get_multi_dimension_report(dimension='product', start_date=None, end_date=None):
        """
        多维度成本分析报表
        dimension: product(按产品)/line(按生产线)/month(按月份)/element(按要素)
        """
        query = CostRecord.query.filter(CostRecord.status == 1)

        if start_date:
            query = query.filter(CostRecord.record_date >= start_date)
        if end_date:
            query = query.filter(CostRecord.record_date <= end_date)

        records = query.all()

        result_data = {}
        type_totals = {'material': 0, 'labor': 0, 'depreciation': 0, 'energy': 0, 'other': 0}

        for record in records:
            if not record.element:
                continue

            elem_type = record.element.element_type
            amount = float(record.amount)
            type_totals[elem_type] += amount

            if dimension == 'product':
                key = record.task.product_name if record.task and record.task.product_name else '未指定产品'
            elif dimension == 'line':
                if record.task and record.task.line_id:
                    line = ProductionLine.query.get(record.task.line_id)
                    key = line.line_name if line else '未指定生产线'
                else:
                    key = '未指定生产线'
            elif dimension == 'month':
                key = record.record_date.strftime('%Y-%m') if record.record_date else '未知月份'
            elif dimension == 'element':
                key = record.element.element_name
            else:
                key = '其他'

            if key not in result_data:
                result_data[key] = {
                    'material': 0, 'labor': 0, 'depreciation': 0, 'energy': 0, 'other': 0, 'total': 0
                }
            result_data[key][elem_type] += amount
            result_data[key]['total'] += amount

        sorted_items = sorted(result_data.items(), key=lambda x: x[1]['total'], reverse=True)
        labels = [item[0] for item in sorted_items]
        datasets = {
            'material': [round(item[1]['material'], 2) for item in sorted_items],
            'labor': [round(item[1]['labor'], 2) for item in sorted_items],
            'depreciation': [round(item[1]['depreciation'], 2) for item in sorted_items],
            'energy': [round(item[1]['energy'], 2) for item in sorted_items],
            'other': [round(item[1]['other'], 2) for item in sorted_items],
            'total': [round(item[1]['total'], 2) for item in sorted_items]
        }

        pivot_data = []
        for label, values in sorted_items:
            pivot_data.append({
                'dimension': label,
                'material': round(values['material'], 2),
                'labor': round(values['labor'], 2),
                'depreciation': round(values['depreciation'], 2),
                'energy': round(values['energy'], 2),
                'other': round(values['other'], 2),
                'total': round(values['total'], 2)
            })

        return Response.success({
            'dimension': dimension,
            'labels': labels,
            'datasets': datasets,
            'type_totals': {k: round(v, 2) for k, v in type_totals.items()},
            'pivot_data': pivot_data
        })

    @staticmethod
    def get_monthly_summary(months=12):
        """按月汇总成本，含同比环比"""
        today = date.today()
        result = []

        for i in range(months):
            month_date = today - timedelta(days=i * 30)
            year = month_date.year
            month = month_date.month

            start_date = date(year, month, 1)
            if month == 12:
                end_date = date(year + 1, 1, 1)
            else:
                end_date = date(year, month + 1, 1)

            records = CostRecord.query.filter(
                CostRecord.status == 1,
                CostRecord.record_date >= start_date,
                CostRecord.record_date < end_date
            ).all()

            month_total = {
                'material': 0, 'labor': 0, 'depreciation': 0, 'energy': 0, 'other': 0, 'total': 0
            }
            for r in records:
                if r.element:
                    month_total[r.element.element_type] += float(r.amount)
            month_total['total'] = sum([month_total[k] for k in ['material', 'labor', 'depreciation', 'energy', 'other']])

            prev_month_start = start_date - timedelta(days=1)
            prev_month_start = date(prev_month_start.year, prev_month_start.month, 1)
            if prev_month_start.month == 12:
                prev_month_end = date(prev_month_start.year + 1, 1, 1)
            else:
                prev_month_end = date(prev_month_start.year, prev_month_start.month + 1, 1)

            prev_records = CostRecord.query.filter(
                CostRecord.status == 1,
                CostRecord.record_date >= prev_month_start,
                CostRecord.record_date < prev_month_end
            ).all()
            prev_total = sum(float(r.amount) for r in prev_records if r.element)

            same_month_last_year = date(year - 1, month, 1)
            if month == 12:
                same_month_end = date(year, 1, 1)
            else:
                same_month_end = date(year - 1, month + 1, 1)

            yoy_records = CostRecord.query.filter(
                CostRecord.status == 1,
                CostRecord.record_date >= same_month_last_year,
                CostRecord.record_date < same_month_end
            ).all()
            yoy_total = sum(float(r.amount) for r in yoy_records if r.element)

            mom = ((month_total['total'] - prev_total) / prev_total * 100) if prev_total > 0 else None
            yoy = ((month_total['total'] - yoy_total) / yoy_total * 100) if yoy_total > 0 else None

            result.append({
                'month': f'{year}-{month:02d}',
                'material': round(month_total['material'], 2),
                'labor': round(month_total['labor'], 2),
                'depreciation': round(month_total['depreciation'], 2),
                'energy': round(month_total['energy'], 2),
                'other': round(month_total['other'], 2),
                'total': round(month_total['total'], 2),
                'mom': round(mom, 2) if mom is not None else None,
                'yoy': round(yoy, 2) if yoy is not None else None
            })

        result.reverse()
        return Response.success(result)

    @staticmethod
    def get_dashboard_cost():
        """获取仪表盘成本数据（本月总成本和同比）"""
        today = date.today()
        this_month_start = date(today.year, today.month, 1)

        this_month_records = CostRecord.query.filter(
            CostRecord.status == 1,
            CostRecord.record_date >= this_month_start
        ).all()
        this_month_total = sum(float(r.amount) for r in this_month_records if r.element)

        last_year_same_month = date(today.year - 1, today.month, 1)
        if today.month == 12:
            last_year_end = date(today.year, 1, 1)
        else:
            last_year_end = date(today.year - 1, today.month + 1, 1)

        last_year_records = CostRecord.query.filter(
            CostRecord.status == 1,
            CostRecord.record_date >= last_year_same_month,
            CostRecord.record_date < last_year_end
        ).all()
        last_year_total = sum(float(r.amount) for r in last_year_records if r.element)

        yoy = ((this_month_total - last_year_total) / last_year_total * 100) if last_year_total > 0 else None

        type_totals = {'material': 0, 'labor': 0, 'depreciation': 0, 'energy': 0, 'other': 0}
        for r in this_month_records:
            if r.element:
                type_totals[r.element.element_type] += float(r.amount)

        return Response.success({
            'this_month_total': round(this_month_total, 2),
            'last_year_total': round(last_year_total, 2),
            'yoy': round(yoy, 2) if yoy is not None else None,
            'type_totals': {k: round(v, 2) for k, v in type_totals.items()}
        })

    @staticmethod
    def export_csv(dimension='product', start_date=None, end_date=None):
        """导出CSV数据"""
        report = CostReportService.get_multi_dimension_report(dimension, start_date, end_date)
        if report[1] != 200:
            return report

        data = report[0].get_json()['data']
        pivot_data = data['pivot_data']

        csv_lines = ['维度,原材料,人工,设备折旧,能源,其他,总计']
        for row in pivot_data:
            csv_lines.append(
                f"{row['dimension']},{row['material']},{row['labor']},{row['depreciation']},{row['energy']},{row['other']},{row['total']}"
            )

        csv_content = '\n'.join(csv_lines)
        return Response.success({
            'filename': f'cost_report_{dimension}_{datetime.now().strftime("%Y%m%d%H%M%S")}.csv',
            'content': csv_content
        })
