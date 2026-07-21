import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  { path: '/', redirect: '/home' },

  // ─── 模块1：认证页面 ───────────────────────────────
  {
    path: '/login', name: 'Login',
    component: () => import('@m1/views/Login.vue'),
    meta: { requiresAuth: false },
  },
  {
    path: '/register', name: 'Register',
    component: () => import('@m1/views/Register.vue'),
    meta: { requiresAuth: false },
  },

  // ─── 模块1：首页导航 ───────────────────────────────
  {
    path: '/home', name: 'Home',
    component: () => import('@m1/views/Home.vue'),
    meta: { requiresAuth: true },
  },

  // ─── 模块1：文案生成 ───────────────────────────────
  {
    path: '/writing', name: 'Writing',
    component: () => import('@m1/views/writing/WritingPage.vue'),
    meta: { requiresAuth: true, title: '文案生成' },
  },

  // ─── 模块2：商品抠图 ───────────────────────────────
  {
    path: '/matte', name: 'Matte',
    component: () => import('@m2/views/matte/MattePage.vue'),
    meta: { requiresAuth: true, title: '商品抠图' },
  },

  // ─── 模块3：背景生成（占位） ────────────────────────
  {
    path: '/background', name: 'Background',
    component: () => import('@m3/views/background/Placeholder.vue'),
    meta: { requiresAuth: true, title: '背景生成' },
  },

  // ─── 模块4：海报合成 ───────────────────────────────
  {
    path: '/poster', name: 'Poster',
    component: () => import('@m4/views/poster/PosterPage.vue'),
    meta: { requiresAuth: true, title: '海报合成' },
  },

  // ─── 模块5：智能客服 + 运营看板 ────────────────────
  {
    path: '/chat', name: 'Chat',
    component: () => import('@m5/views/chat/ChatPage.vue'),
    meta: { requiresAuth: true, title: '智能客服' },
  },
  {
    path: '/dashboard', name: 'Dashboard',
    component: () => import('@m5/views/chat/DashboardPage.vue'),
    meta: { requiresAuth: true, title: '运营看板' },
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('token')
  if (to.meta.requiresAuth !== false && !token) {
    next('/login')
  } else if ((to.path === '/login' || to.path === '/register') && token) {
    next('/home')
  } else {
    next()
  }
})

export default router
