<template>
  <div class="placeholder">
    <el-result
      :icon="icon"
      :title="displayTitle"
      :sub-title="displayDesc"
    >
      <template #extra>
        <el-button type="primary" @click="$router.push('/home')">{{ $t('common.back') }}</el-button>
      </template>
    </el-result>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'

const props = defineProps({
  moduleKey: { type: String, default: 'matte' },
  icon: { type: String, default: 'Clock' },
})

const { t } = useI18n()

const displayTitle = computed(() => {
  const titles = { matte: 'matte.title', background: 'background.title', poster: 'poster.title', chat: 'chat.title' }
  return t(titles[props.moduleKey] || 'developing.title')
})

const displayDesc = computed(() => {
  const owners = { matte: 'matte.owner', background: 'background.owner', poster: 'poster.owner', chat: 'chat.owner' }
  return t('developing.desc', { owner: t(owners[props.moduleKey] || '') })
})
</script>

<style scoped>
.placeholder {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 400px;
  background: #fff;
  border-radius: 8px;
}
</style>
