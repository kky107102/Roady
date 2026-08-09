<script setup lang="ts">
import { computed } from 'vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import { repairStatusInfo } from '@/utils/repairManagement'

const props = defineProps<{ status: string }>()

const info = computed(() => repairStatusInfo(props.status))
</script>

<template>
  <StatusBadge :type="info.type" :label="info.label" />
</template>
