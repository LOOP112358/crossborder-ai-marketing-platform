<template>
  <div class="home-page">
    <section class="hero sketch-card">
      <div>
        <p class="eyebrow">越境智绘 · Cross-border AI</p>
        <h1 class="sketch-title">跨境AI营销系统</h1>
        <p class="lead">
          以智能串联跨境经营：文案、海报工作流、客服与看板，一站式完成从种草到运营。
        </p>
        <div class="actions">
          <el-button class="sketch-btn sketch-btn-primary" size="large" @click="$router.push('/writing')">
            先写一段文案
          </el-button>
          <el-button class="sketch-btn" size="large" @click="$router.push('/poster-workflow')">
            进入海报工作流
          </el-button>
        </div>
      </div>
      <div class="hero-stamp">
        <div class="stamp-ring">境</div>
        <p>跨境AI营销系统</p>
        <p class="muted">越境智绘 · 一站式智能营销</p>
      </div>
    </section>

    <section class="module-grid">
      <article
        v-for="module in modules"
        :key="module.path"
        class="module-card sketch-card"
        @click="$router.push(module.path)"
      >
        <div class="module-icon">{{ module.icon }}</div>
        <h3 class="sketch-title">{{ module.name }}</h3>
        <p>{{ module.desc }}</p>
        <div class="meta">
          <span class="owner">{{ module.owner }}</span>
          <span class="status" :class="module.ready ? 'ready' : 'soon'">{{ module.status }}</span>
        </div>
      </article>
    </section>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()

const modules = computed(() => [
  {
    name: t('home.writingName'),
    desc: t('home.writingDesc'),
    path: '/writing',
    icon: '✎',
    owner: '成员1',
    status: t('home.done'),
    ready: true,
  },
  {
    name: 'AI海报工作流',
    desc: '抠图识别 → 背景生成 → 海报合成，三步整合',
    path: '/poster-workflow',
    icon: '▣',
    owner: '成员2/3/4',
    status: t('home.done'),
    ready: true,
  },
  {
    name: t('home.chatName'),
    desc: t('home.chatDesc'),
    path: '/chat',
    icon: '✉',
    owner: '成员5',
    status: t('home.done'),
    ready: true,
  },
  {
    name: '运营看板',
    desc: '调用统计、趋势、预警与 AI 运营建议',
    path: '/dashboard',
    icon: '◔',
    owner: '成员5',
    status: t('home.done'),
    ready: true,
  },
])
</script>

<style scoped>
.home-page { display: grid; gap: 18px; }
.hero {
  display: grid;
  grid-template-columns: 1.5fr 0.7fr;
  gap: 20px;
  padding: 28px;
  background:
    linear-gradient(135deg, rgba(255,255,255,0.8), rgba(215,232,223,0.65));
}
.eyebrow {
  margin: 0 0 8px;
  color: var(--accent);
  letter-spacing: 2px;
  text-transform: uppercase;
  font-size: 12px;
}
.sketch-title { margin: 0 0 10px; font-size: clamp(2rem, 4vw, 3rem); }
.lead {
  margin: 0 0 18px;
  max-width: 560px;
  line-height: 1.8;
  color: var(--ink-soft);
}
.actions { display: flex; gap: 10px; flex-wrap: wrap; }
.hero-stamp {
  align-self: center;
  justify-self: end;
  text-align: center;
  transform: rotate(4deg);
}
.stamp-ring {
  width: 96px;
  height: 96px;
  margin: 0 auto 8px;
  border: 3px double var(--accent-2);
  border-radius: 50%;
  display: grid;
  place-items: center;
  color: var(--accent-2);
  font-family: var(--font-display);
  font-size: 40px;
  background: rgba(255, 247, 232, 0.9);
}
.hero-stamp p { margin: 0; }
.muted { color: var(--ink-soft); font-size: 12px; margin-top: 4px !important; }
.module-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: 14px;
}
.module-card {
  padding: 18px;
  cursor: pointer;
  transition: transform 0.15s ease, box-shadow 0.15s ease;
  min-height: 180px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.module-card:hover {
  transform: translate(-2px, -3px) rotate(-0.4deg);
  box-shadow: 5px 6px 0 rgba(36, 48, 56, 0.14);
}
.module-icon {
  width: 44px;
  height: 44px;
  border: 2px solid var(--line);
  border-radius: 40% 60% 50% 50% / 55% 45% 55% 45%;
  display: grid;
  place-items: center;
  background: #fff;
  font-size: 20px;
}
.module-card h3 { margin: 0; font-size: 22px; font-weight: 600; }
.module-card p {
  margin: 0;
  flex: 1;
  color: var(--ink-soft);
  font-size: 13px;
  line-height: 1.6;
}
.meta {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 8px;
}
.owner { font-size: 12px; color: var(--ink-soft); }
.status {
  font-size: 12px;
  padding: 2px 8px;
  border: 1.5px solid currentColor;
  border-radius: 999px;
}
.status.ready { color: var(--good); }
.status.soon { color: var(--accent-2); }
@media (max-width: 800px) {
  .hero { grid-template-columns: 1fr; }
  .hero-stamp { justify-self: start; transform: none; }
}
</style>
