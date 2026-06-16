/**
 * 数据服务
 */
const DataService = {
    /**
     * 获取数据列表
     * @param {Object} params - 查询参数
     * @returns {Promise}
     */
    async getList(params = {}) {
        return await Request.get('/data', params);
    },

    /**
     * 根据ID获取数据
     * @param {number} id - 数据ID
     * @returns {Promise}
     */
    async getById(id) {
        return await Request.get(`/data/${id}`);
    },

    /**
     * 创建数据
     * @param {Object} data - 数据
     * @returns {Promise}
     */
    async create(data) {
        return await Request.post('/data', data);
    },

    /**
     * 更新数据
     * @param {number} id - 数据ID
     * @param {Object} data - 更新数据
     * @returns {Promise}
     */
    async update(id, data) {
        return await Request.put(`/data/${id}`, data);
    },

    /**
     * 删除数据
     * @param {number} id - 数据ID
     * @returns {Promise}
     */
    async delete(id) {
        return await Request.delete(`/data/${id}`);
    },

    /**
     * 批量删除数据
     * @param {Array} ids - ID数组
     * @returns {Promise}
     */
    async batchDelete(ids) {
        return await Request.delete('/data/batch', { ids });
    },

    /**
     * 获取数据类型列表
     * @returns {Promise}
     */
    async getTypes() {
        return await Request.get('/data/types');
    }
};

// 全局可用
window.DataService = DataService;
