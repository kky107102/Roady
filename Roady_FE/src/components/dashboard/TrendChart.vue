<script setup lang="ts">
import { computed } from 'vue'
import { Bar } from 'vue-chartjs'
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Tooltip,
  Legend,
  type ChartData,
  type ChartOptions,
} from 'chart.js'
import type { TimeSeriesResponse } from '@/types/statistics'

ChartJS.register(CategoryScale, LinearScale, BarElement, Tooltip, Legend)

interface Props {
  data: TimeSeriesResponse
}

const props = defineProps<Props>()

const COLORS = {
  other: '#C8D9E8',      // 그 외 (전체 - 고위험)
  high: '#E05252',       // 고위험
  otherHover: '#A8C3D8',
  highHover: '#C83A3A',
  grid: '#E8EDF2',
  text: '#6B7A8D',
}

const chartData = computed<ChartData<'bar'>>(() => {
  const items = props.data.items
  const labels = items.map((i) => i.period)
  const highCounts = items.map((i) => i.highSeverityCount ?? 0)
  const otherCounts = items.map((i) => Math.max(0, i.totalCount - (i.highSeverityCount ?? 0)))

  return {
    labels,
    datasets: [
      {
        label: '그 외',
        data: otherCounts,
        backgroundColor: COLORS.other,
        hoverBackgroundColor: COLORS.otherHover,
        borderRadius: 0,
        stack: 'total',
      },
      {
        label: '고위험',
        data: highCounts,
        backgroundColor: COLORS.high,
        hoverBackgroundColor: COLORS.highHover,
        borderRadius: 2,
        stack: 'total',
      },
    ],
  }
})

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
        generateLabels(chart) {
          return chart.data.datasets
            .filter((ds) => ds.label !== '그 외')
            .concat(
              chart.data.datasets.filter((ds) => ds.label === '그 외').map((ds) => ({
                ...ds,
                label: '전체',
              })),
            )
            .map((ds, i) => ({
              text: ds.label === '그 외' ? '전체' : (ds.label ?? ''),
              fillStyle: ds.backgroundColor as string,
              strokeStyle: 'transparent',
              lineWidth: 0,
              hidden: false,
              index: i,
            }))
        },
      },
    },
    tooltip: {
      callbacks: {
        label(ctx) {
          const label = ctx.dataset.label === '그 외' ? '전체(그 외)' : ctx.dataset.label
          return ` ${label}: ${ctx.parsed.y}건`
        },
        footer(items) {
          const total = items.reduce((s, i) => s + (i.parsed.y ?? 0), 0)
          return `합계: ${total}건`
        },
      },
    },
  },
  scales: {
    x: {
      stacked: true,
      grid: { display: false },
      ticks: { color: COLORS.text, font: { size: 12 } },
      border: { display: false },
    },
    y: {
      stacked: true,
      beginAtZero: true,
      grid: { color: COLORS.grid },
      ticks: {
        color: COLORS.text,
        font: { size: 12 },
        stepSize: 5,
        callback: (v) => `${v}건`,
      },
      border: { display: false },
    },
  },
}))
</script>

<template>
  <div class="trend-chart" role="img" aria-label="기간별 탐지 추이 막대 차트">
    <Bar :data="chartData" :options="chartOptions" />
  </div>
</template>

<style scoped>
.trend-chart {
  position: relative;
  height: 24rem;
}
</style>
