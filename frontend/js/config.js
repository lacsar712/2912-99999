/**
 * 配置文件
 */
const Config = {
    // API基础URL
    API_BASE_URL: '/api',

    // 分页配置
    DEFAULT_PAGE_SIZE: 10,
    PAGE_SIZES: [10, 20, 50, 100],

    // Token存储键名
    TOKEN_KEY: 'token',
    USER_INFO_KEY: 'userInfo',

    // 应用名称
    APP_NAME: '数据管理系统',

    // 版本
    VERSION: '1.0.0'
};

// 冻结配置对象，防止修改
Object.freeze(Config);

// 全局可用
window.Config = Config;
