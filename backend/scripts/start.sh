#!/bin/bash
# 启动脚本：等待数据库就绪后启动后端服务

set -e

echo "=== 启动后端服务 ==="
echo "当前工作目录: $(pwd)"
echo "环境变量 DB_HOST: ${DB_HOST:-未设置}"

# 等待数据库就绪
echo "等待数据库就绪..."
python scripts/wait_for_db.py

if [ $? -eq 0 ]; then
    echo "数据库就绪检查通过"
else
    echo "数据库就绪检查失败，退出"
    exit 1
fi

# 检查数据库迁移（如果需要）
# 这里可以添加数据库迁移命令，例如：
# python manage.py db upgrade

# 启动Gunicorn
echo "启动Gunicorn服务器..."
exec gunicorn -w 4 -b 0.0.0.0:5000 \
    --access-logfile - \
    --error-logfile - \
    app:app