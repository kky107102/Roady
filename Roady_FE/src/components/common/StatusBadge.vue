<script setup lang="ts">
import { computed } from 'vue'
import { Badge } from 'krds-vue'
import type { BadgeColor } from 'krds-vue'

export type BadgeType = 'danger' | 'warning' | 'info' | 'success' | 'neutral' | 'new'

interface Props {
  type: BadgeType
  label: string
  size?: 'small' | 'medium' | 'large'
}

const props = withDefaults(defineProps<Props>(), {
  size: 'small',
})

const colorMap: Record<BadgeType, BadgeColor> = {
  danger: 'danger',
  warning: 'warning',
  info: 'information',
  success: 'success',
  neutral: 'gray',
  new: 'primary',
}

const color = computed(() => colorMap[props.type])
</script>

<template>
  <Badge :color="color" variant="light" :size="size" :rounded="true">
    {{ label }}
  </Badge>
</template>
