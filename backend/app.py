"""
生产线监控系统 - 应用入口
"""
import threading
import time
from datetime import datetime
from flask import Flask, jsonify
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

from config import Config
from database.db import db, init_db
from middleware.auth_middleware import AuthMiddleware
from middleware.error_handler import ErrorHandler

# 导入控制器
from controllers.auth_controller import auth_bp
from controllers.production_controller import production_bp
from controllers.simulation_controller import simulation_bp
from controllers.alert_controller import alert_bp
from controllers.safety_controller import safety_bp
from controllers.training_controller import training_bp
from controllers.spare_controller import spare_bp
from controllers.maintenance_controller import maintenance_bp
from controllers.disposal_controller import disposal_bp
from controllers.knowledge_controller import knowledge_bp
from controllers.env_monitor_controller import env_monitor_bp
from controllers.cost_controller import cost_bp
from controllers.video_monitor_controller import video_monitor_bp
from controllers.sop_controller import sop_bp

# 请求限制器 - 默认配置
limiter = None

# 调度任务运行状态
_scheduler_running = False


def start_scheduler(app):
    """启动后台调度线程 - 定时检查证书到期、资质合规、备件安全库存和环境监测数据生成"""
    global _scheduler_running
    if _scheduler_running:
        return
    _scheduler_running = True

    def scheduler_loop():
        with app.app_context():
            from services.training_service import TrainingService
            from services.spare_service import SparePartService
            from services.env_monitor_service import EnvMonitorService
            from utils.logger import logger
            counter = 0
            while True:
                try:
                    # 每5分钟生成环境监测模拟数据
                    logger.info(f"Scheduler running - env monitor simulation at {datetime.now()}")
                    try:
                        EnvMonitorService.generate_simulated_readings({
                            'interval': 5,
                            'abnormal_probability': 0.05
                        })
                    except Exception as e:
                        logger.warning(f"Env monitor simulation error: {e}")
                    
                    counter += 1
                    # 每12小时（144个5分钟周期）执行一次其他检查
                    if counter % 144 == 0:
                        logger.info(f"Scheduler running - certificate check at {datetime.now()}")
                        TrainingService.check_expiring_certificates(30)
                        TrainingService.check_all_qualifications()
                        logger.info(f"Scheduler running - spare low stock check at {datetime.now()}")
                        SparePartService.check_all_low_stock()
                        counter = 0
                except Exception as e:
                    logger.error(f"Scheduler task error: {e}")
                time.sleep(5 * 60)

    thread = threading.Thread(target=scheduler_loop, daemon=True, name="main-scheduler")
    thread.start()
    print("[Scheduler] Started background checker (env: 5min interval, others: 12h interval)")


def create_app(config_class=Config):
    """应用工厂函数"""
    global limiter
    app = Flask(__name__)
    app.config.from_object(config_class)

    # 初始化数据库
    init_db(app)

    # 初始化环境监测默认标准
    with app.app_context():
        from services.env_monitor_service import EnvMonitorService
        try:
            result = EnvMonitorService.init_default_standards()
            print(f"[Env Monitor] {result.get('message', 'Default standards initialized')}")
        except Exception as e:
            print(f"[Env Monitor] Failed to init default standards: {e}")

        # 初始化成本核算默认要素
        from services.cost_service import CostElementService
        try:
            result = CostElementService.init_default_elements()
            result_data = result[0].get_json() if hasattr(result[0], 'get_json') else {}
            created = result_data.get('data', {}).get('created', 0)
            print(f"[Cost] Default cost elements initialized, created {created} new elements")
        except Exception as e:
            print(f"[Cost] Failed to init default cost elements: {e}")

        # 初始化示例成本数据
        from services.cost_service import CostRecordService
        try:
            result = CostRecordService.init_sample_data()
            result_data = result[0].get_json() if hasattr(result[0], 'get_json') else {}
            created = result_data.get('data', {}).get('created', 0)
            if created > 0:
                print(f"[Cost] Sample cost data initialized, created {created} new records")
        except Exception as e:
            print(f"[Cost] Failed to init sample cost data: {e}")

    # 启用跨域
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    # 初始化请求限制器 - 根据环境配置
    if app.config.get('TESTING'):
        # 测试环境：使用内存存储并禁用
        limiter = Limiter(
            key_func=get_remote_address,
            default_limits=["200 per day", "50 per hour"],
            storage_uri="memory://"
        )
        limiter.init_app(app)
        limiter.enabled = False
    else:
        # 生产/开发环境：使用 Redis
        limiter = Limiter(
            key_func=get_remote_address,
            default_limits=["200 per day", "50 per hour"],
            storage_uri="redis://redis:6379/0"
        )
        limiter.init_app(app)

    # 注册中间件
    AuthMiddleware(app)
    ErrorHandler(app)

    # 注册蓝图
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(production_bp, url_prefix='/api/production')
    app.register_blueprint(simulation_bp, url_prefix='/api/simulation')
    app.register_blueprint(alert_bp, url_prefix='/api/alerts')
    app.register_blueprint(safety_bp, url_prefix='/api/safety')
    app.register_blueprint(training_bp, url_prefix='/api/training')
    app.register_blueprint(spare_bp, url_prefix='/api/spare')
    app.register_blueprint(maintenance_bp, url_prefix='/api/maintenance')
    app.register_blueprint(disposal_bp, url_prefix='/api/disposal')
    app.register_blueprint(knowledge_bp, url_prefix='/api/knowledge')
    app.register_blueprint(env_monitor_bp, url_prefix='/api/env-monitor')
    app.register_blueprint(cost_bp, url_prefix='/api/cost')
    app.register_blueprint(video_monitor_bp, url_prefix='/api/video-monitor')
    app.register_blueprint(sop_bp, url_prefix='/api/sop')

    # 启动后台调度线程（非测试环境）
    if not app.config.get('TESTING'):
        try:
            start_scheduler(app)
        except Exception as e:
            print(f"[Training Scheduler] Failed to start: {e}")

    # 健康检查
    @app.route('/health')
    @limiter.exempt
    def health_check():
        return jsonify({
            'status': 'healthy',
            'service': 'production-monitoring-system',
            'version': '1.0.0'
        })

    # 根路径
    @app.route('/')
    def index():
        return jsonify({
            'message': '生产线监控系统 API',
            'version': '1.0.0'
        })

    return app


if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=5000, debug=True)


# 创建Flask应用实例供gunicorn使用
app = create_app()
