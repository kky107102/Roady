import { computed, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { administrativeRegionsApi } from '@/api/administrativeRegions'
import { useAuthStore } from '@/stores/auth'
import type { AssignedMapRegions } from '@/types/map'

const EMD_QUERY_KEY = 'emd'

function queryString(value: unknown): string {
  const raw = Array.isArray(value) ? value[0] : value
  return typeof raw === 'string' ? raw.trim() : ''
}

export function useAssignedMapRegion() {
  const auth = useAuthStore()
  const route = useRoute()
  const router = useRouter()
  const regions = ref<AssignedMapRegions | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)
  let requestSequence = 0

  const assignedRegionCode = computed(() => auth.user?.assignedRegionCode?.trim() || '')
  const assignedRegionName = computed(
    () => auth.user?.assignedRegionName?.trim() || regions.value?.regionName || null,
  )
  const selectedCode = computed(() => queryString(route.query[EMD_QUERY_KEY]))
  const selectedOption = computed(
    () => regions.value?.emds.find((option) => option.code === selectedCode.value) ?? null,
  )
  const selectedBounds = computed(
    () => selectedOption.value?.bounds ?? regions.value?.bounds ?? null,
  )

  function replaceQuerySelection(code: string) {
    const query = { ...route.query }
    if (code) query[EMD_QUERY_KEY] = code
    else delete query[EMD_QUERY_KEY]
    return router.replace({ path: route.path, query })
  }

  function select(code: string) {
    if (code && !regions.value?.emds.some((option) => option.code === code)) return
    void replaceQuerySelection(code)
  }

  function normalizeUrlSelection() {
    if (!selectedCode.value || selectedOption.value) return
    void replaceQuerySelection('')
  }

  async function load() {
    const regionCode = assignedRegionCode.value
    const sequence = ++requestSequence
    regions.value = null
    error.value = null
    if (!regionCode) return

    loading.value = true
    try {
      const response = await administrativeRegionsApi.getEmds(regionCode)
      if (sequence !== requestSequence) return
      regions.value = {
        ...response,
        emds: [...response.emds].sort((left, right) =>
          left.name.localeCompare(right.name, 'ko-KR', { numeric: true }),
        ),
      }
      normalizeUrlSelection()
    } catch {
      if (sequence !== requestSequence) return
      error.value = '읍면동 목록을 불러오지 못했습니다.'
    } finally {
      if (sequence === requestSequence) loading.value = false
    }
  }

  watch(assignedRegionCode, () => void load(), { immediate: true })
  watch(selectedCode, normalizeUrlSelection)

  return {
    assignedRegionCode,
    assignedRegionName,
    options: computed(() => regions.value?.emds ?? []),
    selectedCode,
    selectedBounds,
    loading,
    error,
    load,
    select,
  }
}
