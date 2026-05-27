<template>
  <div class="app-shell">
    <AppHeader />
    <main class="app-shell__main" :class="{ 'app-shell__main--flush': isFlush }">
      <router-view />
    </main>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import AppHeader from '@/components/AppHeader.vue'

const route = useRoute()
const isFlush = computed(() => route.meta?.flushMain === true)
</script>
