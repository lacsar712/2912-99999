/**
 * 培训资质管理服务
 */
const TrainingService = {
    // 培训课程
    async getCourses(params = {}) {
        return await Request.get('/api/training/courses', params);
    },

    async getCourse(courseId) {
        return await Request.get(`/api/training/courses/${courseId}`);
    },

    async createCourse(data) {
        return await Request.post('/api/training/courses', data);
    },

    async updateCourse(courseId, data) {
        return await Request.put(`/api/training/courses/${courseId}`, data);
    },

    async deleteCourse(courseId) {
        return await Request.delete(`/api/training/courses/${courseId}`);
    },

    // 培训计划
    async getPlans(params = {}) {
        return await Request.get('/api/training/plans', params);
    },

    async getPlan(planId) {
        return await Request.get(`/api/training/plans/${planId}`);
    },

    async createPlan(data) {
        return await Request.post('/api/training/plans', data);
    },

    async updatePlan(planId, data) {
        return await Request.put(`/api/training/plans/${planId}`, data);
    },

    async deletePlan(planId) {
        return await Request.delete(`/api/training/plans/${planId}`);
    },

    // 参训记录
    async getAttendances(params = {}) {
        return await Request.get('/api/training/attendances', params);
    },

    async getAttendance(attId) {
        return await Request.get(`/api/training/attendances/${attId}`);
    },

    async createAttendance(data) {
        return await Request.post('/api/training/attendances', data);
    },

    async batchCreateAttendances(planId) {
        return await Request.post(`/api/training/attendances/batch?planId=${planId}`, {});
    },

    async updateAttendance(attId, data) {
        return await Request.put(`/api/training/attendances/${attId}`, data);
    },

    async signInAttendance(attId, data) {
        return await Request.post(`/api/training/attendances/${attId}/sign-in`, data);
    },

    async deleteAttendance(attId) {
        return await Request.delete(`/api/training/attendances/${attId}`);
    },

    // 资质证书
    async getCertificates(params = {}) {
        return await Request.get('/api/training/certificates', params);
    },

    async getCertificate(certId) {
        return await Request.get(`/api/training/certificates/${certId}`);
    },

    async createCertificate(data) {
        return await Request.post('/api/training/certificates', data);
    },

    async updateCertificate(certId, data) {
        return await Request.put(`/api/training/certificates/${certId}`, data);
    },

    async deleteCertificate(certId) {
        return await Request.delete(`/api/training/certificates/${certId}`);
    },

    async checkExpiringCertificates(days = 30) {
        return await Request.post(`/api/training/certificates/check-expiring?days=${days}`, {});
    },

    // 岗位资质要求
    async getPositionQualifications(params = {}) {
        return await Request.get('/api/training/position-qualifications', params);
    },

    async getPositionQualification(pqId) {
        return await Request.get(`/api/training/position-qualifications/${pqId}`);
    },

    async createPositionQualification(data) {
        return await Request.post('/api/training/position-qualifications', data);
    },

    async updatePositionQualification(pqId, data) {
        return await Request.put(`/api/training/position-qualifications/${pqId}`, data);
    },

    async deletePositionQualification(pqId) {
        return await Request.delete(`/api/training/position-qualifications/${pqId}`);
    },

    // 资质校验
    async checkUserQualification(userId) {
        return await Request.get(`/api/training/qualifications/check/${userId}`);
    },

    async checkAllQualifications() {
        return await Request.post('/api/training/qualifications/check-all', {});
    },

    async getQualificationMatrix() {
        return await Request.get('/api/training/qualifications/matrix');
    }
};

window.TrainingService = TrainingService;
