<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { damagesApi } from '@/api/damages'

const props = defineProps<{
  damageId: number
  imageCount: number
}>()

const blobUrl = ref<string | null>(null)
const status = ref<'idle' | 'loading' | 'done' | 'error'>('idle')

onMounted(async () => {
  if (props.imageCount === 0) {
    status.value = 'error'
    return
  }
  status.value = 'loading'
  try {
    const detail = await damagesApi.getDetail(props.damageId)
    const firstImage = detail.images[0]
    if (!firstImage) {
      status.value = 'error'
      return
    }
    const blob = await damagesApi.getImageContent(props.damageId, firstImage.id)
    blobUrl.value = URL.createObjectURL(blob)
    status.value = 'done'
  } catch {
    status.value = 'error'
  }
})

onUnmounted(() => {
  if (blobUrl.value) URL.revokeObjectURL(blobUrl.value)
})
</script>

<template>
  <div class="thumbnail" :class="`thumbnail--${status}`">
    <img
      v-if="status === 'done' && blobUrl"
      :src="blobUrl"
      alt="파손 현장 이미지"
      class="thumbnail__img"
    />
    <!-- 로딩 중 스켈레톤 -->
    <div v-else-if="status === 'loading'" class="thumbnail__skeleton" aria-hidden="true" />
    <!-- 이미지 없음 / 오류 -->
    <div v-else class="thumbnail__empty" aria-hidden="true">
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
        <rect x="3" y="3" width="18" height="18" rx="2"/><circle cx="8.5" cy="8.5" r="1.5"/>
        <polyline points="21 15 16 10 5 21"/>
      </svg>
    </div>
  </div>
</template>

<style scoped>
.thumbnail {
  width: 7.2rem;
  height: 7.2rem;
  flex-shrink: 0;
  border-radius: 0.6rem;
  overflow: hidden;
  background: var(--roady-surface-subtle);
}

.thumbnail__img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.thumbnail__skeleton {
  width: 100%;
  height: 100%;
  background: linear-gradient(
    90deg,
    var(--roady-surface-subtle) 25%,
    var(--roady-border-default) 50%,
    var(--roady-surface-subtle) 75%
  );
  background-size: 200% 100%;
  animation: shimmer 1.4s infinite;
}

@keyframes shimmer {
  0% { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}

.thumbnail__empty {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--roady-text-tertiary);
}
</style>
