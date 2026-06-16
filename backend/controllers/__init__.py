"""
控制器模块
"""
from .auth_controller import auth_bp
from .user_controller import user_bp
from .data_controller import data_bp
from .statistics_controller import stats_bp
from .config_controller import config_bp
from .production_controller import production_bp
from .simulation_controller import simulation_bp

__all__ = [
    'auth_bp',
    'user_bp',
    'data_bp',
    'stats_bp',
    'config_bp',
    'production_bp',
    'simulation_bp'
]
