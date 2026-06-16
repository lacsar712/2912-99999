/**
 * HTTP请求封装模块
 */
const Request = {
    // 基础URL
    baseURL: Config.API_BASE_URL,

    // 请求拦截器
    interceptors: {
        request(config) {
            // 添加Token到请求头
            const token = Storage.getToken();
            console.log('[Request] Token from Storage:', token ? 'exists' : 'null/undefined');
            console.log('[Request] Token value:', token);
            if (token) {
                config.headers = config.headers || {};
                config.headers['Authorization'] = `Bearer ${token}`;
                console.log('[Request] Authorization header set');
            } else {
                console.log('[Request] No token found, Authorization header NOT set');
            }
            return config;
        },

        response(response) {
            // 处理401错误
            if (response.code === 401) {
                Storage.clearAuth();
                window.location.href = '/login.html';
                return Promise.reject(new Error('未授权'));
            }
            return response;
        }
    },

    /**
     * 通用请求方法
     * @param {string} method - HTTP方法
     * @param {string} url - 请求URL
     * @param {Object} data - 请求数据
     * @param {Object} options - 额外选项
     * @returns {Promise}
     */
    async request(method, url, data = null, options = {}) {
        const config = {
            method,
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            }
        };

        // 请求拦截
        this.interceptors.request(config);

        // 构建完整URL
        let fullURL = this.baseURL + url;

        // 处理GET请求参数
        if (data && method === 'GET') {
            const params = new URLSearchParams();
            Object.keys(data).forEach(key => {
                if (data[key] !== undefined && data[key] !== null) {
                    params.append(key, data[key]);
                }
            });
            const queryString = params.toString();
            if (queryString) {
                fullURL += '?' + queryString;
            }
        } else if (data && method !== 'GET') {
            config.body = JSON.stringify(data);
        }

        try {
            const response = await fetch(fullURL, config);
            const result = await response.json();
            return this.interceptors.response(result);
        } catch (error) {
            console.error('请求错误:', error);
            throw error;
        }
    },

    /**
     * GET请求
     */
    get(url, params) {
        return this.request('GET', url, params);
    },

    /**
     * POST请求
     */
    post(url, data) {
        return this.request('POST', url, data);
    },

    /**
     * PUT请求
     */
    put(url, data) {
        return this.request('PUT', url, data);
    },

    /**
     * DELETE请求
     */
    delete(url, data) {
        return this.request('DELETE', url, data);
    },

    /**
     * 文件上传请求
     */
    async upload(url, formData) {
        const config = {
            method: 'POST',
            headers: {}
        };

        // 请求拦截
        this.interceptors.request(config);

        // 构建完整URL
        const fullURL = this.baseURL + url;

        // 不要设置Content-Type，让浏览器自动设置边界
        delete config.headers['Content-Type'];

        config.body = formData;

        try {
            const response = await fetch(fullURL, config);
            const result = await response.json();
            return this.interceptors.response(result);
        } catch (error) {
            console.error('上传错误:', error);
            throw error;
        }
    }
};

// 全局可用
window.Request = Request;
