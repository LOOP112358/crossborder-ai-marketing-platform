import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  { path: '/', redirect: '/home' },

  {
    path: '/login',
    name: 'Login',
    component: () => import('@m1/views/Login.vue'),
    meta: { requiresAuth: false },
  },
  {
    path: '/register',
    name: 'Register',
    component: () => import('@m1/views/Register.vue'),
    meta: { requiresAuth: false },
  },

  {
    path: '/',
    component: () => import('@/layouts/MainLayout.vue'),
    meta: { requiresAuth: true },
    children: [
      {
        path: 'home',
        name: 'Home',
        component: () => import('@m1/views/Home.vue'),
        meta: { title: '首页' },
      },
      {
        path: 'writing',
        name: 'Writing',
        component: () => import('@m1/views/writing/WritingPage.vue'),
        meta: { title: '文案生成' },
      },
      {
        path: 'poster-workflow',
        name: 'PosterWorkflow',
        component: () => import('@/views/PosterWorkflowPage.vue'),
        meta: { title: 'AI海报工作流' },
      },
      // 旧路由兼容：跳到工作流对应步骤
      { path: 'matte', redirect: { path: '/poster-workflow', query: { step: '0' } } },
      { path: 'background', redirect: { path: '/poster-workflow', query: { step: '1' } } },
      { path: 'poster', redirect: { path: '/poster-workflow', query: { step: '2' } } },
      {
        path: 'chat',
        name: 'Chat',
        component: () => import('@m5/views/chat/ChatPage.vue'),
        meta: { title: '智能客服' },
      },
      {
        path: 'dashboard',
        name: 'Dashboard',
        component: () => import('@m5/views/chat/DashboardPage.vue'),
        meta: { title: '运营看板' },
      },
    ],
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('token')
  const needAuth = to.matched.some((r) => r.meta.requiresAuth)
  if (needAuth && !token) {
    next('/login')
  } else if ((to.path === '/login' || to.path === '/register') && token) {
    next('/home')
  } else {
    next()
  }
})

export default router
