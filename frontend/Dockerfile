# 数据管理系统 - 前端Dockerfile
FROM nginx:alpine

# 复制前端文件
COPY . /usr/share/nginx/html

# 复制nginx配置
COPY nginx.conf /etc/nginx/conf.d/default.conf

# 暴露端口
EXPOSE 80

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD wget -q --spider http://127.0.0.1/ || exit 1

# 启动nginx
CMD ["nginx", "-g", "daemon off;"]
