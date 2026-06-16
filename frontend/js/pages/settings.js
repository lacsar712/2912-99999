/**
 * 系统设置页面
 */
const SettingsPage = {
    init() {
        this.render();
    },

    render() {
        const user = AuthService.getCurrentUser();
        const isAdmin = AuthService.isAdmin();

        const container = document.getElementById('pageContainer');

        container.innerHTML = `
            <div class="grid grid-2">
                <div class="card">
                    <div class="card-header">
                        <h3 class="card-title">个人信息</h3>
                    </div>
                    <div class="card-body">
                        <form id="profileForm">
                            <div class="form-group">
                                <label class="form-label">用户名</label>
                                <input type="text" class="form-control" value="${user?.username || ''}" disabled>
                            </div>
                            <div class="form-group">
                                <label class="form-label">邮箱</label>
                                <input type="email" class="form-control" name="email" value="${user?.email || ''}">
                            </div>
                            <div class="form-group">
                                <label class="form-label">角色</label>
                                <input type="text" class="form-control" value="${user?.role === 'admin' ? '管理员' : '普通用户'}" disabled>
                            </div>
                            <button type="submit" class="btn btn-primary">保存修改</button>
                        </form>
                    </div>
                </div>

                <div class="card">
                    <div class="card-header">
                        <h3 class="card-title">修改密码</h3>
                    </div>
                    <div class="card-body">
                        <form id="passwordForm">
                            <div class="form-group">
                                <label class="form-label">原密码</label>
                                <input type="password" class="form-control" name="oldPassword" required>
                            </div>
                            <div class="form-group">
                                <label class="form-label">新密码</label>
                                <input type="password" class="form-control" name="newPassword" required minlength="6">
                            </div>
                            <div class="form-group">
                                <label class="form-label">确认新密码</label>
                                <input type="password" class="form-control" name="confirmPassword" required>
                            </div>
                            <button type="submit" class="btn btn-primary">修改密码</button>
                        </form>
                    </div>
                </div>
            </div>

            ${isAdmin ? `
            <div class="card">
                <div class="card-header">
                    <h3 class="card-title">系统信息</h3>
                </div>
                <div class="card-body">
                    <div class="grid grid-3">
                        <div class="form-group">
                            <label class="form-label">系统名称</label>
                            <input type="text" class="form-control" value="${Config.APP_NAME}" disabled>
                        </div>
                        <div class="form-group">
                            <label class="form-label">版本号</label>
                            <input type="text" class="form-control" value="${Config.VERSION}" disabled>
                        </div>
                        <div class="form-group">
                            <label class="form-label">默认分页大小</label>
                            <input type="text" class="form-control" value="${Config.DEFAULT_PAGE_SIZE}" disabled>
                        </div>
                    </div>
                </div>
            </div>
            ` : ''}
        `;

        this.bindEvents();
    },

    bindEvents() {
        // 个人信息表单
        document.getElementById('profileForm')?.addEventListener('submit', async (e) => {
            e.preventDefault();
            const form = e.target;
            const data = {
                email: form.email.value
            };

            try {
                // 这里应该调用更新用户信息的API
                Toast.success('保存成功');
                const user = AuthService.getCurrentUser();
                user.email = data.email;
                Storage.setUserInfo(user);
            } catch (error) {
                Toast.error('保存失败');
            }
        });

        // 密码表单
        document.getElementById('passwordForm')?.addEventListener('submit', async (e) => {
            e.preventDefault();
            const form = e.target;
            const oldPassword = form.oldPassword.value;
            const newPassword = form.newPassword.value;
            const confirmPassword = form.confirmPassword.value;

            if (newPassword !== confirmPassword) {
                Toast.error('两次输入的密码不一致');
                return;
            }

            try {
                const response = await AuthService.changePassword(oldPassword, newPassword);
                if (response.code === 200) {
                    Toast.success('密码修改成功');
                    form.reset();
                } else {
                    Toast.error(response.message);
                }
            } catch (error) {
                Toast.error('修改失败');
            }
        });
    },

    destroy() {
        // 清理资源
    }
};

// 全局可用
window.SettingsPage = SettingsPage;
