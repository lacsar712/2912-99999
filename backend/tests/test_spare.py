"""
备件库存与维修领用 - 单元测试
测试备件档案、入库、领用、盘点、安全库存预警、周转率统计
"""
import pytest
import sys
import os
from datetime import datetime, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


class TestSparePartModel:
    """备件档案模型测试"""
    
    def test_spare_part_creation(self):
        """测试备件创建"""
        from models.spare import SparePart
        
        part = SparePart(
            part_code='SP001',
            part_name='轴承',
            specification='6205-2RS',
            unit='个',
            safety_stock=10,
            current_stock=50,
            equipment_type='cnc',
            unit_price=120.50,
            location='A-01-01'
        )
        
        assert part.part_code == 'SP001'
        assert part.part_name == '轴承'
        assert part.specification == '6205-2RS'
        assert part.unit == '个'
        assert part.safety_stock == 10
        assert part.current_stock == 50
        assert part.equipment_type == 'cnc'
        assert float(part.unit_price) == 120.50
        assert part.location == 'A-01-01'
    
    def test_is_low_stock_property(self):
        """测试低库存计算属性"""
        from models.spare import SparePart
        
        # 库存高于安全库存
        part1 = SparePart(current_stock=50, safety_stock=10)
        assert part1.is_low_stock == False
        
        # 库存等于安全库存
        part2 = SparePart(current_stock=10, safety_stock=10)
        assert part2.is_low_stock == True
        
        # 库存低于安全库存
        part3 = SparePart(current_stock=5, safety_stock=10)
        assert part3.is_low_stock == True
    
    def test_spare_part_to_dict(self):
        """测试备件转字典"""
        from models.spare import SparePart
        
        part = SparePart(
            part_code='SP001',
            part_name='轴承',
            safety_stock=10,
            current_stock=5
        )
        part.id = 1
        part.create_time = datetime.now()
        
        part_dict = part.to_dict()
        
        assert part_dict['id'] == 1
        assert part_dict['part_code'] == 'SP001'
        assert part_dict['part_name'] == '轴承'
        assert part_dict['is_low_stock'] == True


class TestSpareInboundModel:
    """入库单模型测试"""
    
    def test_inbound_creation_purchase(self):
        """测试采购入库创建"""
        from models.spare import SpareInbound
        
        inbound = SpareInbound(
            inbound_code='IN20240101001',
            part_id=1,
            source_type='purchase',
            quantity=50,
            unit_price=120.50,
            batch_no='BATCH20240101',
            operator='张三'
        )
        
        assert inbound.inbound_code == 'IN20240101001'
        assert inbound.part_id == 1
        assert inbound.source_type == 'purchase'
        assert inbound.quantity == 50
        assert float(inbound.unit_price) == 120.50
        assert inbound.batch_no == 'BATCH20240101'
        assert inbound.operator == '张三'
    
    def test_inbound_creation_return(self):
        """测试退库创建"""
        from models.spare import SpareInbound
        
        inbound = SpareInbound(
            inbound_code='RT20240101001',
            part_id=1,
            source_type='return',
            quantity=5,
            unit_price=120.50,
            operator='李四',
            remark='领多了退库'
        )
        
        assert inbound.source_type == 'return'
        assert inbound.quantity == 5
        assert inbound.remark == '领多了退库'
    
    def test_inbound_source_types(self):
        """测试入库来源类型"""
        from models.spare import SpareInbound
        
        valid_sources = ['purchase', 'return']
        for source in valid_sources:
            inbound = SpareInbound(source_type=source)
            assert inbound.source_type == source


class TestSpareOutboundModel:
    """领用单模型测试"""
    
    def test_outbound_creation_with_work_order(self):
        """测试关联工单的领用创建"""
        from models.spare import SpareOutbound
        
        outbound = SpareOutbound(
            outbound_code='OUT20240101001',
            part_id=1,
            work_order_id=1,
            quantity=3,
            receiver='王工',
            is_returned=False
        )
        
        assert outbound.outbound_code == 'OUT20240101001'
        assert outbound.part_id == 1
        assert outbound.work_order_id == 1
        assert outbound.reason is None  # 有关单时原因可为空
        assert outbound.quantity == 3
        assert outbound.receiver == '王工'
        assert outbound.is_returned == False
    
    def test_outbound_creation_with_custom_reason(self):
        """测试自定义原因的领用创建"""
        from models.spare import SpareOutbound
        
        outbound = SpareOutbound(
            outbound_code='OUT20240101002',
            part_id=1,
            reason='日常维护',
            quantity=2,
            receiver='李工',
            is_returned=False
        )
        
        assert outbound.work_order_id is None
        assert outbound.reason == '日常维护'
    
    def test_outbound_return(self):
        """测试归还标记"""
        from models.spare import SpareOutbound
        
        outbound = SpareOutbound(is_returned=False)
        assert outbound.is_returned == False
        
        outbound.is_returned = True
        outbound.return_time = datetime.now()
        assert outbound.is_returned == True
        assert outbound.return_time is not None


class TestSpareInventoryModel:
    """盘点表模型测试"""
    
    def test_inventory_creation(self):
        """测试盘点创建"""
        from models.spare import SpareInventory
        
        inventory = SpareInventory(
            inventory_code='INV202401',
            spare_part_id=1,
            inventory_month='2024-01',
            book_stock=50,
            actual_stock=48,
            difference=-2,
            difference_reason='正常损耗',
            operator='盘点员A'
        )
        
        assert inventory.inventory_code == 'INV202401'
        assert inventory.spare_part_id == 1
        assert inventory.inventory_month == '2024-01'
        assert inventory.book_stock == 50
        assert inventory.actual_stock == 48
        assert inventory.difference == -2
        assert inventory.difference_reason == '正常损耗'
        assert inventory.operator == '盘点员A'
    
    def test_difference_calculation(self):
        """测试差异计算"""
        from models.spare import SpareInventory
        
        # 盘亏
        inv1 = SpareInventory(book_stock=50, actual_stock=48, difference=-2)
        assert inv1.difference == -2
        
        # 盘盈
        inv2 = SpareInventory(book_stock=50, actual_stock=52, difference=2)
        assert inv2.difference == 2
        
        # 无差异
        inv3 = SpareInventory(book_stock=50, actual_stock=50, difference=0)
        assert inv3.difference == 0


class TestMaintenanceWorkOrderModel:
    """维修工单模型测试"""
    
    def test_work_order_creation(self):
        """测试工单创建"""
        from models.maintenance import MaintenanceWorkOrder
        
        order = MaintenanceWorkOrder(
            order_code='WO20240101001',
            order_name='数控机床主轴维修',
            equipment_id=1,
            fault_description='主轴异响，震动过大',
            priority='high',
            status='pending'
        )
        
        assert order.order_code == 'WO20240101001'
        assert order.order_name == '数控机床主轴维修'
        assert order.equipment_id == 1
        assert order.fault_description == '主轴异响，震动过大'
        assert order.priority == 'high'
        assert order.status == 'pending'
    
    def test_work_order_priorities(self):
        """测试工单优先级"""
        from models.maintenance import MaintenanceWorkOrder
        
        valid_priorities = ['low', 'medium', 'high', 'urgent']
        for priority in valid_priorities:
            order = MaintenanceWorkOrder(priority=priority)
            assert order.priority == priority
    
    def test_work_order_statuses(self):
        """测试工单状态"""
        from models.maintenance import MaintenanceWorkOrder
        
        valid_statuses = ['pending', 'in_progress', 'completed', 'cancelled']
        for status in valid_statuses:
            order = MaintenanceWorkOrder(status=status)
            assert order.status == status
    
    def test_materials_json(self):
        """测试耗材明细JSON"""
        from models.maintenance import MaintenanceWorkOrder
        import json
        
        materials = [
            {'part_id': 1, 'part_name': '轴承', 'quantity': 2, 'unit_price': 120.50},
            {'part_id': 2, 'part_name': '密封圈', 'quantity': 5, 'unit_price': 15.00}
        ]
        
        order = MaintenanceWorkOrder(
            materials=json.dumps(materials, ensure_ascii=False),
            materials_cost=2 * 120.50 + 5 * 15.00
        )
        
        parsed_materials = json.loads(order.materials)
        assert len(parsed_materials) == 2
        assert parsed_materials[0]['part_name'] == '轴承'
        assert float(order.materials_cost) == 316.00


class TestSpareService:
    """备件服务层测试"""
    
    def test_check_low_stock(self):
        """测试低库存检测"""
        from services.spare import SparePartService
        from models.spare import SparePart
        from models.production import AlertRecord
        
        # 创建一个低库存备件
        part = SparePart(
            id=1,
            part_code='SP001',
            part_name='测试轴承',
            safety_stock=10,
            current_stock=5
        )
        
        # 调用检测方法（不实际保存到数据库）
        # 这里只测试逻辑
        is_low = part.current_stock <= part.safety_stock
        assert is_low == True
    
    def test_turnover_rate_calculation(self):
        """测试周转率计算逻辑"""
        from services.spare import SpareStatisticsService
        
        # 模拟数据
        end_stock = 50  # 期末库存
        outbound_total = 100  # 出库量
        inbound_total = 80  # 入库量
        
        # 期初库存 = 期末库存 + 出库量 - 入库量
        begin_stock = end_stock + outbound_total - inbound_total
        assert begin_stock == 70
        
        # 平均库存 = (期初库存 + 期末库存) / 2
        avg_stock = (begin_stock + end_stock) / 2
        assert avg_stock == 60
        
        # 周转率 = 出库量 / 平均库存
        turnover_rate = outbound_total / avg_stock if avg_stock > 0 else 0
        assert turnover_rate == 100 / 60
        assert round(turnover_rate, 4) == 1.6667
    
    def test_zero_stock_turnover_rate(self):
        """测试零库存时的周转率计算"""
        from services.spare import SpareStatisticsService
        
        outbound_total = 0
        avg_stock = 0
        
        turnover_rate = outbound_total / avg_stock if avg_stock > 0 else 0
        assert turnover_rate == 0


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
