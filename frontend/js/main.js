/**
 * 主入口模块 - 生产线监控系统
 */
const App = {
    currentPage: null,
    pages: {
        dashboard: MonitorPage,
        production: ProductionLinePage,
        equipment: EquipmentPage,
        tasks: TasksPage,
        alerts: AlertsPage,
        safety: SafetyPage,
        training: TrainingPage,
        maintenance: MaintenancePage,
        spare: SparePage,
        disposal: DisposalPage,
        simulation: SimulationPage,
        knowledge: KnowledgePage,
        'env-monitor': EnvMonitorPage
    },

    init() {
        // 检查登录状态
        if (!AuthService.isLoggedIn()) {
            window.location.href = '/login.html';
            return;
        }

        // 初始化UI
        this.initSidebar();
        this.initHeader();

        // 加载默认页面
        const hash = window.location.hash.slice(1) || 'dashboard';
        this.navigate(hash);

        // 监听hash变化
        window.addEventListener('hashchange', () => {
            const hash = window.location.hash.slice(1) || 'dashboard';
            this.navigate(hash);
        });
    },

    initSidebar() {
        const sidebar = document.getElementById('sidebar');
        const menuToggle = document.getElementById('menuToggle');
        const sidebarToggle = document.getElementById('sidebarToggle');

        menuToggle?.addEventListener('click', () => {
            sidebar.classList.toggle('show');
        });

        sidebarToggle?.addEventListener('click', () => {
            sidebar.classList.remove('show');
        });

        document.querySelectorAll('.nav-item').forEach(item => {
            item.addEventListener('click', (e) => {
                e.preventDefault();
                const page = item.dataset.page;
                this.navigate(page);
                sidebar.classList.remove('show');
            });
        });
    },

    initHeader() {
        const user = AuthService.getCurrentUser();
        const usernameEl = document.getElementById('username');
        if (usernameEl && user) {
            usernameEl.textContent = user.username;
        }

        document.getElementById('logoutBtn')?.addEventListener('click', async () => {
            const confirmed = await Modal.confirm('确定要退出登录吗？');
            if (confirmed) {
                await AuthService.logout();
                window.location.href = '/login.html';
            }
        });

        // 全局搜索
        const globalSearchInput = document.getElementById('globalSearchInput');
        const globalSearchBtn = document.getElementById('globalSearchBtn');
        
        if (globalSearchInput) {
            globalSearchInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    this.doGlobalSearch();
                }
            });
        }
        
        if (globalSearchBtn) {
            globalSearchBtn.addEventListener('click', () => {
                this.doGlobalSearch();
            });
        }
    },

    doGlobalSearch() {
        const keyword = document.getElementById('globalSearchInput')?.value.trim();
        if (!keyword) {
            Toast.warning('请输入搜索关键词');
            return;
        }
        this.navigate('knowledge');
        // 延迟执行，确保知识库页面已加载
        setTimeout(() => {
            if (window.KnowledgePage) {
                KnowledgePage.searchKeyword = keyword;
                KnowledgePage.page = 1;
                KnowledgePage.view = 'list';
                KnowledgePage.render();
                KnowledgePage.loadDocuments();
            }
        }, 100);
    },

    navigate(page) {
        window.location.hash = page;

        document.querySelectorAll('.nav-item').forEach(item => {
            item.classList.toggle('active', item.dataset.page === page);
        });

        const titles = {
            dashboard: '监控中心',
            production: '生产线管理',
            equipment: '设备管理',
            tasks: '生产任务',
            alerts: '告警中心',
            safety: '安全管理',
            training: '培训资质管理',
            maintenance: '维修工单',
            spare: '备件管理',
            disposal: '不合格品处置',
            simulation: '数据模拟',
            knowledge: '知识库',
            'env-monitor': '环境监测'
        };
        document.getElementById('pageTitle').textContent = titles[page] || page;
        document.title = `${titles[page] || page} - 生产线监控系统`;

        if (this.currentPage && this.pages[this.currentPage]?.destroy) {
            this.pages[this.currentPage].destroy();
        }

        this.currentPage = page;
        if (this.pages[page]?.init) {
            this.pages[page].init();
        }
    }
};

document.addEventListener('DOMContentLoaded', () => {
    App.init();
});

window.App = App;
