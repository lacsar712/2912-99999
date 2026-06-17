"""
SOP标准作业管理服务模块
"""
from datetime import datetime
from database.db import db
from models.sop import (
    SOPDocument, SOPStep, SOPVersion, SOPTrainingRelation,
    SOPChecklist, SOPChecklistItem
)
from models.production import Equipment
from utils.response import Response
from utils.validator import Validator


class SOPService:
    """SOP服务类"""

    # ==================== SOP文档 CRUD ====================

    @staticmethod
    def get_sops(page=1, size=20, status=None, keyword=None, equipment_id=None, product=None):
        query = SOPDocument.query
        if status:
            query = query.filter(SOPDocument.sop_status == status)
        if keyword:
            like = f'%{keyword}%'
            query = query.filter(
                db.or_(SOPDocument.sop_code.like(like),
                       SOPDocument.sop_name.like(like))
            )
        if product:
            query = query.filter(SOPDocument.applicable_product.like(f'%{product}%'))
        if equipment_id:
            query = query.filter(SOPDocument.equipment_ids.like(f'%{equipment_id}%'))
        pagination = query.order_by(SOPDocument.create_time.desc()).paginate(
            page=page, per_page=size, error_out=False
        )
        return Response.paginate(
            [item.to_dict(include_steps=False) for item in pagination.items],
            pagination.total, page, size
        )

    @staticmethod
    def get_sop(sop_id):
        sop = SOPDocument.get_by_id(sop_id)
        if not sop:
            return Response.not_found('SOP文档不存在')
        result = sop.to_dict()
        result['versions'] = [
            {
                'id': v.id,
                'version': v.version,
                'change_log': v.change_log,
                'published_time': v.published_time.strftime('%Y-%m-%d %H:%M:%S') if v.published_time else None,
                'published_by': v.published_by
            }
            for v in sop.versions.order_by(SOPVersion.create_time.desc()).all()
        ]
        relations = SOPTrainingRelation.query.filter_by(sop_id=sop_id, status=1).all()
        result['training_relations'] = [r.to_dict() for r in relations]
        return Response.success(result)

    @staticmethod
    def create_sop(data):
        validation = Validator.validate_form(data, {
            'sop_code': ['required'],
            'sop_name': ['required']
        })
        if not validation['valid']:
            return Response.bad_request(list(validation['errors'].values())[0])
        if SOPDocument.query.filter_by(sop_code=data['sop_code']).first():
            return Response.bad_request('SOP编号已存在')
        sop = SOPDocument(
            sop_code=data['sop_code'],
            sop_name=data['sop_name'],
            applicable_product=data.get('applicable_product'),
            version=data.get('version', '1.0'),
            sop_status=data.get('status', 'draft'),
            description=data.get('description'),
            created_by=data.get('created_by')
        )
        if data.get('equipment_id_list'):
            sop.set_equipment_ids(data['equipment_id_list'])
        db.session.add(sop)
        db.session.flush()
        if data.get('steps'):
            for idx, step_data in enumerate(data['steps']):
                step = SOPStep(
                    sop_id=sop.id,
                    step_order=step_data.get('order', idx + 1),
                    title=step_data.get('title', ''),
                    description=step_data.get('description'),
                    image_base64=step_data.get('image_base64'),
                    video_url=step_data.get('video_url'),
                    duration_minutes=step_data.get('duration_minutes', 0)
                )
                db.session.add(step)
        db.session.commit()
        return Response.created(sop.to_dict())

    @staticmethod
    def update_sop(sop_id, data):
        sop = SOPDocument.get_by_id(sop_id)
        if not sop:
            return Response.not_found('SOP文档不存在')
        if 'sop_code' in data and data['sop_code'] != sop.sop_code:
            if SOPDocument.query.filter_by(sop_code=data['sop_code']).first():
                return Response.bad_request('SOP编号已存在')
            sop.sop_code = data['sop_code']
        for key in ['sop_name', 'applicable_product', 'version', 'description']:
            if key in data:
                setattr(sop, key, data[key])
        if 'status' in data:
            sop.sop_status = data['status']
        if 'equipment_id_list' in data:
            sop.set_equipment_ids(data['equipment_id_list'])
        if 'steps' in data:
            SOPStep.query.filter_by(sop_id=sop_id).delete()
            for idx, step_data in enumerate(data['steps']):
                step = SOPStep(
                    sop_id=sop.id,
                    step_order=step_data.get('order', idx + 1),
                    title=step_data.get('title', ''),
                    description=step_data.get('description'),
                    image_base64=step_data.get('image_base64'),
                    video_url=step_data.get('video_url'),
                    duration_minutes=step_data.get('duration_minutes', 0)
                )
                db.session.add(step)
        db.session.commit()
        return Response.success(sop.to_dict())

    @staticmethod
    def delete_sop(sop_id):
        sop = SOPDocument.get_by_id(sop_id)
        if not sop:
            return Response.not_found('SOP文档不存在')
        sop.delete()
        return Response.success(message='删除成功')

    # ==================== SOP发布与版本 ====================

    @staticmethod
    def publish_sop(sop_id, data):
        sop = SOPDocument.get_by_id(sop_id)
        if not sop:
            return Response.not_found('SOP文档不存在')
        change_log = data.get('change_log', '')
        new_version = data.get('version')
        if not new_version:
            parts = sop.version.split('.')
            try:
                parts[-1] = str(int(parts[-1]) + 1)
                new_version = '.'.join(parts)
            except Exception:
                new_version = sop.version + '.1'
        snapshot = sop.snapshot_dict()
        version_record = SOPVersion(
            sop_id=sop.id,
            version=new_version,
            change_log=change_log,
            published_by=data.get('published_by')
        )
        version_record.set_snapshot(snapshot)
        db.session.add(version_record)
        sop.version = new_version
        sop.sop_status = 'published'
        db.session.commit()
        return Response.success(sop.to_dict())

    @staticmethod
    def get_version_diff(sop_id, version1_id=None, version2_id=None):
        sop = SOPDocument.get_by_id(sop_id)
        if not sop:
            return Response.not_found('SOP文档不存在')
        versions = sop.versions.order_by(SOPVersion.create_time.desc()).all()
        if len(versions) < 2 and not version1_id and not version2_id:
            return Response.success({'has_diff': False, 'message': '版本记录不足，无法对比'})
        v1 = None
        v2 = None
        if version1_id and version2_id:
            v1 = SOPVersion.get_by_id(version1_id)
            v2 = SOPVersion.get_by_id(version2_id)
        elif len(versions) >= 2:
            v1 = versions[1]
            v2 = versions[0]
        if not v1 or not v2:
            return Response.bad_request('无法找到指定版本进行对比')
        s1 = v1.get_snapshot()
        s2 = v2.get_snapshot()
        diff = {
            'version1': {'id': v1.id, 'version': v1.version, 'published_time': v1.published_time.strftime('%Y-%m-%d %H:%M:%S') if v1.published_time else None},
            'version2': {'id': v2.id, 'version': v2.version, 'published_time': v2.published_time.strftime('%Y-%m-%d %H:%M:%S') if v2.published_time else None},
            'fields': [],
            'steps': {'added': [], 'removed': [], 'modified': [], 'unchanged': []}
        }
        for field in ['sop_code', 'sop_name', 'applicable_product', 'version', 'description']:
            old_val = s1.get(field, '')
            new_val = s2.get(field, '')
            if old_val != new_val:
                diff['fields'].append({'field': field, 'old': old_val, 'new': new_val})
        steps1 = {s['step_order']: s for s in s1.get('steps', [])}
        steps2 = {s['step_order']: s for s in s2.get('steps', [])}
        all_orders = set(steps1.keys()) | set(steps2.keys())
        for order in sorted(all_orders):
            s1_step = steps1.get(order)
            s2_step = steps2.get(order)
            if s1_step and not s2_step:
                diff['steps']['removed'].append({'order': order, 'step': s1_step})
            elif not s1_step and s2_step:
                diff['steps']['added'].append({'order': order, 'step': s2_step})
            elif s1_step and s2_step:
                mod_fields = {}
                for key in ['title', 'description', 'video_url', 'duration_minutes', 'has_image']:
                    if s1_step.get(key) != s2_step.get(key):
                        mod_fields[key] = {'old': s1_step.get(key), 'new': s2_step.get(key)}
                if mod_fields:
                    diff['steps']['modified'].append({'order': order, 'fields': mod_fields})
                else:
                    diff['steps']['unchanged'].append({'order': order, 'step': s2_step})
        diff['has_diff'] = bool(diff['fields']) or bool(diff['steps']['added']) or bool(diff['steps']['removed']) or bool(diff['steps']['modified'])
        return Response.success(diff)

    # ==================== 培训关联 ====================

    @staticmethod
    def add_training_relation(sop_id, course_id):
        sop = SOPDocument.get_by_id(sop_id)
        if not sop:
            return Response.not_found('SOP文档不存在')
        from models.training import TrainingCourse
        if not TrainingCourse.get_by_id(course_id):
            return Response.not_found('培训课程不存在')
        if SOPTrainingRelation.query.filter_by(sop_id=sop_id, training_course_id=course_id, status=1).first():
            return Response.bad_request('关联已存在')
        rel = SOPTrainingRelation(sop_id=sop_id, training_course_id=course_id)
        db.session.add(rel)
        db.session.commit()
        return Response.created(rel.to_dict())

    @staticmethod
    def remove_training_relation(relation_id):
        rel = SOPTrainingRelation.get_by_id(relation_id)
        if not rel:
            return Response.not_found('关联不存在')
        rel.delete()
        return Response.success(message='已解除关联')

    # ==================== 按设备/产品查询 ====================

    @staticmethod
    def get_sops_by_equipment(equipment_id):
        eq = Equipment.get_by_id(equipment_id)
        if not eq:
            return Response.not_found('设备不存在')
        like = f'%{equipment_id}%'
        sops = SOPDocument.query.filter(
            SOPDocument.sop_status == 'published',
            SOPDocument.equipment_ids.like(like)
        ).all()
        return Response.success([s.to_dict(include_steps=False) for s in sops])

    @staticmethod
    def get_sops_by_product(product_name):
        sops = SOPDocument.query.filter(
            SOPDocument.sop_status == 'published',
            SOPDocument.applicable_product.like(f'%{product_name}%')
        ).all()
        return Response.success([s.to_dict(include_steps=False) for s in sops])

    # ==================== 执行检查表 ====================

    @staticmethod
    def get_checklists(page=1, size=20, sop_id=None, equipment_id=None, operator_id=None):
        query = SOPChecklist.query
        if sop_id:
            query = query.filter(SOPChecklist.sop_id == sop_id)
        if equipment_id:
            query = query.filter(SOPChecklist.equipment_id == equipment_id)
        if operator_id:
            query = query.filter(SOPChecklist.operator_id == operator_id)
        pagination = query.order_by(SOPChecklist.create_time.desc()).paginate(
            page=page, per_page=size, error_out=False
        )
        return Response.paginate(
            [item.to_dict(include_items=False) for item in pagination.items],
            pagination.total, page, size
        )

    @staticmethod
    def get_checklist(checklist_id):
        cl = SOPChecklist.get_by_id(checklist_id)
        if not cl:
            return Response.not_found('检查表不存在')
        return Response.success(cl.to_dict())

    @staticmethod
    def create_checklist(data):
        validation = Validator.validate_form(data, {
            'sop_id': ['required']
        })
        if not validation['valid']:
            return Response.bad_request(list(validation['errors'].values())[0])
        sop = SOPDocument.get_by_id(data['sop_id'])
        if not sop:
            return Response.not_found('SOP文档不存在')
        cl = SOPChecklist(
            sop_id=sop.id,
            sop_version=sop.version,
            equipment_id=data.get('equipment_id'),
            operator_id=data.get('operator_id'),
            operator_name=data.get('operator_name'),
            remark=data.get('remark')
        )
        db.session.add(cl)
        db.session.flush()
        for step in sop.steps.all():
            item = SOPChecklistItem(
                checklist_id=cl.id,
                step_order=step.step_order,
                step_title=step.title,
                step_description=step.description,
                is_completed=False
            )
            db.session.add(item)
        db.session.commit()
        return Response.created(cl.to_dict())

    @staticmethod
    def update_checklist_item(checklist_id, item_id, data):
        cl = SOPChecklist.get_by_id(checklist_id)
        if not cl:
            return Response.not_found('检查表不存在')
        item = SOPChecklistItem.get_by_id(item_id)
        if not item or item.checklist_id != checklist_id:
            return Response.not_found('检查项不存在')
        if 'is_completed' in data:
            item.is_completed = data['is_completed']
            if data['is_completed']:
                item.completed_time = datetime.now()
        if 'photo_base64' in data:
            item.photo_base64 = data['photo_base64']
        if 'remark' in data:
            item.remark = data['remark']
        db.session.commit()
        cl.compliance_rate = cl.calculate_compliance()
        db.session.commit()
        return Response.success(item.to_dict())

    @staticmethod
    def submit_checklist(checklist_id, data):
        cl = SOPChecklist.get_by_id(checklist_id)
        if not cl:
            return Response.not_found('检查表不存在')
        cl.end_time = datetime.now()
        cl.compliance_rate = cl.calculate_compliance()
        cl.signer_id = data.get('signer_id')
        cl.signer_name = data.get('signer_name')
        cl.sign_time = datetime.now()
        if 'remark' in data:
            cl.remark = data['remark']
        db.session.commit()
        return Response.success(cl.to_dict())

    @staticmethod
    def delete_checklist(checklist_id):
        cl = SOPChecklist.get_by_id(checklist_id)
        if not cl:
            return Response.not_found('检查表不存在')
        cl.delete()
        return Response.success(message='删除成功')

    # ==================== 合规率统计 ====================

    @staticmethod
    def get_compliance_stats(sop_id=None, equipment_id=None, start_date=None, end_date=None):
        query = SOPChecklist.query.filter(SOPChecklist.sign_time.isnot(None))
        if sop_id:
            query = query.filter(SOPChecklist.sop_id == sop_id)
        if equipment_id:
            query = query.filter(SOPChecklist.equipment_id == equipment_id)
        if start_date:
            try:
                sd = datetime.strptime(start_date, '%Y-%m-%d')
                query = query.filter(SOPChecklist.sign_time >= sd)
            except Exception:
                pass
        if end_date:
            try:
                ed = datetime.strptime(end_date, '%Y-%m-%d')
                ed = ed.replace(hour=23, minute=59, second=59)
                query = query.filter(SOPChecklist.sign_time <= ed)
            except Exception:
                pass
        records = query.all()
        total = len(records)
        if total == 0:
            return Response.success({
                'total_checklists': 0,
                'avg_compliance_rate': 0,
                'compliant_count': 0,
                'non_compliant_count': 0,
                'by_sop': [],
                'by_equipment': [],
                'daily_trend': []
            })
        rates = [float(r.compliance_rate or 0) for r in records]
        avg_rate = round(sum(rates) / total, 2)
        compliant = sum(1 for r in rates if r >= 100)
        non_compliant = total - compliant
        sop_stats = {}
        for r in records:
            key = r.sop_id
            if key not in sop_stats:
                sop_stats[key] = {'sop_id': key, 'count': 0, 'rates': []}
                try:
                    sop = SOPDocument.get_by_id(key)
                    if sop:
                        sop_stats[key]['sop_code'] = sop.sop_code
                        sop_stats[key]['sop_name'] = sop.sop_name
                except Exception:
                    sop_stats[key]['sop_code'] = '-'
                    sop_stats[key]['sop_name'] = '-'
            sop_stats[key]['count'] += 1
            sop_stats[key]['rates'].append(float(r.compliance_rate or 0))
        by_sop = []
        for k, v in sop_stats.items():
            v['avg_rate'] = round(sum(v['rates']) / len(v['rates']), 2) if v['rates'] else 0
            del v['rates']
            by_sop.append(v)
        eq_stats = {}
        for r in records:
            key = r.equipment_id or 0
            if key not in eq_stats:
                eq_stats[key] = {'equipment_id': key, 'count': 0, 'rates': []}
                try:
                    if key:
                        eq = Equipment.get_by_id(key)
                        if eq:
                            eq_stats[key]['equipment_code'] = eq.equipment_code
                            eq_stats[key]['equipment_name'] = eq.equipment_name
                except Exception:
                    pass
            eq_stats[key]['count'] += 1
            eq_stats[key]['rates'].append(float(r.compliance_rate or 0))
        by_equipment = []
        for k, v in eq_stats.items():
            v['avg_rate'] = round(sum(v['rates']) / len(v['rates']), 2) if v['rates'] else 0
            del v['rates']
            by_equipment.append(v)
        daily = {}
        for r in records:
            if r.sign_time:
                day = r.sign_time.strftime('%Y-%m-%d')
                if day not in daily:
                    daily[day] = {'date': day, 'count': 0, 'rates': []}
                daily[day]['count'] += 1
                daily[day]['rates'].append(float(r.compliance_rate or 0))
        daily_trend = []
        for k in sorted(daily.keys()):
            v = daily[k]
            v['avg_rate'] = round(sum(v['rates']) / len(v['rates']), 2) if v['rates'] else 0
            del v['rates']
            daily_trend.append(v)
        return Response.success({
            'total_checklists': total,
            'avg_compliance_rate': avg_rate,
            'compliant_count': compliant,
            'non_compliant_count': non_compliant,
            'by_sop': by_sop,
            'by_equipment': by_equipment,
            'daily_trend': daily_trend
        })
