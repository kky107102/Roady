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

const COLORS = {
  total: '#5B7C9D',
  completed: '#4F9D69',
  totalHover: '#466987',
  completedHover: '#3D8154',
  grid: '#E8EDF2',
  text: '#6B7A8D',
}

const chartData = computed<ChartData<'bar'>>(() => ({
  labels: props.data.items.map((item) => item.period),
  datasets: [
    {
      label: '전체 탐지',
      data: props.data.items.map((item) => item.totalCount),
      backgroundColor: COLORS.total,
      hoverBackgroundColor: COLORS.totalHover,
      borderRadius: 2,
    },
    {
      label: '보수 완료',
      data: props.data.items.map((item) => item.repairCompletedCount),
      backgroundColor: COLORS.completed,
      hoverBackgroundColor: COLORS.completedHover,
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
        color: COLORS.text,
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
      ticks: { color: COLORS.text, font: { size: 12 } },
      border: { display: false },
    },
    y: {
      beginAtZero: true,
      grid: { color: COLORS.grid },
      ticks: {
        color: COLORS.text,
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
