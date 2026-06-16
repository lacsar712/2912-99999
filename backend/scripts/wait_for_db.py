#!/usr/bin/env python3
"""
等待MySQL数据库就绪脚本
在启动后端服务前，检查数据库是否可连接且必要的表已初始化
"""

import os
import sys
import time
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_db_config():
    """从环境变量获取数据库配置"""
    config = {
        'host': os.environ.get('DB_HOST', 'mysql'),
        'port': int(os.environ.get('DB_PORT', 3306)),
        'user': os.environ.get('DB_USER', 'root'),
        'password': os.environ.get('DB_PASSWORD', ''),
        'database': os.environ.get('DB_NAME', 'production_system')
    }
    return config

def check_database():
    """检查数据库连接和表是否存在"""
    try:
        import pymysql
    except ImportError:
        logger.error("pymysql模块未安装，请安装pymysql")
        return False
    
    config = get_db_config()
    
    try:
        # 尝试连接数据库
        conn = pymysql.connect(
            host=config['host'],
            port=config['port'],
            user=config['user'],
            password=config['password'],
            database=config['database'],
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
        )
        
        with conn.cursor() as cursor:
            # 执行简单查询验证连接
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            logger.info("数据库连接成功")
            
            # 检查必要的表是否存在（例如 production_line 表）
            cursor.execute("""
                SELECT COUNT(*) as count 
                FROM information_schema.tables 
                WHERE table_schema = %s 
                AND table_name = 'production_line'
            """, (config['database'],))
            table_exists = cursor.fetchone()['count'] > 0
            
            if table_exists:
                logger.info("生产表已初始化")
            else:
                logger.warning("生产表未找到，等待初始化...")
                return False
        
        conn.close()
        return True
        
    except pymysql.Error as e:
        logger.warning("数据库连接失败: %s", e)
        return False
    except Exception as e:
        logger.error("未知错误: %s", e)
        return False

def main():
    """主函数，重试直到数据库就绪或超时"""
    max_retries = 30
    retry_interval = 2  # 秒
    
    logger.info("等待数据库就绪...")
    logger.info("数据库配置: host=%s, port=%s, database=%s", 
                os.environ.get('DB_HOST', 'mysql'),
                os.environ.get('DB_PORT', 3306),
                os.environ.get('DB_NAME', 'production_system'))
    
    for attempt in range(1, max_retries + 1):
        logger.info("尝试连接数据库 (第 %d/%d 次)...", attempt, max_retries)
        
        if check_database():
            logger.info("数据库已就绪，可以启动后端服务")
            sys.exit(0)
        
        if attempt < max_retries:
            logger.info("等待 %d 秒后重试...", retry_interval)
            time.sleep(retry_interval)
    
    logger.error("数据库等待超时，无法连接数据库")
    sys.exit(1)

if __name__ == "__main__":
    main()