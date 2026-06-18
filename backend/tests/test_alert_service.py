"""
告警服务单元测试
覆盖告警创建、查询、确认、解决、批量解决、统计等核心方法
"""
import pytest
import sys
import os
import json
from datetime import datetime
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


@pytest.fixture
def app_context():
    """创建Flask应用上下文，使用内存SQLite数据库"""
    from flask import Flask
    from database.db import db
    import models.production
    import models.user
    import models.log
    
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'test-secret-key'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['TESTING'] = True
    
    db.init_app(app)
    
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


class TestAlertService:
    """告警服务测试类"""

    def test_create_alert_success(self, app_context):
        """测试创建告警成功"""
        from services.alert_service import AlertService

        alert_data = {
            'alert_type': 'temperature',
            'message': '温度超过阈值',
            'severity': 'critical',
            'equipment_id': 1,
            'sensor_id': 1,
            'value': 85.5,
            'threshold': 80.0
        }

        response = AlertService.create_alert(alert_data)
        
        assert response[1] == 200
        data = json.loads(response[0].data)
        assert data['code'] == 200
        assert 'data' in data
        assert data['data']['alert_code'] is not None
        assert data['data']['status'] == 'active'
        assert data['data']['severity'] == 'critical'

    def test_create_alert_missing_required_fields(self, app_context):
        """测试创建告警缺少必填字段"""
        from services.alert_service import AlertService

        # 缺少 alert_type
        alert_data = {'message': '温度告警'}
        response = AlertService.create_alert(alert_data)
        assert response[1] == 400

        # 缺少 message
        alert_data = {'alert_type': 'temperature'}
        response = AlertService.create_alert(alert_data)
        assert response[1] == 400

    def test_create_alert_invalid_severity(self, app_context):
        """测试创建告警使用无效的严重程度值"""
        from services.alert_service import AlertService

        alert_data = {
            'alert_type': 'test',
            'message': '测试告警',
            'severity': 'invalid_severity'  # 无效值
        }

        # 由于数据库会验证枚举值，这里应该会引发错误
        with pytest.raises(Exception):
            AlertService.create_alert(alert_data)

    def test_get_alerts_pagination(self, app_context):
        """测试分页查询告警列表"""
        from services.alert_service import AlertService
        from models.production import AlertRecord
        from database.db import db

        # 创建测试数据
        for i in range(25):
            alert = AlertRecord(
                alert_code=f'ALERT-TEST-{i}',
                alert_type='test',
                message=f'Test alert {i}',
                severity='warning',
                status='active'
            )
            db.session.add(alert)
        db.session.commit()

        # 测试第一页
        response = AlertService.get_alerts(page=1, size=10)
        assert response[1] == 200
        data = json.loads(response[0].data)
        assert len(data['data']['items']) == 10
        assert data['data']['total'] == 25
        assert data['data']['page'] == 1

        # 测试最后一页
        response = AlertService.get_alerts(page=3, size=10)
        assert response[1] == 200
        data = json.loads(response[0].data)
        assert len(data['data']['items']) == 5

    def test_get_alerts_empty_list(self, app_context):
        """测试查询空告警列表"""
        from services.alert_service import AlertService

        response = AlertService.get_alerts()
        assert response[1] == 200
        data = json.loads(response[0].data)
        assert len(data['data']['items']) == 0
        assert data['data']['total'] == 0

    def test_get_alerts_large_page_number(self, app_context):
        """测试超大分页页码"""
        from services.alert_service import AlertService

        response = AlertService.get_alerts(page=99999, size=10)
        assert response[1] == 200
        data = json.loads(response[0].data)
        assert len(data['data']['items']) == 0

    def test_get_alerts_filter_by_severity(self, app_context):
        """测试按严重程度过滤告警"""
        from services.alert_service import AlertService
        from models.production import AlertRecord
        from database.db import db

        # 创建不同严重程度的告警
        severities = ['critical', 'error', 'warning', 'info']
        for i, severity in enumerate(severities):
            for j in range(3):
                alert = AlertRecord(
                    alert_code=f'ALERT-{severity}-{j}',
                    alert_type='test',
                    message=f'{severity} alert {j}',
                    severity=severity,
                    status='active'
                )
                db.session.add(alert)
        db.session.commit()

        # 只查询 critical 告警
        response = AlertService.get_alerts(severity='critical')
        assert response[1] == 200
        data = json.loads(response[0].data)
        assert len(data['data']['items']) == 3
        for item in data['data']['items']:
            assert item['severity'] == 'critical'

    def test_get_alerts_filter_by_status(self, app_context):
        """测试按状态过滤告警"""
        from services.alert_service import AlertService
        from models.production import AlertRecord
        from database.db import db

        # 创建不同状态的告警
        statuses = ['active', 'acknowledged', 'resolved']
        for status in statuses:
            for i in range(3):
                alert = AlertRecord(
                    alert_code=f'ALERT-{status}-{i}',
                    alert_type='test',
                    message=f'{status} alert {i}',
                    severity='warning',
                    status=status
                )
                db.session.add(alert)
        db.session.commit()

        # 只查询 active 告警
        response = AlertService.get_alerts(status='active')
        assert response[1] == 200
        data = json.loads(response[0].data)
        assert len(data['data']['items']) == 3

    def test_get_alert_by_id_success(self, app_context):
        """测试获取告警详情成功"""
        from services.alert_service import AlertService
        from models.production import AlertRecord
        from database.db import db

        alert = AlertRecord(
            alert_code='ALERT-TEST-001',
            alert_type='temperature',
            message='温度告警',
            severity='error',
            status='active'
        )
        db.session.add(alert)
        db.session.commit()

        response = AlertService.get_alert_by_id(alert.id)
        assert response[1] == 200
        data = json.loads(response[0].data)
        assert data['code'] == 200
        assert data['data']['id'] == alert.id
        assert data['data']['alert_code'] == 'ALERT-TEST-001'

    def test_get_alert_by_id_not_found(self, app_context):
        """测试获取不存在的告警"""
        from services.alert_service import AlertService

        response = AlertService.get_alert_by_id(99999)
        assert response[1] == 404
        data = json.loads(response[0].data)
        assert data['code'] == 404

    def test_acknowledge_alert_success(self, app_context):
        """测试确认告警成功"""
        from services.alert_service import AlertService
        from models.production import AlertRecord
        from database.db import db

        alert = AlertRecord(
            alert_code='ALERT-ACK-001',
            alert_type='test',
            message='Test alert',
            severity='warning',
            status='active'
        )
        db.session.add(alert)
        db.session.commit()

        response = AlertService.acknowledge_alert(alert.id, '已确认')
        assert response[1] == 200
        data = json.loads(response[0].data)
        assert data['data']['status'] == 'acknowledged'
        assert data['data']['resolve_note'] == '已确认'

    def test_acknowledge_alert_not_found(self, app_context):
        """测试确认不存在的告警"""
        from services.alert_service import AlertService

        response = AlertService.acknowledge_alert(99999)
        assert response[1] == 404

    def test_acknowledge_alert_already_acknowledged(self, app_context):
        """测试确认已确认的告警（状态非法流转）"""
        from services.alert_service import AlertService
        from models.production import AlertRecord
        from database.db import db

        alert = AlertRecord(
            alert_code='ALERT-ACK-002',
            alert_type='test',
            message='Test alert',
            severity='warning',
            status='acknowledged'
        )
        db.session.add(alert)
        db.session.commit()

        response = AlertService.acknowledge_alert(alert.id)
        assert response[1] == 400
        data = json.loads(response[0].data)
        assert data['code'] == 400

    def test_acknowledge_alert_resolved(self, app_context):
        """测试确认已解决的告警（状态非法流转）"""
        from services.alert_service import AlertService
        from models.production import AlertRecord
        from database.db import db

        alert = AlertRecord(
            alert_code='ALERT-ACK-003',
            alert_type='test',
            message='Test alert',
            severity='warning',
            status='resolved'
        )
        db.session.add(alert)
        db.session.commit()

        response = AlertService.acknowledge_alert(alert.id)
        assert response[1] == 400

    def test_resolve_alert_success(self, app_context):
        """测试解决告警成功"""
        from services.alert_service import AlertService
        from models.production import AlertRecord
        from database.db import db

        alert = AlertRecord(
            alert_code='ALERT-RES-001',
            alert_type='test',
            message='Test alert',
            severity='error',
            status='active'
        )
        db.session.add(alert)
        db.session.commit()

        response = AlertService.resolve_alert(alert.id, '已修复')
        assert response[1] == 200
        data = json.loads(response[0].data)
        assert data['data']['status'] == 'resolved'
        assert data['data']['resolve_note'] == '已修复'

    def test_resolve_alert_not_found(self, app_context):
        """测试解决不存在的告警"""
        from services.alert_service import AlertService

        response = AlertService.resolve_alert(99999)
        assert response[1] == 404

    def test_resolve_alert_already_resolved(self, app_context):
        """测试解决已解决的告警（状态非法流转）"""
        from services.alert_service import AlertService
        from models.production import AlertRecord
        from database.db import db

        alert = AlertRecord(
            alert_code='ALERT-RES-002',
            alert_type='test',
            message='Test alert',
            severity='warning',
            status='resolved'
        )
        db.session.add(alert)
        db.session.commit()

        response = AlertService.resolve_alert(alert.id)
        assert response[1] == 200
        data = json.loads(response[0].data)
        assert data['data']['status'] == 'resolved'

    def test_batch_resolve_success(self, app_context):
        """测试批量解决告警成功"""
        from services.alert_service import AlertService
        from models.production import AlertRecord
        from database.db import db

        # 创建多个告警
        alert_ids = []
        for i in range(5):
            alert = AlertRecord(
                alert_code=f'ALERT-BATCH-{i}',
                alert_type='test',
                message=f'Test alert {i}',
                severity='warning',
                status='active'
            )
            db.session.add(alert)
            db.session.flush()
            alert_ids.append(alert.id)
        db.session.commit()

        # 批量解决前3个
        response = AlertService.batch_resolve(alert_ids[:3], '批量解决')
        assert response[1] == 200
        data = json.loads(response[0].data)
        assert data['data']['resolved_count'] == 3

        # 验证状态变化
        for i, aid in enumerate(alert_ids):
            alert = AlertRecord.get_by_id(aid)
            if i < 3:
                assert alert.status == 'resolved'
                assert alert.resolve_note == '批量解决'
            else:
                assert alert.status == 'active'

    def test_batch_resolve_empty_list(self, app_context):
        """测试批量解决空列表"""
        from services.alert_service import AlertService

        response = AlertService.batch_resolve([])
        assert response[1] == 200
        data = json.loads(response[0].data)
        assert data['data']['resolved_count'] == 0

    def test_batch_resolve_invalid_ids(self, app_context):
        """测试批量解决包含无效ID的列表"""
        from services.alert_service import AlertService
        from models.production import AlertRecord
        from database.db import db

        # 创建一个告警
        alert = AlertRecord(
            alert_code='ALERT-BATCH-001',
            alert_type='test',
            message='Test alert',
            severity='warning',
            status='active'
        )
        db.session.add(alert)
        db.session.commit()

        # 批量解决包含无效ID
        response = AlertService.batch_resolve([alert.id, 99999, 88888])
        assert response[1] == 200
        data = json.loads(response[0].data)
        assert data['data']['resolved_count'] == 1

    def test_batch_resolve_all_resolved(self, app_context):
        """测试批量解决已解决的告警"""
        from services.alert_service import AlertService
        from models.production import AlertRecord
        from database.db import db

        # 创建已解决的告警
        alert = AlertRecord(
            alert_code='ALERT-BATCH-RES',
            alert_type='test',
            message='Test alert',
            severity='warning',
            status='resolved'
        )
        db.session.add(alert)
        db.session.commit()

        response = AlertService.batch_resolve([alert.id])
        assert response[1] == 200
        data = json.loads(response[0].data)
        assert data['data']['resolved_count'] == 0

    def test_get_alert_statistics(self, app_context):
        """测试获取告警统计"""
        from services.alert_service import AlertService
        from models.production import AlertRecord
        from database.db import db

        # 创建不同严重程度和状态的告警
        severities = ['critical', 'error', 'warning', 'info']
        for severity in severities:
            for _ in range(3):
                alert = AlertRecord(
                    alert_code=f'ALERT-STAT-{severity}-{_}',
                    alert_type='test',
                    message=f'{severity} alert',
                    severity=severity,
                    status='active'
                )
                db.session.add(alert)
        
        # 添加一些已确认和已解决的告警
        for _ in range(2):
            ack_alert = AlertRecord(
                alert_code=f'ALERT-ACK-{_}',
                alert_type='test',
                message='Acknowledged',
                severity='warning',
                status='acknowledged'
            )
            res_alert = AlertRecord(
                alert_code=f'ALERT-RES-{_}',
                alert_type='test',
                message='Resolved',
                severity='info',
                status='resolved'
            )
            db.session.add(ack_alert)
            db.session.add(res_alert)
        
        db.session.commit()

        response = AlertService.get_alert_statistics()
        assert response[1] == 200
        data = json.loads(response[0].data)
        
        # 验证统计数据
        assert data['data']['total'] == 16  # 4*3 + 2 + 2
        assert data['data']['active'] == 12  # 4*3
        assert data['data']['acknowledged'] == 2
        assert data['data']['resolved'] == 2
        
        # 验证按严重程度统计
        by_severity = data['data']['by_severity']
        assert by_severity['critical'] == 3
        assert by_severity['error'] == 3
        assert by_severity['warning'] == 3
        assert by_severity['info'] == 3

    def test_get_alert_statistics_empty(self, app_context):
        """测试空数据库的告警统计"""
        from services.alert_service import AlertService

        response = AlertService.get_alert_statistics()
        assert response[1] == 200
        data = json.loads(response[0].data)
        
        assert data['data']['total'] == 0
        assert data['data']['active'] == 0
        assert data['data']['acknowledged'] == 0
        assert data['data']['resolved'] == 0
        
        by_severity = data['data']['by_severity']
        assert by_severity['critical'] == 0
        assert by_severity['error'] == 0
        assert by_severity['warning'] == 0
        assert by_severity['info'] == 0

    def test_create_alert_db_exception_rollback(self, app_context):
        """测试创建告警时数据库异常是否正确回滚"""
        from services.alert_service import AlertService
        from models.production import AlertRecord
        from database.db import db

        # 在commit前抛出异常
        with patch.object(db.session, 'commit', side_effect=Exception('DB error')):
            alert_data = {
                'alert_type': 'test',
                'message': 'Test alert'
            }
            with pytest.raises(Exception):
                AlertService.create_alert(alert_data)

        # 验证数据库中没有新增记录
        count = AlertRecord.query.count()
        assert count == 0

    def test_acknowledge_alert_db_exception_rollback(self, app_context):
        """测试确认告警时数据库异常是否正确回滚"""
        from services.alert_service import AlertService
        from models.production import AlertRecord
        from database.db import db

        alert = AlertRecord(
            alert_code='ALERT-ROLLBACK',
            alert_type='test',
            message='Test alert',
            severity='warning',
            status='active'
        )
        db.session.add(alert)
        db.session.commit()

        # 在commit前抛出异常
        with patch.object(db.session, 'commit', side_effect=Exception('DB error')):
            with pytest.raises(Exception):
                AlertService.acknowledge_alert(alert.id)

        # 重新查询验证状态未变化
        db.session.rollback()
        alert_after = AlertRecord.get_by_id(alert.id)
        assert alert_after.status == 'active'

    def test_resolve_alert_db_exception_rollback(self, app_context):
        """测试解决告警时数据库异常是否正确回滚"""
        from services.alert_service import AlertService
        from models.production import AlertRecord
        from database.db import db

        alert = AlertRecord(
            alert_code='ALERT-ROLLBACK-RES',
            alert_type='test',
            message='Test alert',
            severity='error',
            status='active'
        )
        db.session.add(alert)
        db.session.commit()

        # 在commit前抛出异常
        with patch.object(db.session, 'commit', side_effect=Exception('DB error')):
            with pytest.raises(Exception):
                AlertService.resolve_alert(alert.id)

        # 重新查询验证状态未变化
        db.session.rollback()
        alert_after = AlertRecord.get_by_id(alert.id)
        assert alert_after.status == 'active'

    def test_batch_resolve_db_exception_rollback(self, app_context):
        """测试批量解决告警时数据库异常是否正确回滚"""
        from services.alert_service import AlertService
        from models.production import AlertRecord
        from database.db import db

        # 创建多个告警
        alert_ids = []
        for i in range(3):
            alert = AlertRecord(
                alert_code=f'ALERT-BATCH-ROLLBACK-{i}',
                alert_type='test',
                message=f'Test alert {i}',
                severity='warning',
                status='active'
            )
            db.session.add(alert)
            db.session.flush()
            alert_ids.append(alert.id)
        db.session.commit()

        # 在commit前抛出异常
        with patch.object(db.session, 'commit', side_effect=Exception('DB error')):
            with pytest.raises(Exception):
                AlertService.batch_resolve(alert_ids)

        # 重新查询验证状态未变化
        db.session.rollback()
        for aid in alert_ids:
            alert = AlertRecord.get_by_id(aid)
            assert alert.status == 'active'


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
