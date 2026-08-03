<script setup lang="ts">
import { computed } from 'vue'
import type { BadgeType } from '@/components/common/StatusBadge.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'

const props = defineProps<{ status: string }>()

const STATUS_MAP: Record<string, { label: string; type: BadgeType }> = {
  REQUESTED: { label: '요청 전', type: 'warning' },
  REPAIR_IN_PROGRESS: { label: '요청 완료', type: 'info' },
  REPAIR_COMPLETED: { label: '보수 완료', type: 'success' },
}

const info = computed(
  () => STATUS_MAP[props.status] ?? { label: props.status, type: 'neutral' as BadgeType },
)
</script>

<template>
  <StatusBadge :type="info.type" :label="info.label" />
</template>
