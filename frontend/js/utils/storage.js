/**
 * 本地存储封装模块
 */
const Storage = {
    /**
     * 存储数据
     * @param {string} key - 键名
     * @param {*} value - 值
     */
    set(key, value) {
        try {
            const data = JSON.stringify(value);
            localStorage.setItem(key, data);
        } catch (error) {
            console.error('存储数据失败:', error);
        }
    },

    /**
     * 获取数据
     * @param {string} key - 键名
     * @param {*} defaultValue - 默认值
     * @returns {*}
     */
    get(key, defaultValue = null) {
        try {
            const data = localStorage.getItem(key);
            return data ? JSON.parse(data) : defaultValue;
        } catch (error) {
            console.error('获取数据失败:', error);
            return defaultValue;
        }
    },

    /**
     * 删除数据
     * @param {string} key - 键名
     */
    remove(key) {
        localStorage.removeItem(key);
    },

    /**
     * 清空所有数据
     */
    clear() {
        localStorage.clear();
    },

    /**
     * 存储Token
     * @param {string} token
     */
    setToken(token) {
        console.log('[Storage] setToken called with:', token);
        console.log('[Storage] Config.TOKEN_KEY:', Config.TOKEN_KEY);
        this.set(Config.TOKEN_KEY, token);
        console.log('[Storage] Token stored, verifying...');
        const stored = localStorage.getItem(Config.TOKEN_KEY);
        console.log('[Storage] Raw stored value:', stored);
    },

    /**
     * 获取Token
     * @returns {string|null}
     */
    getToken() {
        console.log('[Storage] getToken called');
        console.log('[Storage] Config.TOKEN_KEY:', Config.TOKEN_KEY);
        const rawValue = localStorage.getItem(Config.TOKEN_KEY);
        console.log('[Storage] Raw localStorage value:', rawValue);
        
        if (!rawValue) {
            return null;
        }
        
        // 尝试JSON解析
        try {
            const parsed = JSON.parse(rawValue);
            console.log('[Storage] Parsed token:', parsed);
            return parsed;
        } catch (error) {
            console.log('[Storage] JSON解析失败，返回原始字符串');
            // 如果解析失败，可能是纯字符串token，直接返回
            return rawValue;
        }
    },

    /**
     * 存储用户信息
     * @param {Object} userInfo
     */
    setUserInfo(userInfo) {
        this.set(Config.USER_INFO_KEY, userInfo);
    },

    /**
     * 获取用户信息
     * @returns {Object|null}
     */
    getUserInfo() {
        return this.get(Config.USER_INFO_KEY);
    },

    /**
     * 清除登录信息
     */
    clearAuth() {
        this.remove(Config.TOKEN_KEY);
        this.remove(Config.USER_INFO_KEY);
    }
};

// 全局可用
window.Storage = Storage;
