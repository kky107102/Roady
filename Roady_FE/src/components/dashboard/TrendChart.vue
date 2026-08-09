<script setup lang="ts">
import { computed } from 'vue'
import { Bar } from 'vue-chartjs'
import {
  BarElement,
  CategoryScale,
  Chart as ChartJS,
  Legend,
  LinearScale,
  Tooltip,
  type ChartData,
  type ChartOptions,
} from 'chart.js'
import type { TimeSeriesResponse } from '@/types/statistics'

ChartJS.register(CategoryScale, LinearScale, BarElement, Tooltip, Legend)

const props = defineProps<{ data: TimeSeriesResponse }>()

function cssColor(token: string, fallback: string): string {
  if (typeof document === 'undefined') return fallback
  return getComputedStyle(document.documentElement).getPropertyValue(token).trim() || fallback
}

const colors = computed(() => ({
  total: cssColor('--roady-chart-total', '#5b7c9d'),
  completed: cssColor('--roady-chart-completed', '#4f9d69'),
  totalHover: cssColor('--roady-chart-total-hover', '#466987'),
  completedHover: cssColor('--roady-chart-completed-hover', '#3d8154'),
  grid: cssColor('--roady-chart-grid', '#e8edf2'),
  text: cssColor('--roady-chart-text', '#6b7a8d'),
}))

const chartData = computed<ChartData<'bar'>>(() => ({
  labels: props.data.items.map((item) => item.period),
  datasets: [
    {
      label: '전체 탐지',
      data: props.data.items.map((item) => item.totalCount),
      backgroundColor: colors.value.total,
      hoverBackgroundColor: colors.value.totalHover,
      borderRadius: 2,
    },
    {
      label: '보수 완료',
      data: props.data.items.map((item) => item.repairCompletedCount),
      backgroundColor: colors.value.completed,
      hoverBackgroundColor: colors.value.completedHover,
      borderRadius: 2,
    },
  ],
}))

const chartOptions = computed<ChartOptions<'bar'>>(() => ({
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: {
      position: 'top',
      align: 'end',
      labels: {
        boxWidth: 10,
        boxHeight: 10,
        borderRadius: 2,
        useBorderRadius: true,
        color: colors.value.text,
        font: { size: 12 },
        padding: 16,
      },
    },
    tooltip: {
      callbacks: {
        label(context) {
          return ` ${context.dataset.label}: ${context.parsed.y}건`
        },
      },
    },
  },
  scales: {
    x: {
      grid: { display: false },
      ticks: { color: colors.value.text, font: { size: 12 } },
      border: { display: false },
    },
    y: {
      beginAtZero: true,
      grid: { color: colors.value.grid },
      ticks: {
        color: colors.value.text,
        font: { size: 12 },
        precision: 0,
        callback: (value) => `${value}건`,
      },
      border: { display: false },
    },
  },
}))
</script>

<template>
  <div class="trend-chart" role="img" aria-label="기간별 탐지 및 보수 완료 건수 막대 차트">
    <Bar :data="chartData" :options="chartOptions" />
  </div>
</template>

<style scoped>
.trend-chart {
  position: relative;
  height: 24rem;
}
</style>
