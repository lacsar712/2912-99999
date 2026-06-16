/**
 * 培训资质管理页面
 */
const TrainingPage = {
    activeTab: 'courses',
    courses: [],
    plans: [],
    attendances: [],
    certificates: [],
    positionQualifications: [],
    users: [],
    matrixData: null,
    calendarDate: new Date(),
    _activeModal: null,

    init() {
        this.activeTab = 'courses';
        this.calendarDate = new Date();
        this.render();
        this.loadTabData();
        this.startAutoCheck();
    },

    destroy() {
        this.closeModal();
        if (this._autoCheckInterval) clearInterval(this._autoCheckInterval);
    },

    startAutoCheck() {
        const doCheck = async () => {
            try {
                await TrainingService.checkExpiringCertificates(30);
                await TrainingService.checkAllQualifications();
            } catch (e) {}
        };
        doCheck();
        this._autoCheckInterval = setInterval(doCheck, 30 * 60 * 1000);
    },

    openModal(options) {
        this._activeModal = new Modal(options);
        this._activeModal.show();
        return this._activeModal;
    },

    closeModal() {
        if (this._activeModal) {
            this._activeModal.close();
            this._activeModal = null;
        }
    },

    formatDate(dateStr, format = 'YYYY-MM-DD') {
        if (!dateStr) return '';
        return Formatter.formatDate(dateStr, format);
    },

    getDaysToExpiry(expiryDateStr) {
        if (!expiryDateStr) return null;
        const expiry = new Date(expiryDateStr);
        const now = new Date();
        now.setHours(0, 0, 0, 0);
        expiry.setHours(0, 0, 0, 0);
        const diff = Math.floor((expiry - now) / (1000 * 60 * 60 * 24));
        return diff;
    },

    getExpiryBadge(daysToExpiry) {
        if (daysToExpiry === null || daysToExpiry === undefined) return '';
        if (daysToExpiry < 0) {
            return `<span class="status-badge" style="background:rgba(220,53,69,0.1);color:#dc3545;">已过期 ${Math.abs(daysToExpiry)} 天</span>`;
        } else if (daysToExpiry <= 30) {
            return `<span class="status-badge" style="background:rgba(255,193,7,0.1);color:#856404;">即将过期 ${daysToExpiry} 天</span>`;
        } else {
            return `<span class="status-badge" style="background:rgba(40,167,69,0.1);color:#28a745;">正常 ${daysToExpiry} 天</span>`;
        }
    },

    handleFileUpload(e, previewId, storageKey) {
        const file = e.target.files[0];
        if (!file) return;
        const reader = new FileReader();
        reader.onload = (ev) => {
            const base64 = ev.target.result.split(',')[1];
            this[storageKey] = base64;
            const preview = document.getElementById(previewId);
            if (preview) {
                preview.innerHTML = `<img src="${ev.target.result}" class="photo-preview">`;
            }
        };
        reader.readAsDataURL(file);
    },

    render() {
        const container = document.getElementById('pageContainer');
        container.innerHTML = `
            <div class="card">
                <div class="card-header">
                    <h3 class="card-title">培训资质管理</h3>
                </div>
                <div class="card-body">
                    <div class="safety-tab-bar">
                        <div class="safety-tab active" data-tab="courses">课程库</div>
                        <div class="safety-tab" data-tab="plans">培训计划日历</div>
                        <div class="safety-tab" data-tab="attendances">参训签到与成绩</div>
                        <div class="safety-tab" data-tab="cards">员工资质卡片</div>
                        <div class="safety-tab" data-tab="matrix">岗位资质矩阵</div>
                    </div>
                    <div id="trainingTabContent"></div>
                </div>
            </div>
        `;
        this.setupTabListeners();
    },

    setupTabListeners() {
        document.querySelectorAll('.safety-tab').forEach(tab => {
            tab.addEventListener('click', () => {
                document.querySelectorAll('.safety-tab').forEach(t => t.classList.remove('active'));
                tab.classList.add('active');
                this.activeTab = tab.dataset.tab;
                this.loadTabData();
            });
        });
    },

    async loadTabData() {
        switch (this.activeTab) {
            case 'courses': await this.loadCourses(); break;
            case 'plans': await this.loadPlans(); break;
            case 'attendances': await this.loadAttendances(); break;
            case 'cards':
                await this.loadCertificates();
                await this.loadUsers();
                this.renderQualificationCards();
                break;
            case 'matrix':
                await this.loadPositionQualifications();
                await this.loadMatrix();
                break;
        }
    },

    // ==================== Tab 1: 课程库 ====================

    async loadCourses() {
        try {
            const res = await TrainingService.getCourses({ size: 200 });
            if (res.code === 200) {
                this.courses = res.data.items || [];
            }
        } catch (e) {
            Toast.error('加载课程数据失败');
        }
        this.renderCourses();
    },

    renderCourses() {
        const content = document.getElementById('trainingTabContent');
        const categories = ['安全', '技能', '管理', '其他'];
        const assessmentMap = { exam: '考试', practice: '实操', paper: '论文', attendance: '考勤' };

        content.innerHTML = `
            <div style="margin-bottom:16px;display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:8px;">
                <div>
                    <select class="form-control" id="courseCategoryFilter" style="width:120px;display:inline-block;">
                        <option value="">全部类别</option>
                        ${categories.map(c => `<option value="${c}">${c}</option>`).join('')}
                    </select>
                    <input type="text" class="form-control" id="courseNameSearch" placeholder="搜索课程名称" style="width:200px;display:inline-block;margin-left:8px;">
                </div>
                <button class="btn btn-primary" id="addCourseBtn">+ 新增课程</button>
            </div>
            <div id="coursesTableWrap">
                ${this.courses.length === 0 ? '<div style="text-align:center;padding:40px;color:var(--text-secondary);">暂无课程数据</div>' : `
                <table class="data-table">
                    <thead>
                        <tr>
                            <th>课程编号</th>
                            <th>课程名称</th>
                            <th>类别</th>
                            <th>讲师</th>
                            <th>计划时长(h)</th>
                            <th>考核形式</th>
                            <th>操作</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${this.courses.map(c => `
                            <tr>
                                <td>${c.course_code || '-'}</td>
                                <td>${c.course_name || '-'}</td>
                                <td>${c.category || '-'}</td>
                                <td>${c.lecturer || '-'}</td>
                                <td>${c.planned_duration != null ? c.planned_duration : '-'}</td>
                                <td>${assessmentMap[c.assessment_form] || c.assessment_form || '-'}</td>
                                <td>
                                    <button class="btn btn-sm btn-outline" onclick="TrainingPage.openCourseModal(${c.id})">编辑</button>
                                    <button class="btn btn-sm btn-danger" onclick="TrainingPage.deleteCourse(${c.id})">删除</button>
                                </td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
                `}
            </div>
        `;

        document.getElementById('addCourseBtn')?.addEventListener('click', () => this.openCourseModal());
        document.getElementById('courseCategoryFilter')?.addEventListener('change', () => this.filterCourses());
        document.getElementById('courseNameSearch')?.addEventListener('input', () => this.filterCourses());
    },

    async filterCourses() {
        const category = document.getElementById('courseCategoryFilter')?.value;
        const name = (document.getElementById('courseNameSearch')?.value || '').toLowerCase().trim();
        try {
            const res = await TrainingService.getCourses({
                size: 200,
                category: category || undefined
            });
            if (res.code === 200) {
                let items = res.data.items || [];
                if (name) {
                    items = items.filter(c =>
                        (c.course_name || '').toLowerCase().includes(name) ||
                        (c.course_code || '').toLowerCase().includes(name)
                    );
                }
                this.courses = items;
            }
        } catch (e) {
            Toast.error('筛选失败');
        }
        this.renderCourses();
    },

    openCourseModal(courseId = null) {
        const isEdit = courseId !== null;
        let course = {};
        if (isEdit) {
            course = this.courses.find(c => c.id === courseId) || {};
        }
        this._pendingCourseFileBase64 = null;

        const categories = [
            { value: '安全', label: '安全' },
            { value: '技能', label: '技能' },
            { value: '管理', label: '管理' },
            { value: '其他', label: '其他' }
        ];
        const assessments = [
            { value: 'exam', label: '考试' },
            { value: 'practice', label: '实操' },
            { value: 'paper', label: '论文' },
            { value: 'attendance', label: '考勤' }
        ];

        this.openModal({
            title: isEdit ? '编辑课程' : '新增课程',
            width: '600px',
            content: `
                <form id="courseForm">
                    <div class="form-group">
                        <label>课程编号 *</label>
                        <input type="text" class="form-control" name="course_code" value="${course.course_code || ''}" required>
                    </div>
                    <div class="form-group">
                        <label>课程名称 *</label>
                        <input type="text" class="form-control" name="course_name" value="${course.course_name || ''}" required>
                    </div>
                    <div class="form-group">
                        <label>类别</label>
                        <select class="form-control" name="category">
                            <option value="">请选择</option>
                            ${categories.map(c => `<option value="${c.value}" ${course.category === c.value ? 'selected' : ''}>${c.label}</option>`).join('')}
                        </select>
                    </div>
                    <div class="form-group">
                        <label>讲师</label>
                        <input type="text" class="form-control" name="lecturer" value="${course.lecturer || ''}">
                    </div>
                    <div class="form-group">
                        <label>计划时长(h)</label>
                        <input type="number" class="form-control" name="planned_duration" step="0.5" value="${course.planned_duration || ''}">
                    </div>
                    <div class="form-group">
                        <label>考核形式</label>
                        <select class="form-control" name="assessment_form">
                            <option value="">请选择</option>
                            ${assessments.map(a => `<option value="${a.value}" ${course.assessment_form === a.value ? 'selected' : ''}>${a.label}</option>`).join('')}
                        </select>
                    </div>
                    <div class="form-group">
                        <label>课程描述</label>
                        <textarea class="form-control" name="description" rows="3">${course.description || ''}</textarea>
                    </div>
                    <div class="form-group">
                        <label>附件</label>
                        <input type="file" id="courseFileInput" class="form-control">
                        <div id="courseFilePreview" style="margin-top:8px;">
                            ${course.attachment_base64 ? `<img src="data:image/jpeg;base64,${course.attachment_base64}" class="photo-preview">` : ''}
                        </div>
                    </div>
                </form>
            `,
            onConfirm: async () => {
                const form = document.getElementById('courseForm');
                const data = {
                    course_code: form.course_code.value,
                    course_name: form.course_name.value,
                    category: form.category.value || null,
                    lecturer: form.lecturer.value || null,
                    planned_duration: form.planned_duration.value ? parseFloat(form.planned_duration.value) : null,
                    assessment_form: form.assessment_form.value || null,
                    description: form.description.value || null,
                    attachment_base64: this._pendingCourseFileBase64 || course.attachment_base64 || null
                };
                if (!data.course_code || !data.course_name) {
                    Toast.error('请填写课程编号和名称');
                    return false;
                }
                return await this.saveCourse(isEdit ? courseId : null, data);
            }
        });

        setTimeout(() => {
            const fileInput = document.getElementById('courseFileInput');
            if (fileInput) {
                fileInput.addEventListener('change', (e) => this.handleFileUpload(e, 'courseFilePreview', '_pendingCourseFileBase64'));
            }
        }, 100);
    },

    async saveCourse(id, data) {
        try {
            let res;
            if (id) {
                res = await TrainingService.updateCourse(id, data);
            } else {
                res = await TrainingService.createCourse(data);
            }
            if (res.code === 200 || res.code === 201) {
                Toast.show(id ? '更新成功' : '创建成功', 'success');
                this.loadCourses();
                return true;
            } else {
                Toast.error(res.message || '操作失败');
                return false;
            }
        } catch (e) {
            Toast.error('操作失败');
            return false;
        }
    },

    async deleteCourse(id) {
        const confirmed = await Modal.confirm('确定要删除该课程吗？');
        if (!confirmed) return;
        try {
            const res = await TrainingService.deleteCourse(id);
            if (res.code === 200) {
                Toast.show('删除成功', 'success');
                this.loadCourses();
            } else {
                Toast.error(res.message || '删除失败');
            }
        } catch (e) {
            Toast.error('删除失败');
        }
    },

    // ==================== Tab 2: 培训计划日历 ====================

    async loadPlans() {
        try {
            const res = await TrainingService.getPlans({ size: 200 });
            if (res.code === 200) {
                this.plans = res.data.items || [];
            }
        } catch (e) {
            Toast.error('加载培训计划失败');
        }
        this.renderPlansCalendar();
    },

    renderPlansCalendar() {
        const content = document.getElementById('trainingTabContent');
        const year = this.calendarDate.getFullYear();
        const month = this.calendarDate.getMonth();
        const firstDay = new Date(year, month, 1);
        const lastDay = new Date(year, month + 1, 0);
        const startWeekday = firstDay.getDay();
        const daysInMonth = lastDay.getDate();

        const statusColorMap = {
            draft: '#6c757d',
            published: '#007bff',
            ongoing: '#28a745',
            completed: '#6f42c1',
            cancelled: '#dc3545'
        };
        const statusLabelMap = {
            draft: '草稿',
            published: '已发布',
            ongoing: '进行中',
            completed: '已完成',
            cancelled: '已取消'
        };

        const monthNames = ['1月', '2月', '3月', '4月', '5月', '6月', '7月', '8月', '9月', '10月', '11月', '12月'];
        const weekdays = ['日', '一', '二', '三', '四', '五', '六'];

        const today = new Date();
        today.setHours(0, 0, 0, 0);

        const cells = [];
        for (let i = 0; i < startWeekday; i++) {
            cells.push('<div class="calendar-cell other-month"></div>');
        }

        for (let day = 1; day <= daysInMonth; day++) {
            const dateStr = `${year}-${String(month + 1).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
            const currentDate = new Date(year, month, day);
            const isToday = currentDate.getTime() === today.getTime();

            const dayPlans = this.plans.filter(p => {
                const start = p.start_time ? new Date(p.start_time).toISOString().split('T')[0] : '';
                const end = p.end_time ? new Date(p.end_time).toISOString().split('T')[0] : '';
                return start === dateStr || end === dateStr || (start <= dateStr && end >= dateStr);
            });

            cells.push(`
                <div class="calendar-cell ${isToday ? 'today' : ''}" data-date="${dateStr}" style="min-height:80px;border:1px solid var(--border-color,#dee2e6);padding:6px;cursor:pointer;position:relative;">
                    <div style="font-weight:${isToday ? 'bold' : 'normal'};color:${isToday ? '#007bff' : 'inherit'};">${day}</div>
                    <div style="margin-top:4px;">
                        ${dayPlans.slice(0, 3).map(p => {
                            const shortName = (p.plan_name || '').substring(0, 8);
                            const color = statusColorMap[p.status] || '#6c757d';
                            return `<div style="background:${color};color:white;font-size:11px;padding:2px 4px;border-radius:3px;margin-bottom:2px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;" 
                                title="${p.plan_name || ''} (${statusLabelMap[p.status] || p.status || ''})"
                                onclick="event.stopPropagation();TrainingPage.openPlanModal(${p.id})">${shortName}</div>`;
                        }).join('')}
                        ${dayPlans.length > 3 ? `<div style="font-size:11px;color:var(--text-secondary);">+${dayPlans.length - 3} 更多</div>` : ''}
                    </div>
                </div>
            `);
        }

        const totalCells = startWeekday + daysInMonth;
        const remaining = totalCells % 7 === 0 ? 0 : 7 - (totalCells % 7);
        for (let i = 0; i < remaining; i++) {
            cells.push('<div class="calendar-cell other-month"></div>');
        }

        content.innerHTML = `
            <div style="margin-bottom:16px;display:flex;justify-content:space-between;align-items:center;">
                <div style="display:flex;align-items:center;gap:8px;">
                    <button class="btn btn-outline" id="prevMonthBtn">← 上月</button>
                    <h4 style="margin:0 16px;">${year}年 ${monthNames[month]}</h4>
                    <button class="btn btn-outline" id="nextMonthBtn">下月 →</button>
                </div>
                <div style="display:flex;align-items:center;gap:8px;">
                    <div style="display:flex;gap:12px;font-size:12px;">
                        ${Object.entries(statusColorMap).map(([s, c]) => `<span style="display:flex;align-items:center;gap:4px;"><span style="width:12px;height:12px;background:${c};border-radius:2px;display:inline-block;"></span>${statusLabelMap[s]}</span>`).join('')}
                    </div>
                    <button class="btn btn-primary" id="addPlanBtn">+ 新增计划</button>
                </div>
            </div>
            <div style="display:grid;grid-template-columns:repeat(7,1fr);gap:1px;background:var(--border-color,#dee2e6);">
                ${weekdays.map(w => `<div style="background:var(--bg-light,#f8f9fa);padding:8px;text-align:center;font-weight:500;">${w}</div>`).join('')}
            </div>
            <div style="display:grid;grid-template-columns:repeat(7,1fr);gap:1px;background:var(--border-color,#dee2e6);">
                ${cells.join('')}
            </div>
        `;

        document.getElementById('prevMonthBtn')?.addEventListener('click', () => this.changeCalendarMonth(-1));
        document.getElementById('nextMonthBtn')?.addEventListener('click', () => this.changeCalendarMonth(1));
        document.getElementById('addPlanBtn')?.addEventListener('click', () => this.openPlanModal());

        content.querySelectorAll('.calendar-cell[data-date]').forEach(cell => {
            cell.addEventListener('click', () => {
                const date = cell.dataset.date;
                this.openPlanModal(null, date);
            });
        });
    },

    changeCalendarMonth(delta) {
        this.calendarDate.setMonth(this.calendarDate.getMonth() + delta);
        this.renderPlansCalendar();
    },

    openPlanModal(planId = null, defaultDate = null) {
        const isEdit = planId !== null;
        let plan = {};
        if (isEdit) {
            plan = this.plans.find(p => p.id === planId) || {};
        }

        const statuses = [
            { value: 'draft', label: '草稿' },
            { value: 'published', label: '已发布' },
            { value: 'ongoing', label: '进行中' },
            { value: 'completed', label: '已完成' },
            { value: 'cancelled', label: '已取消' }
        ];

        const startTime = plan.start_time ? plan.start_time.replace(' ', 'T').substring(0, 16) :
            defaultDate ? `${defaultDate}T09:00` : '';
        const endTime = plan.end_time ? plan.end_time.replace(' ', 'T').substring(0, 16) :
            defaultDate ? `${defaultDate}T17:00` : '';

        const traineeIds = plan.trainee_ids || [];

        this.openModal({
            title: isEdit ? '编辑培训计划' : '新增培训计划',
            width: '650px',
            content: `
                <form id="planForm">
                    <div class="form-group">
                        <label>计划名称 *</label>
                        <input type="text" class="form-control" name="plan_name" value="${plan.plan_name || ''}" required>
                    </div>
                    <div class="form-group">
                        <label>关联课程</label>
                        <select class="form-control" name="course_id">
                            <option value="">请选择</option>
                            ${this.courses.map(c => `<option value="${c.id}" ${plan.course_id == c.id ? 'selected' : ''}>${c.course_code} - ${c.course_name}</option>`).join('')}
                        </select>
                    </div>
                    <div class="form-group">
                        <label>参训人员</label>
                        <div id="traineeSelectBox" style="max-height:150px;overflow-y:auto;border:1px solid var(--border-color,#dee2e6);border-radius:4px;padding:8px;">
                            ${this.users.length === 0 ? '<span style="color:var(--text-secondary);">暂无员工数据，请先在资质卡片页加载</span>' :
                                this.users.map(u => `
                                    <label style="display:flex;align-items:center;gap:6px;padding:2px 0;">
                                        <input type="checkbox" name="trainee_ids" value="${u.id}" ${traineeIds.includes(u.id) || traineeIds.includes(String(u.id)) ? 'checked' : ''}>
                                        <span>${u.username || u.name}${u.position ? ` (${u.position})` : ''}</span>
                                    </label>
                                `).join('')
                            }
                        </div>
                    </div>
                    <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;">
                        <div class="form-group">
                            <label>开始时间 *</label>
                            <input type="datetime-local" class="form-control" name="start_time" value="${startTime}" required>
                        </div>
                        <div class="form-group">
                            <label>结束时间 *</label>
                            <input type="datetime-local" class="form-control" name="end_time" value="${endTime}" required>
                        </div>
                    </div>
                    <div class="form-group">
                        <label>培训地点</label>
                        <input type="text" class="form-control" name="location" value="${plan.location || ''}">
                    </div>
                    <div class="form-group">
                        <label>状态</label>
                        <select class="form-control" name="status">
                            ${statuses.map(s => `<option value="${s.value}" ${plan.status === s.value ? 'selected' : ''} ${!plan.status && s.value === 'draft' ? 'selected' : ''}>${s.label}</option>`).join('')}
                        </select>
                    </div>
                    <div class="form-group">
                        <label>描述</label>
                        <textarea class="form-control" name="description" rows="3">${plan.description || ''}</textarea>
                    </div>
                </form>
            `,
            onConfirm: async () => {
                const form = document.getElementById('planForm');
                const selectedTrainees = Array.from(form.querySelectorAll('input[name="trainee_ids"]:checked')).map(i => parseInt(i.value));
                const data = {
                    plan_name: form.plan_name.value,
                    course_id: form.course_id.value ? parseInt(form.course_id.value) : null,
                    trainee_ids: selectedTrainees,
                    start_time: form.start_time.value.replace('T', ' ') + ':00',
                    end_time: form.end_time.value.replace('T', ' ') + ':00',
                    location: form.location.value || null,
                    status: form.status.value,
                    description: form.description.value || null
                };
                if (!data.plan_name || !data.start_time || !data.end_time) {
                    Toast.error('请填写必填项');
                    return false;
                }
                return await this.savePlan(isEdit ? planId : null, data);
            }
        });
    },

    async savePlan(id, data) {
        try {
            let res;
            if (id) {
                res = await TrainingService.updatePlan(id, data);
            } else {
                res = await TrainingService.createPlan(data);
            }
            if (res.code === 200 || res.code === 201) {
                Toast.show(id ? '更新成功' : '创建成功', 'success');
                this.loadPlans();
                return true;
            } else {
                Toast.error(res.message || '操作失败');
                return false;
            }
        } catch (e) {
            Toast.error('操作失败');
            return false;
        }
    },

    async deletePlan(id) {
        const confirmed = await Modal.confirm('确定要删除该培训计划吗？');
        if (!confirmed) return;
        try {
            const res = await TrainingService.deletePlan(id);
            if (res.code === 200) {
                Toast.show('删除成功', 'success');
                this.loadPlans();
            } else {
                Toast.error(res.message || '删除失败');
            }
        } catch (e) {
            Toast.error('删除失败');
        }
    },

    // ==================== Tab 3: 参训签到与成绩 ====================

    async loadAttendances() {
        try {
            const res = await TrainingService.getAttendances({ size: 300 });
            if (res.code === 200) {
                this.attendances = res.data.items || [];
            }
        } catch (e) {
            Toast.error('加载参训记录失败');
        }
        this.renderAttendances();
    },

    renderAttendances() {
        const content = document.getElementById('trainingTabContent');
        const signStatusMap = {
            not_signed: { label: '未签到', color: '#6c757d' },
            signed_in: { label: '已签到', color: '#28a745' },
            late: { label: '迟到', color: '#ffc107' },
            absent: { label: '缺勤', color: '#dc3545' },
            leave: { label: '请假', color: '#17a2b8' }
        };

        content.innerHTML = `
            <div style="margin-bottom:16px;display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:8px;">
                <div>
                    <select class="form-control" id="attendancePlanFilter" style="width:220px;display:inline-block;">
                        <option value="">全部培训计划</option>
                        ${this.plans.map(p => `<option value="${p.id}">${p.plan_name || p.id}</option>`).join('')}
                    </select>
                    <select class="form-control" id="attendanceStatusFilter" style="width:140px;display:inline-block;margin-left:8px;">
                        <option value="">全部签到状态</option>
                        ${Object.entries(signStatusMap).map(([k, v]) => `<option value="${k}">${v.label}</option>`).join('')}
                    </select>
                </div>
                <div style="display:flex;gap:8px;">
                    <button class="btn btn-outline" id="batchCreateBtn">批量生成参训记录</button>
                </div>
            </div>
            <div id="attendancesTableWrap">
                ${this.attendances.length === 0 ? '<div style="text-align:center;padding:40px;color:var(--text-secondary);">暂无参训记录，点击上方"批量生成参训记录"从培训计划创建</div>' : `
                <table class="data-table">
                    <thead>
                        <tr>
                            <th>员工</th>
                            <th>培训计划</th>
                            <th>签到状态</th>
                            <th>签到时间</th>
                            <th>最终成绩</th>
                            <th>是否合格</th>
                            <th>操作</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${this.attendances.map(a => {
                            const plan = this.plans.find(p => p.id === a.plan_id);
                            const status = signStatusMap[a.sign_status] || signStatusMap.not_signed;
                            return `
                                <tr>
                                    <td>${a.user_name || a.username || '员工' + a.user_id}</td>
                                    <td>${plan ? plan.plan_name : ('计划' + a.plan_id)}</td>
                                    <td><span class="status-badge" style="background:${status.color}22;color:${status.color};">${status.label}</span></td>
                                    <td>${a.sign_time || '-'}</td>
                                    <td>${a.score != null ? a.score : '-'}</td>
                                    <td>${a.is_passed === true ? '<span class="status-badge" style="background:rgba(40,167,69,0.1);color:#28a745;">合格</span>' :
                                        a.is_passed === false ? '<span class="status-badge" style="background:rgba(220,53,69,0.1);color:#dc3545;">不合格</span>' : '-'}</td>
                                    <td>
                                        <button class="btn btn-sm btn-outline" onclick="TrainingPage.openSignInModal(${a.id})">签到</button>
                                        <button class="btn btn-sm btn-outline" onclick="TrainingPage.openScoreModal(${a.id})">成绩</button>
                                    </td>
                                </tr>
                            `;
                        }).join('')}
                    </tbody>
                </table>
                `}
            </div>
        `;

        document.getElementById('attendancePlanFilter')?.addEventListener('change', () => this.filterAttendances());
        document.getElementById('attendanceStatusFilter')?.addEventListener('change', () => this.filterAttendances());
        document.getElementById('batchCreateBtn')?.addEventListener('click', () => this.openBatchCreateModal());
    },

    async filterAttendances() {
        const planId = document.getElementById('attendancePlanFilter')?.value;
        const status = document.getElementById('attendanceStatusFilter')?.value;
        try {
            const res = await TrainingService.getAttendances({
                size: 300,
                plan_id: planId || undefined,
                sign_in_status: status || undefined
            });
            if (res.code === 200) {
                this.attendances = res.data.items || [];
            }
        } catch (e) {
            Toast.error('筛选失败');
        }
        this.renderAttendances();
    },

    openBatchCreateModal() {
        if (this.plans.length === 0) {
            Toast.error('请先创建培训计划');
            return;
        }
        this.openModal({
            title: '批量生成参训记录',
            width: '500px',
            content: `
                <form id="batchCreateForm">
                    <div class="form-group">
                        <label>选择培训计划 *</label>
                        <select class="form-control" name="plan_id" required>
                            <option value="">请选择</option>
                            ${this.plans.map(p => `<option value="${p.id}">${p.plan_name || p.id}</option>`).join('')}
                        </select>
                    </div>
                    <div style="color:var(--text-secondary);font-size:13px;">将为该计划的所有参训人员生成参训记录</div>
                </form>
            `,
            onConfirm: async () => {
                const form = document.getElementById('batchCreateForm');
                const planId = form.plan_id.value;
                if (!planId) {
                    Toast.error('请选择培训计划');
                    return false;
                }
                return await this.batchCreateAttendances(parseInt(planId));
            }
        });
    },

    async batchCreateAttendances(planId) {
        try {
            const res = await TrainingService.batchCreateAttendances(planId);
            if (res.code === 200 || res.code === 201) {
                Toast.show('批量生成成功', 'success');
                this.loadAttendances();
                return true;
            } else {
                Toast.error(res.message || '操作失败');
                return false;
            }
        } catch (e) {
            Toast.error('操作失败');
            return false;
        }
    },

    openSignInModal(attendanceId) {
        const attendance = this.attendances.find(a => a.id === attendanceId);
        if (!attendance) return;

        const signStatuses = [
            { value: 'signed_in', label: '正常签到' },
            { value: 'late', label: '迟到' },
            { value: 'absent', label: '缺勤' },
            { value: 'leave', label: '请假' }
        ];

        this.openModal({
            title: '签到确认',
            width: '450px',
            content: `
                <div style="margin-bottom:16px;">
                    <p><strong>员工：</strong>${attendance.user_name || attendance.username || '员工' + attendance.user_id}</p>
                    <p><strong>当前状态：</strong>${attendance.sign_status || '未签到'}</p>
                </div>
                <form id="signInForm">
                    <div class="form-group">
                        <label>签到状态 *</label>
                        <select class="form-control" name="sign_status" required>
                            <option value="">请选择</option>
                            ${signStatuses.map(s => `<option value="${s.value}" ${attendance.sign_status === s.value ? 'selected' : ''}>${s.label}</option>`).join('')}
                        </select>
                    </div>
                </form>
            `,
            onConfirm: async () => {
                const form = document.getElementById('signInForm');
                const data = {
                    sign_status: form.sign_status.value
                };
                if (!data.sign_status) {
                    Toast.error('请选择签到状态');
                    return false;
                }
                return await this.signIn(attendanceId, data);
            }
        });
    },

    async signIn(attendanceId, data) {
        try {
            const res = await TrainingService.signInAttendance(attendanceId, data);
            if (res.code === 200) {
                Toast.show('签到成功', 'success');
                this.loadAttendances();
                return true;
            } else {
                Toast.error(res.message || '签到失败');
                return false;
            }
        } catch (e) {
            Toast.error('签到失败');
            return false;
        }
    },

    openScoreModal(attendanceId) {
        const attendance = this.attendances.find(a => a.id === attendanceId);
        if (!attendance) return;

        this.openModal({
            title: '录入成绩',
            width: '450px',
            content: `
                <div style="margin-bottom:16px;">
                    <p><strong>员工：</strong>${attendance.user_name || attendance.username || '员工' + attendance.user_id}</p>
                </div>
                <form id="scoreForm">
                    <div class="form-group">
                        <label>成绩（数字）</label>
                        <input type="number" class="form-control" name="score" step="0.1" min="0" max="100" value="${attendance.score != null ? attendance.score : ''}">
                    </div>
                    <div class="form-group">
                        <label style="display:flex;align-items:center;gap:8px;">
                            <input type="checkbox" name="is_passed" ${attendance.is_passed === true ? 'checked' : ''}>
                            是否合格
                        </label>
                    </div>
                </form>
            `,
            onConfirm: async () => {
                const form = document.getElementById('scoreForm');
                const score = form.score.value ? parseFloat(form.score.value) : null;
                const isPassed = form.is_passed.checked;
                return await this.saveAttendanceScore(attendanceId, score, isPassed);
            }
        });
    },

    async saveAttendanceScore(attendanceId, score, isPassed) {
        try {
            const res = await TrainingService.updateAttendance(attendanceId, {
                final_score: score,
                is_passed: isPassed
            });
            if (res.code === 200) {
                Toast.show('成绩已保存', 'success');
                this.loadAttendances();
                return true;
            } else {
                Toast.error(res.message || '保存失败');
                return false;
            }
        } catch (e) {
            Toast.error('保存失败');
            return false;
        }
    },

    // ==================== Tab 4: 员工资质卡片 ====================

    async loadCertificates() {
        try {
            const res = await TrainingService.getCertificates({ size: 500 });
            if (res.code === 200) {
                this.certificates = res.data.items || [];
            }
        } catch (e) {
            Toast.error('加载证书数据失败');
        }
    },

    async loadUsers() {
        try {
            const userMap = new Map();
            this.certificates.forEach(cert => {
                const uid = cert.user_id;
                if (uid != null && !userMap.has(uid)) {
                    userMap.set(uid, {
                        id: uid,
                        name: cert.user_name || cert.username || ('员工' + uid),
                        username: cert.user_name || cert.username || ('员工' + uid),
                        position: cert.user_position || cert.position || ''
                    });
                }
            });
            this.users = Array.from(userMap.values());
        } catch (e) {
            console.error('Load users failed:', e);
        }
    },

    async checkAllQualifications() {
        try {
            const res = await TrainingService.checkAllQualifications();
            if (res.code === 200) {
                Toast.show('资质校验完成', 'success');
                await this.loadCertificates();
                await this.loadUsers();
                this.renderQualificationCards();
            } else {
                Toast.error(res.message || '校验失败');
            }
        } catch (e) {
            Toast.error('校验失败');
        }
    },

    renderQualificationCards() {
        const content = document.getElementById('trainingTabContent');

        content.innerHTML = `
            <div style="margin-bottom:16px;display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:8px;">
                <div>
                    <input type="text" class="form-control" id="userSearchInput" placeholder="搜索员工姓名或岗位" style="width:240px;">
                </div>
                <button class="btn btn-primary" id="checkQualificationsBtn">🔍 资质校验</button>
            </div>
            <div id="qualificationCardsWrap" style="display:grid;grid-template-columns:repeat(auto-fill,minmax(320px,1fr));gap:16px;">
                ${this.users.length === 0 ? '<div style="grid-column:1/-1;text-align:center;padding:40px;color:var(--text-secondary);">暂无员工数据</div>' : ''}
            </div>
        `;

        document.getElementById('userSearchInput')?.addEventListener('input', () => this.filterQualificationCards());
        document.getElementById('checkQualificationsBtn')?.addEventListener('click', () => this.checkAllQualifications());

        this._renderFilteredCards('');
    },

    filterQualificationCards() {
        const keyword = document.getElementById('userSearchInput')?.value || '';
        this._renderFilteredCards(keyword);
    },

    _renderFilteredCards(keyword) {
        const wrap = document.getElementById('qualificationCardsWrap');
        if (!wrap) return;

        const kw = keyword.toLowerCase().trim();
        const filteredUsers = kw ?
            this.users.filter(u =>
                (u.name || u.username || '').toLowerCase().includes(kw) ||
                (u.position || '').toLowerCase().includes(kw)
            ) : this.users;

        if (filteredUsers.length === 0) {
            wrap.innerHTML = '<div style="grid-column:1/-1;text-align:center;padding:40px;color:var(--text-secondary);">无匹配结果</div>';
            return;
        }

        wrap.innerHTML = filteredUsers.map(user => this._renderUserCard(user)).join('');
    },

    _renderUserCard(user) {
        const userCerts = this.certificates.filter(c => c.user_id === user.id);
        const requiredCerts = this._getRequiredCertsForPosition(user.position);
        const missingCerts = this._getMissingCerts(userCerts, requiredCerts);

        let compliant = true;
        userCerts.forEach(cert => {
            const days = this.getDaysToExpiry(cert.expiry_date);
            if (days !== null && days < 0) compliant = false;
        });
        if (missingCerts.length > 0) compliant = false;

        return `
            <div style="background:white;border:1px solid var(--border-color,#dee2e6);border-radius:8px;padding:16px;transition:all 0.3s;" onmouseover="this.style.boxShadow='0 4px 12px rgba(0,0,0,0.1)'" onmouseout="this.style.boxShadow='none'">
                <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:12px;">
                    <div>
                        <div style="font-size:16px;font-weight:600;">${user.name || user.username}</div>
                        <div style="font-size:13px;color:var(--text-secondary,#6c757d);">${user.position || '岗位未设置'}</div>
                    </div>
                    <span class="status-badge" style="background:${compliant ? 'rgba(40,167,69,0.1)' : 'rgba(220,53,69,0.1)'};color:${compliant ? '#28a745' : '#dc3545'};">
                        ${compliant ? '✓ 合规' : '✗ 不合规'}
                    </span>
                </div>

                ${userCerts.length > 0 ? `
                <div style="margin-bottom:12px;">
                    <div style="font-size:13px;font-weight:500;margin-bottom:6px;color:var(--text-secondary);">证书列表</div>
                    ${userCerts.map(cert => {
                        const days = this.getDaysToExpiry(cert.expiry_date);
                        return `
                            <div style="border:1px solid var(--border-color,#e9ecef);border-radius:6px;padding:8px;margin-bottom:6px;font-size:12px;">
                                <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:4px;">
                                    <div style="font-weight:500;">
                                        ${cert.certificate_type || cert.type || '证书'} ${cert.certificate_code || cert.code ? '#' + (cert.certificate_code || cert.code) : ''}
                                    </div>
                                    ${this.getExpiryBadge(days)}
                                </div>
                                <div style="color:var(--text-secondary,#6c757d);">
                                    获取: ${this.formatDate(cert.issue_date)} | 有效期至: ${this.formatDate(cert.expiry_date)}
                                </div>
                                ${cert.attachment_base64 ? `<div style="margin-top:4px;"><img src="data:image/jpeg;base64,${cert.attachment_base64}" class="photo-preview" style="max-width:80px;max-height:60px;"></div>` : ''}
                            </div>
                        `;
                    }).join('')}
                </div>
                ` : ''}

                ${missingCerts.length > 0 ? `
                <div>
                    <div style="font-size:13px;font-weight:500;margin-bottom:6px;color:var(--text-secondary);">缺失证书</div>
                    <div style="display:flex;flex-wrap:wrap;gap:4px;">
                        ${missingCerts.map(mc => `<span class="status-badge" style="background:rgba(220,53,69,0.1);color:#dc3545;font-size:11px;">缺失: ${mc}</span>`).join('')}
                    </div>
                </div>
                ` : ''}

                ${userCerts.length === 0 && missingCerts.length === 0 ? `<div style="color:var(--text-secondary);font-size:12px;">暂无证书数据</div>` : ''}
            </div>
        `;
    },

    _getRequiredCertsForPosition(position) {
        if (!position) return [];
        const matches = this.positionQualifications.filter(pq => pq.position_name === position || pq.position === position);
        const result = [];
        matches.forEach(pq => {
            if (pq.required_certificates) {
                if (Array.isArray(pq.required_certificates)) {
                    result.push(...pq.required_certificates);
                } else if (typeof pq.required_certificates === 'string') {
                    try {
                        result.push(...JSON.parse(pq.required_certificates));
                    } catch (e) {}
                }
            }
        });
        return result;
    },

    _getMissingCerts(userCerts, requiredCerts) {
        if (requiredCerts.length === 0) return [];
        const userCertTypes = new Set(
            userCerts
                .filter(c => {
                    const days = this.getDaysToExpiry(c.expiry_date);
                    return days === null || days >= 0;
                })
                .map(c => c.certificate_type || c.type || '')
                .filter(Boolean)
        );
        return requiredCerts.filter(rc => !userCertTypes.has(rc));
    },

    // ==================== Tab 5: 岗位资质矩阵 ====================

    async loadPositionQualifications() {
        try {
            const res = await TrainingService.getPositionQualifications({ size: 200 });
            if (res.code === 200) {
                this.positionQualifications = res.data.items || [];
            }
        } catch (e) {
            console.error('Load position qualifications failed:', e);
        }
    },

    async loadMatrix() {
        try {
            const res = await TrainingService.getQualificationMatrix();
            if (res.code === 200) {
                this.matrixData = res.data || null;
            }
        } catch (e) {
            console.error('Load matrix failed:', e);
        }
        this.renderMatrix();
    },

    renderMatrix() {
        const content = document.getElementById('trainingTabContent');

        const positions = this._extractPositions();
        const users = this.users;

        content.innerHTML = `
            <div style="margin-bottom:16px;display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:8px;">
                <div style="display:flex;gap:16px;align-items:center;font-size:12px;">
                    <span style="display:flex;align-items:center;gap:4px;"><span style="width:16px;height:16px;background:#28a745;border-radius:2px;display:inline-block;"></span>满足要求</span>
                    <span style="display:flex;align-items:center;gap:4px;"><span style="width:16px;height:16px;background:#dc3545;border-radius:2px;display:inline-block;"></span>不满足</span>
                    <span style="display:flex;align-items:center;gap:4px;"><span style="width:16px;height:16px;background:#e9ecef;border-radius:2px;display:inline-block;"></span>非本岗位</span>
                </div>
                <div style="display:flex;gap:8px;">
                    <button class="btn btn-outline" id="refreshMatrixBtn">🔄 刷新矩阵</button>
                    <button class="btn btn-primary" id="positionConfigBtn">⚙ 岗位资质配置</button>
                </div>
            </div>
            <div style="overflow:auto;">
                ${users.length === 0 || positions.length === 0 ?
                    '<div style="text-align:center;padding:40px;color:var(--text-secondary);">暂无足够数据，请先确保有员工数据和岗位资质配置</div>' : `
                <table class="data-table" style="min-width:${80 + positions.length * 100}px;">
                    <thead>
                        <tr>
                            <th style="position:sticky;left:0;background:var(--bg-light,#f8f9fa);z-index:2;min-width:180px;text-align:left;">员工 / 岗位</th>
                            ${positions.map(p => `<th style="min-width:100px;">${p}</th>`).join('')}
                        </tr>
                    </thead>
                    <tbody>
                        ${users.map(user => `
                            <tr>
                                <td style="position:sticky;left:0;background:white;z-index:1;border-right:1px solid var(--border-color,#dee2e6);min-width:180px;">
                                    <div style="font-weight:500;">${user.name || user.username}</div>
                                    <div style="font-size:11px;color:var(--text-secondary,#6c757d);">${user.position || '-'}</div>
                                </td>
                                ${positions.map(pos => this._renderMatrixCell(user, pos)).join('')}
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
                `}
            </div>
        `;

        document.getElementById('refreshMatrixBtn')?.addEventListener('click', () => this.loadMatrix());
        document.getElementById('positionConfigBtn')?.addEventListener('click', () => this.openPositionQualificationModal());
    },

    _extractPositions() {
        const posSet = new Set();
        this.users.forEach(u => {
            if (u.position) posSet.add(u.position);
        });
        this.positionQualifications.forEach(pq => {
            if (pq.position_name) posSet.add(pq.position_name);
            if (pq.position) posSet.add(pq.position);
        });
        return Array.from(posSet);
    },

    _renderMatrixCell(user, position) {
        const isCurrentPosition = user.position === position;
        if (!isCurrentPosition) {
            return `<td style="width:100px;height:50px;text-align:center;background:#e9ecef;" title="员工非该岗位"></td>`;
        }

        const requiredCerts = this._getRequiredCertsForPosition(position);
        const missingCerts = this._getMissingCerts(
            this.certificates.filter(c => c.user_id === user.id),
            requiredCerts
        );
        const isSatisfied = missingCerts.length === 0;

        const titleText = requiredCerts.length === 0 ?
            '该岗位暂无资质要求配置' :
            (isSatisfied ? '所有证书要求已满足' : `缺失证书: ${missingCerts.join(', ')}`);

        const bgColor = isSatisfied ? '#28a745' : '#dc3545';

        return `
            <td style="width:100px;height:50px;text-align:center;padding:0;">
                <div style="width:100%;height:100%;background:${bgColor};display:flex;align-items:center;justify-content:center;color:white;font-size:12px;font-weight:500;cursor:help;"
                    title="${titleText}">
                    ${requiredCerts.length === 0 ? '未配置' : (isSatisfied ? '✓' : '✗ ' + missingCerts.length)}
                </div>
            </td>
        `;
    },

    openPositionQualificationModal(pqId = null) {
        const isEdit = pqId !== null;
        let pq = {};
        if (isEdit) {
            pq = this.positionQualifications.find(p => p.id === pqId) || {};
        }

        let requiredCerts = [];
        if (pq.required_certificates) {
            if (Array.isArray(pq.required_certificates)) {
                requiredCerts = pq.required_certificates;
            } else if (typeof pq.required_certificates === 'string') {
                try {
                    requiredCerts = JSON.parse(pq.required_certificates);
                } catch (e) {}
            }
        }
        const requiredCertsStr = requiredCerts.join(', ');

        const positions = this._extractPositions();

        this.openModal({
            title: '岗位资质配置管理',
            width: '700px',
            content: `
                <div style="margin-bottom:16px;padding:12px;background:var(--bg-light,#f8f9fa);border-radius:6px;">
                    <h5 style="margin:0 0 8px;">新增/编辑岗位资质要求</h5>
                    <form id="pqForm">
                        <div class="form-group">
                            <label>岗位名称 *</label>
                            <input type="text" class="form-control" name="position_name" value="${pq.position_name || pq.position || ''}" placeholder="如：操作员、质检员..." list="positionsList" required>
                            <datalist id="positionsList">
                                ${positions.map(p => `<option value="${p}">`).join('')}
                            </datalist>
                        </div>
                        <div class="form-group">
                            <label>所需证书类型（多个用逗号分隔）</label>
                            <input type="text" class="form-control" name="required_certificates" value="${requiredCertsStr}" placeholder="如：电工证,安全培训证,特种设备操作证">
                            <small style="color:var(--text-secondary);">所有持有这些有效证书的员工才算满足该岗位资质要求</small>
                        </div>
                        <div class="form-group">
                            <label>描述</label>
                            <textarea class="form-control" name="description" rows="2">${pq.description || ''}</textarea>
                        </div>
                        <div style="text-align:right;">
                            <button type="button" class="btn btn-primary" id="savePqBtn">${isEdit ? '更新' : '添加'}</button>
                        </div>
                    </form>
                </div>
                <div>
                    <h5 style="margin:0 0 8px;">已有配置</h5>
                    <table class="data-table">
                        <thead>
                            <tr><th>岗位</th><th>所需证书</th><th>描述</th><th>操作</th></tr>
                        </thead>
                        <tbody>
                            ${this.positionQualifications.length === 0 ? '<tr><td colspan="4" style="text-align:center;color:var(--text-secondary);padding:20px;">暂无配置</td></tr>' :
                                this.positionQualifications.map(item => {
                                    let certs = item.required_certificates;
                                    if (Array.isArray(certs)) certs = certs.join(', ');
                                    else if (typeof certs === 'string') {
                                        try { certs = JSON.parse(certs).join(', '); } catch (e) {}
                                    }
                                    return `
                                        <tr>
                                            <td>${item.position_name || item.position || '-'}</td>
                                            <td>${certs || '-'}</td>
                                            <td>${item.description || '-'}</td>
                                            <td>
                                                <button class="btn btn-sm btn-outline" onclick="TrainingPage.closeModal();setTimeout(()=>TrainingPage.openPositionQualificationModal(${item.id}),100);">编辑</button>
                                                <button class="btn btn-sm btn-danger" onclick="TrainingPage.deletePositionQualification(${item.id})">删除</button>
                                            </td>
                                        </tr>
                                    `;
                                }).join('')
                            }
                        </tbody>
                    </table>
                </div>
            `,
            showFooter: false
        });

        setTimeout(() => {
            document.getElementById('savePqBtn')?.addEventListener('click', async () => {
                const form = document.getElementById('pqForm');
                const positionName = form.position_name.value.trim();
                const certsInput = form.required_certificates.value.trim();
                const certsList = certsInput ? certsInput.split(/[,，]/).map(s => s.trim()).filter(Boolean) : [];
                const description = form.description.value || null;

                if (!positionName) {
                    Toast.error('请填写岗位名称');
                    return;
                }

                const data = {
                    position_name: positionName,
                    position: positionName,
                    required_certificates: certsList,
                    description: description
                };

                const success = await this._savePositionQualification(isEdit ? pqId : null, data);
                if (success) {
                    this.closeModal();
                    await this.loadPositionQualifications();
                    this.renderMatrix();
                }
            });
        }, 100);
    },

    async _savePositionQualification(id, data) {
        try {
            let res;
            if (id) {
                res = await TrainingService.updatePositionQualification(id, data);
            } else {
                res = await TrainingService.createPositionQualification(data);
            }
            if (res.code === 200 || res.code === 201) {
                Toast.show(id ? '更新成功' : '添加成功', 'success');
                return true;
            } else {
                Toast.error(res.message || '操作失败');
                return false;
            }
        } catch (e) {
            Toast.error('操作失败');
            return false;
        }
    },

    async deletePositionQualification(id) {
        const confirmed = await Modal.confirm('确定要删除该岗位资质配置吗？');
        if (!confirmed) return;
        try {
            const res = await TrainingService.deletePositionQualification(id);
            if (res.code === 200) {
                Toast.show('删除成功', 'success');
                await this.loadPositionQualifications();
                this.renderMatrix();
            } else {
                Toast.error(res.message || '删除失败');
            }
        } catch (e) {
            Toast.error('删除失败');
        }
    }
};

window.TrainingPage = TrainingPage;
