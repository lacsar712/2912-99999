"""
安全管理服务模块
"""
from datetime import datetime, timedelta
from database.db import db
from models.safety import HazardType, InspectionTask, HazardRecord, RectificationRecord, AccidentRecord
from models.production import AlertRecord
from utils.response import Response


class SafetyService:

    @staticmethod
    def get_hazard_types(page=1, size=20, category=None):
        query = HazardType.query
        if category:
            query = query.filter(HazardType.category == category)
        query = query.filter(HazardType.is_active == True)
        pagination = query.order_by(HazardType.create_time.desc()).paginate(
            page=page, per_page=size, error_out=False
        )
        return Response.paginate(
            [item.to_dict() for item in pagination.items],
            pagination.total, page, size
        )

    @staticmethod
    def create_hazard_type(data):
        from utils.validator import Validator
        validation = Validator.validate_form(data, {
            'type_code': ['required'],
            'type_name': ['required']
        })
        if not validation['valid']:
            return Response.bad_request(list(validation['errors'].values())[0])
        if HazardType.query.filter_by(type_code=data['type_code']).first():
            return Response.bad_request('类型编码已存在')
        ht = HazardType(
            type_code=data['type_code'],
            type_name=data['type_name'],
            category=data.get('category'),
            description=data.get('description')
        )
        db.session.add(ht)
        db.session.commit()
        return Response.created(ht.to_dict())

    @staticmethod
    def update_hazard_type(type_id, data):
        ht = HazardType.get_by_id(type_id)
        if not ht:
            return Response.not_found('隐患类型不存在')
        for key in ['type_name', 'category', 'description', 'is_active']:
            if key in data:
                setattr(ht, key, data[key])
        db.session.commit()
        return Response.success(ht.to_dict())

    @staticmethod
    def delete_hazard_type(type_id):
        ht = HazardType.get_by_id(type_id)
        if not ht:
            return Response.not_found('隐患类型不存在')
        ht.is_active = False
        db.session.commit()
        return Response.success(message='删除成功')

    @staticmethod
    def get_inspection_tasks(page=1, size=20, task_type=None):
        query = InspectionTask.query
        if task_type:
            query = query.filter(InspectionTask.task_type == task_type)
        query = query.filter(InspectionTask.is_active == True)
        pagination = query.order_by(InspectionTask.create_time.desc()).paginate(
            page=page, per_page=size, error_out=False
        )
        return Response.paginate(
            [item.to_dict() for item in pagination.items],
            pagination.total, page, size
        )

    @staticmethod
    def create_inspection_task(data):
        from utils.validator import Validator
        validation = Validator.validate_form(data, {
            'task_code': ['required'],
            'task_name': ['required']
        })
        if not validation['valid']:
            return Response.bad_request(list(validation['errors'].values())[0])
        if InspectionTask.query.filter_by(task_code=data['task_code']).first():
            return Response.bad_request('任务编号已存在')
        task = InspectionTask(
            task_code=data['task_code'],
            task_name=data['task_name'],
            task_type=data.get('task_type', 'plan'),
            period=data.get('period'),
            responsible_person=data.get('responsible_person'),
            area=data.get('area'),
            description=data.get('description'),
            next_execution=datetime.strptime(data['next_execution'], '%Y-%m-%d %H:%M:%S') if data.get('next_execution') else None
        )
        db.session.add(task)
        db.session.commit()
        return Response.created(task.to_dict())

    @staticmethod
    def update_inspection_task(task_id, data):
        task = InspectionTask.get_by_id(task_id)
        if not task:
            return Response.not_found('排查任务不存在')
        for key in ['task_name', 'task_type', 'period', 'responsible_person', 'area', 'description', 'is_active']:
            if key in data:
                setattr(task, key, data[key])
        if 'next_execution' in data and data['next_execution']:
            task.next_execution = datetime.strptime(data['next_execution'], '%Y-%m-%d %H:%M:%S')
        db.session.commit()
        return Response.success(task.to_dict())

    @staticmethod
    def delete_inspection_task(task_id):
        task = InspectionTask.get_by_id(task_id)
        if not task:
            return Response.not_found('排查任务不存在')
        task.is_active = False
        db.session.commit()
        return Response.success(message='删除成功')

    @staticmethod
    def get_hazard_records(page=1, size=20, hazard_status=None, severity=None, hazard_type_id=None):
        query = HazardRecord.query
        if hazard_status:
            query = query.filter(HazardRecord.hazard_status == hazard_status)
        if severity:
            query = query.filter(HazardRecord.severity == severity)
        if hazard_type_id:
            query = query.filter(HazardRecord.hazard_type_id == hazard_type_id)
        pagination = query.order_by(HazardRecord.create_time.desc()).paginate(
            page=page, per_page=size, error_out=False
        )
        return Response.paginate(
            [item.to_dict() for item in pagination.items],
            pagination.total, page, size
        )

    @staticmethod
    def get_hazard_record_by_id(record_id):
        record = HazardRecord.get_by_id(record_id)
        if not record:
            return Response.not_found('隐患记录不存在')
        result = record.to_dict()
        result['rectifications'] = [r.to_dict() for r in record.rectifications.all()]
        return Response.success(result)

    @staticmethod
    def create_hazard_record(data):
        from utils.validator import Validator
        validation = Validator.validate_form(data, {
            'title': ['required']
        })
        if not validation['valid']:
            return Response.bad_request(list(validation['errors'].values())[0])
        now = datetime.now()
        hazard_code = f"HZ-{now.strftime('%Y%m%d%H%M%S')}-{HazardRecord.query.count() + 1}"
        deadline = None
        if data.get('deadline'):
            deadline = datetime.strptime(data['deadline'], '%Y-%m-%d %H:%M:%S')
        record = HazardRecord(
            hazard_code=hazard_code,
            title=data['title'],
            discoverer=data.get('discoverer'),
            location=data.get('location'),
            hazard_type_id=data.get('hazard_type_id'),
            severity=data.get('severity', 'medium'),
            photo_base64=data.get('photo_base64'),
            hazard_status=data.get('hazard_status', 'pending'),
            description=data.get('description'),
            deadline=deadline,
            inspection_task_id=data.get('inspection_task_id')
        )
        db.session.add(record)
        db.session.commit()
        return Response.created(record.to_dict())

    @staticmethod
    def update_hazard_record(record_id, data):
        record = HazardRecord.get_by_id(record_id)
        if not record:
            return Response.not_found('隐患记录不存在')
        old_status = record.hazard_status
        for key in ['title', 'discoverer', 'location', 'hazard_type_id', 'severity',
                     'photo_base64', 'hazard_status', 'description', 'is_escalated', 'inspection_task_id']:
            if key in data:
                setattr(record, key, data[key])
        if 'deadline' in data and data['deadline']:
            record.deadline = datetime.strptime(data['deadline'], '%Y-%m-%d %H:%M:%S')
        db.session.commit()
        return Response.success(record.to_dict())

    @staticmethod
    def delete_hazard_record(record_id):
        record = HazardRecord.get_by_id(record_id)
        if not record:
            return Response.not_found('隐患记录不存在')
        record.delete()
        return Response.success(message='删除成功')

    @staticmethod
    def get_rectification_records(hazard_id, page=1, size=20):
        query = RectificationRecord.query.filter_by(hazard_id=hazard_id)
        pagination = query.order_by(RectificationRecord.create_time.desc()).paginate(
            page=page, per_page=size, error_out=False
        )
        return Response.paginate(
            [item.to_dict() for item in pagination.items],
            pagination.total, page, size
        )

    @staticmethod
    def create_rectification_record(data):
        from utils.validator import Validator
        validation = Validator.validate_form(data, {
            'hazard_id': ['required'],
            'measure': ['required']
        })
        if not validation['valid']:
            return Response.bad_request(list(validation['errors'].values())[0])
        hazard = HazardRecord.get_by_id(data['hazard_id'])
        if not hazard:
            return Response.not_found('隐患记录不存在')
        plan_time = None
        if data.get('plan_complete_time'):
            plan_time = datetime.strptime(data['plan_complete_time'], '%Y-%m-%d %H:%M:%S')
        actual_time = None
        if data.get('actual_complete_time'):
            actual_time = datetime.strptime(data['actual_complete_time'], '%Y-%m-%d %H:%M:%S')
        rect = RectificationRecord(
            hazard_id=data['hazard_id'],
            measure=data['measure'],
            responsible_person=data.get('responsible_person'),
            plan_complete_time=plan_time,
            actual_complete_time=actual_time,
            result=data.get('result'),
            photo_base64=data.get('photo_base64')
        )
        db.session.add(rect)
        if hazard.hazard_status == 'pending':
            hazard.hazard_status = 'rectifying'
        if actual_time:
            hazard.hazard_status = 'rectified'
        db.session.commit()
        return Response.created(rect.to_dict())

    @staticmethod
    def update_rectification_record(rect_id, data):
        rect = RectificationRecord.get_by_id(rect_id)
        if not rect:
            return Response.not_found('整改记录不存在')
        for key in ['measure', 'responsible_person', 'result', 'photo_base64']:
            if key in data:
                setattr(rect, key, data[key])
        if 'plan_complete_time' in data and data['plan_complete_time']:
            rect.plan_complete_time = datetime.strptime(data['plan_complete_time'], '%Y-%m-%d %H:%M:%S')
        if 'actual_complete_time' in data and data['actual_complete_time']:
            rect.actual_complete_time = datetime.strptime(data['actual_complete_time'], '%Y-%m-%d %H:%M:%S')
            hazard = HazardRecord.get_by_id(rect.hazard_id)
            if hazard:
                hazard.hazard_status = 'rectified'
        db.session.commit()
        return Response.success(rect.to_dict())

    @staticmethod
    def accept_hazard(record_id):
        record = HazardRecord.get_by_id(record_id)
        if not record:
            return Response.not_found('隐患记录不存在')
        if record.hazard_status != 'rectified':
            return Response.bad_request('只有已整改的隐患才能验收')
        record.hazard_status = 'accepted'
        db.session.commit()
        return Response.success(record.to_dict())

    @staticmethod
    def get_accident_records(page=1, size=20, severity=None):
        query = AccidentRecord.query
        if severity:
            query = query.filter(AccidentRecord.severity == severity)
        pagination = query.order_by(AccidentRecord.create_time.desc()).paginate(
            page=page, per_page=size, error_out=False
        )
        return Response.paginate(
            [item.to_dict() for item in pagination.items],
            pagination.total, page, size
        )

    @staticmethod
    def get_accident_record_by_id(record_id):
        record = AccidentRecord.get_by_id(record_id)
        if not record:
            return Response.not_found('事故记录不存在')
        return Response.success(record.to_dict())

    @staticmethod
    def create_accident_record(data):
        from utils.validator import Validator
        validation = Validator.validate_form(data, {
            'accident_time': ['required'],
            'location': ['required']
        })
        if not validation['valid']:
            return Response.bad_request(list(validation['errors'].values())[0])
        now = datetime.now()
        accident_code = f"AC-{now.strftime('%Y%m%d%H%M%S')}-{AccidentRecord.query.count() + 1}"
        accident_time = datetime.strptime(data['accident_time'], '%Y-%m-%d %H:%M:%S')
        loss = None
        if data.get('loss_estimate'):
            loss = float(data['loss_estimate'])
        record = AccidentRecord(
            accident_code=accident_code,
            accident_time=accident_time,
            location=data['location'],
            involved_persons=data.get('involved_persons'),
            loss_estimate=loss,
            cause_analysis=data.get('cause_analysis'),
            rectification_measures=data.get('rectification_measures'),
            attachment_base64=data.get('attachment_base64'),
            severity=data.get('severity', 'general'),
            description=data.get('description')
        )
        db.session.add(record)
        db.session.commit()
        return Response.created(record.to_dict())

    @staticmethod
    def update_accident_record(record_id, data):
        record = AccidentRecord.get_by_id(record_id)
        if not record:
            return Response.not_found('事故记录不存在')
        for key in ['location', 'involved_persons', 'cause_analysis',
                     'rectification_measures', 'attachment_base64', 'severity', 'description']:
            if key in data:
                setattr(record, key, data[key])
        if 'accident_time' in data and data['accident_time']:
            record.accident_time = datetime.strptime(data['accident_time'], '%Y-%m-%d %H:%M:%S')
        if 'loss_estimate' in data and data['loss_estimate'] is not None:
            record.loss_estimate = float(data['loss_estimate'])
        db.session.commit()
        return Response.success(record.to_dict())

    @staticmethod
    def delete_accident_record(record_id):
        record = AccidentRecord.get_by_id(record_id)
        if not record:
            return Response.not_found('事故记录不存在')
        record.delete()
        return Response.success(message='删除成功')

    @staticmethod
    def check_overdue_hazards():
        now = datetime.now()
        overdue_records = HazardRecord.query.filter(
            HazardRecord.hazard_status.in_(['pending', 'rectifying']),
            HazardRecord.deadline != None,
            HazardRecord.deadline < now,
            HazardRecord.is_escalated == False
        ).all()
        escalated_count = 0
        for record in overdue_records:
            record.is_escalated = True
            alert_code = f"ALERT-{now.strftime('%Y%m%d%H%M%S')}-SAFETY-{record.id}"
            alert = AlertRecord(
                alert_code=alert_code,
                alert_type='safety_overdue',
                severity='error',
                message=f'隐患"{record.title}"({record.hazard_code})已超过整改截止时间，请立即处理！',
                status='active'
            )
            db.session.add(alert)
            escalated_count += 1
        db.session.commit()
        return Response.success({
            'checked_count': len(overdue_records),
            'escalated_count': escalated_count
        })

    @staticmethod
    def get_monthly_report(months=6):
        now = datetime.now()
        month_labels = []
        hazard_counts = []
        rectified_counts = []
        accident_counts = []
        rectification_rates = []

        for i in range(months - 1, -1, -1):
            month_start = (now - timedelta(days=30 * i)).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            if month_start.month == 12:
                month_end = month_start.replace(year=month_start.year + 1, month=1)
            else:
                month_end = month_start.replace(month=month_start.month + 1)
            label = month_start.strftime('%Y-%m')
            month_labels.append(label)

            hazard_count = HazardRecord.query.filter(
                HazardRecord.create_time >= month_start,
                HazardRecord.create_time < month_end
            ).count()

            rectified_count = HazardRecord.query.filter(
                HazardRecord.hazard_status.in_(['rectified', 'accepted']),
                HazardRecord.create_time >= month_start,
                HazardRecord.create_time < month_end
            ).count()

            accident_count = AccidentRecord.query.filter(
                AccidentRecord.create_time >= month_start,
                AccidentRecord.create_time < month_end
            ).count()

            rate = round(rectified_count / hazard_count * 100, 1) if hazard_count > 0 else 100.0

            hazard_counts.append(hazard_count)
            rectified_counts.append(rectified_count)
            accident_counts.append(accident_count)
            rectification_rates.append(rate)

        total_hazards = HazardRecord.query.count()
        pending_hazards = HazardRecord.query.filter(HazardRecord.hazard_status == 'pending').count()
        rectifying_hazards = HazardRecord.query.filter(HazardRecord.hazard_status == 'rectifying').count()
        rectified_hazards = HazardRecord.query.filter(HazardRecord.hazard_status == 'rectified').count()
        accepted_hazards = HazardRecord.query.filter(HazardRecord.hazard_status == 'accepted').count()
        total_accidents = AccidentRecord.query.count()

        by_severity = {}
        for sev in ['low', 'medium', 'high', 'critical']:
            by_severity[sev] = HazardRecord.query.filter(HazardRecord.severity == sev).count()

        by_type = db.session.query(
            HazardType.type_name,
            db.func.count(HazardRecord.id)
        ).join(HazardRecord, HazardType.id == HazardRecord.hazard_type_id, isouter=True).group_by(
            HazardType.type_name
        ).all()
        by_type_dict = {name: count for name, count in by_type}

        return Response.success({
            'summary': {
                'total_hazards': total_hazards,
                'pending': pending_hazards,
                'rectifying': rectifying_hazards,
                'rectified': rectified_hazards,
                'accepted': accepted_hazards,
                'total_accidents': total_accidents,
                'overall_rectification_rate': round(
                    (rectified_hazards + accepted_hazards) / total_hazards * 100, 1
                ) if total_hazards > 0 else 100.0
            },
            'trend': {
                'labels': month_labels,
                'hazard_counts': hazard_counts,
                'rectified_counts': rectified_counts,
                'accident_counts': accident_counts,
                'rectification_rates': rectification_rates
            },
            'by_severity': by_severity,
            'by_type': by_type_dict
        })
