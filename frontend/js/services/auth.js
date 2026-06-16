/**
 * 认证服务
 */
const AuthService = {
    /**
     * 用户登录
     * @param {string} username - 用户名
     * @param {string} password - 密码
     * @returns {Promise}
     */
    async login(username, password) {
        const response = await Request.post('/auth/login', {
            username,
            password
        });

        console.log('[Auth] Login response:', response);
        console.log('[Auth] response.code:', response.code);
        console.log('[Auth] response.data:', response.data);

        if (response.code === 200 && response.data) {
            console.log('[Auth] Token to store:', response.data.token);
            Storage.setToken(response.data.token);
            Storage.setUserInfo(response.data.userInfo);
            console.log('[Auth] Token stored, verifying...');
            const storedToken = Storage.getToken();
            console.log('[Auth] Stored token retrieved:', storedToken ? 'exists' : 'null');
        }

        return response;
    },

    /**
     * 用户注册
     * @param {Object} data - 注册数据
     * @returns {Promise}
     */
    async register(data) {
        return await Request.post('/auth/register', data);
    },

    /**
     * 用户登出
     * @returns {Promise}
     */
    async logout() {
        try {
            await Request.post('/auth/logout');
        } finally {
            Storage.clearAuth();
        }
    },

    /**
     * 修改密码
     * @param {string} oldPassword - 原密码
     * @param {string} newPassword - 新密码
     * @returns {Promise}
     */
    async changePassword(oldPassword, newPassword) {
        return await Request.post('/auth/change-password', {
            oldPassword,
            newPassword
        });
    },

    /**
     * 检查是否已登录
     * @returns {boolean}
     */
    isLoggedIn() {
        return !!Storage.getToken();
    },

    /**
     * 获取当前用户信息
     * @returns {Object|null}
     */
    getCurrentUser() {
        return Storage.getUserInfo();
    },

    /**
     * 检查是否为管理员
     * @returns {boolean}
     */
    isAdmin() {
        const user = this.getCurrentUser();
        return user && user.role === 'admin';
    }
};

// 全局可用
window.AuthService = AuthService;
