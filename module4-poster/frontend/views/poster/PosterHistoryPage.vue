<template>
  <div />
</template>
<script setup>
import { onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
const router = useRouter()
const route = useRoute()
onMounted(() => {
  router.replace({ path: '/my-works', query: { ...route.query, tab: route.query.tab || 'poster' } })
})
</script>
