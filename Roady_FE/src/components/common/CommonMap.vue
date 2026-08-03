<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref, watch } from 'vue'
import {
  divIcon,
  latLngBounds,
  map as createMap,
  marker as createMarker,
  polyline as createPolyline,
  tileLayer,
  type Map,
  type Marker,
  type Polyline,
} from 'leaflet'
import 'leaflet/dist/leaflet.css'
import type { MapMarkerItem, MapPathItem } from '@/types/map'

interface Props {
  markers?: MapMarkerItem[]
  paths?: MapPathItem[]
  center?: [number, number]
  zoom?: number
  focusedCenter?: [number, number] | null
  focusZoom?: number
  rightInset?: number
  emptyMessage?: string
  mapLabel?: string
}

const props = withDefaults(defineProps<Props>(), {
  markers: () => [],
  paths: () => [],
  center: () => [37.5665, 126.978],
  zoom: 12,
  focusZoom: 16,
  rightInset: 0,
  emptyMessage: '표시할 위치 정보가 없습니다.',
  mapLabel: '지도',
})
const emit = defineEmits<{
  markerSelect: [id: MapMarkerItem['id']]
}>()

const mapElement = ref<HTMLElement | null>(null)
let mapInstance: Map | null = null
let markerInstances: Marker[] = []
let pathInstances: Polyline[] = []
let resizeObserver: ResizeObserver | null = null
let focusSettleTimer: ReturnType<typeof setTimeout> | null = null

function markerIcon(tone: MapMarkerItem['tone']) {
  const normalizedTone = tone ?? 'primary'
  const symbols: Record<NonNullable<MapMarkerItem['tone']>, string> = {
    primary: 'i',
    success: '✓',
    warning: '!',
    danger: '!',
    neutral: '·',
  }

  return divIcon({
    className: 'roady-map-marker-wrapper',
    html: `<span class="roady-map-marker roady-map-marker--${normalizedTone}"><span class="roady-map-marker__symbol">${symbols[normalizedTone]}</span></span>`,
    iconSize: [32, 40],
    iconAnchor: [16, 40],
    popupAnchor: [0, -34],
  })
}

function popupContent(item: MapMarkerItem): HTMLElement {
  const container = document.createElement('div')
  container.className = 'roady-map-popup'

  const title = document.createElement('strong')
  title.className = 'roady-map-popup__title'
  title.textContent = item.title
  container.append(title)

  if (item.details?.length) {
    const list = document.createElement('dl')
    list.className = 'roady-map-popup__details'

    item.details.forEach((detail) => {
      const label = document.createElement('dt')
      const value = document.createElement('dd')
      label.textContent = detail.label
      value.textContent = detail.value
      list.append(label, value)
    })
    container.append(list)
  }

  return container
}

function clearMarkers() {
  markerInstances.forEach((marker) => marker.remove())
  markerInstances = []
}

function insetAdjustedCenter(center: [number, number]): [number, number] {
  if (!mapInstance || props.rightInset <= 0) return center

  const mapWidth = mapInstance.getSize().x
  const safeInset = Math.min(props.rightInset, Math.max(0, mapWidth - 80))
  const point = mapInstance.project(center, props.focusZoom).add([safeInset / 2, 0])
  const adjusted = mapInstance.unproject(point, props.focusZoom)
  return [adjusted.lat, adjusted.lng]
}

function focusSelectedLocation(animate: boolean) {
  if (!mapInstance || !props.focusedCenter) return
  const center = insetAdjustedCenter(props.focusedCenter)
  if (animate) {
    mapInstance.flyTo(center, props.focusZoom, { duration: 0.4 })
  } else {
    mapInstance.setView(center, props.focusZoom, { animate: false })
  }
}

function clearPaths() {
  pathInstances.forEach((path) => path.remove())
  pathInstances = []
}

function pathColor(tone: MapPathItem['tone']): string {
  const tokenMap = {
    primary: '--roady-brand-secondary',
    success: '--roady-status-success',
    warning: '--roady-status-warning',
    danger: '--roady-status-danger',
    neutral: '--roady-text-tertiary',
  }
  const token = tokenMap[tone ?? 'primary']
  return getComputedStyle(document.documentElement).getPropertyValue(token).trim() || 'currentColor'
}

function renderMarkers() {
  if (!mapInstance) return
  clearMarkers()
  clearPaths()

  pathInstances = props.paths
    .filter((path) => path.points.length >= 2)
    .map((path) =>
      createPolyline(
        path.points.map((point) => [point.latitude, point.longitude]),
        {
          color: pathColor(path.tone),
          weight: 5,
          opacity: 0.8,
          lineCap: 'round',
          lineJoin: 'round',
        },
      ).addTo(mapInstance as Map),
    )

  markerInstances = props.markers.map((item) => {
    const marker = createMarker([item.latitude, item.longitude], {
      icon: markerIcon(item.tone),
      title: item.title,
      alt: `${item.title} 위치`,
      keyboard: true,
    })
      .bindPopup(popupContent(item), { minWidth: 190 })
      .addTo(mapInstance as Map)

    marker.on('click', () => emit('markerSelect', item.id))
    return marker
  })

  if (props.focusedCenter) {
    focusSelectedLocation(false)
  } else {
    const allCoordinates = [
      ...props.markers.map((item) => [item.latitude, item.longitude] as [number, number]),
      ...props.paths.flatMap((path) =>
        path.points.map((point) => [point.latitude, point.longitude] as [number, number]),
      ),
    ]

    if (allCoordinates.length === 1) {
      const coordinate = allCoordinates[0]
      if (coordinate) mapInstance.setView(coordinate, 15)
    } else if (allCoordinates.length > 1) {
      const bounds = latLngBounds(allCoordinates)
      mapInstance.fitBounds(bounds, { padding: [40, 40], maxZoom: 15 })
    } else {
      mapInstance.setView(props.center, props.zoom)
    }
  }
}

onMounted(() => {
  if (!mapElement.value) return

  mapInstance = createMap(mapElement.value, {
    center: props.center,
    zoom: props.zoom,
    zoomControl: true,
  })

  tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 19,
    attribution: '&copy; OpenStreetMap contributors',
  }).addTo(mapInstance)

  renderMarkers()

  if (typeof ResizeObserver !== 'undefined') {
    resizeObserver = new ResizeObserver(() => mapInstance?.invalidateSize())
    resizeObserver.observe(mapElement.value)
  }
})

watch(
  () => [props.markers, props.paths],
  () => renderMarkers(),
  { deep: true },
)

watch(
  () => [
    props.focusedCenter?.[0] ?? null,
    props.focusedCenter?.[1] ?? null,
    props.focusZoom,
    props.rightInset,
  ] as const,
  ([latitude, longitude], previous) => {
    if (latitude == null || longitude == null) return

    const locationChanged = !previous || latitude !== previous[0] || longitude !== previous[1]
    focusSelectedLocation(locationChanged)

    if (focusSettleTimer) clearTimeout(focusSettleTimer)
    focusSettleTimer = setTimeout(() => {
      focusSelectedLocation(false)
      focusSettleTimer = null
    }, 300)
  },
  { flush: 'post' },
)

onBeforeUnmount(() => {
  if (focusSettleTimer) clearTimeout(focusSettleTimer)
  resizeObserver?.disconnect()
  clearMarkers()
  clearPaths()
  mapInstance?.remove()
  mapInstance = null
})
</script>

<template>
  <div class="common-map">
    <div ref="mapElement" class="common-map__canvas" :aria-label="mapLabel"></div>
    <div v-if="markers.length === 0" class="common-map__empty" role="status">
      {{ emptyMessage }}
    </div>
    <ul v-else class="common-map__summary">
      <li v-for="marker in markers" :key="marker.id">
        <strong>{{ marker.title }}</strong>
        <span v-for="detail in marker.details" :key="detail.label">
          {{ detail.label }} {{ detail.value }}
        </span>
      </li>
    </ul>
    <ul v-if="paths.length" class="common-map__summary">
      <li v-for="path in paths" :key="path.id">
        {{ path.label || '이동 경로' }} {{ path.points.length }}개 위치
      </li>
    </ul>
  </div>
</template>

<style scoped>
.common-map {
  position: relative;
  width: 100%;
  height: 100%;
  min-height: 28rem;
  overflow: hidden;
  border-radius: 0.6rem;
  background: var(--roady-surface-background);
}

.common-map__canvas {
  width: 100%;
  height: 100%;
  min-height: inherit;
}

.common-map__empty {
  position: absolute;
  bottom: 1.6rem;
  left: 50%;
  z-index: 500;
  padding: 0.8rem 1.2rem;
  border: 1px solid var(--roady-border-default);
  border-radius: 0.6rem;
  color: var(--roady-text-secondary);
  background: color-mix(in srgb, var(--roady-surface-default) 92%, transparent);
  box-shadow: 0 0.4rem 1.2rem color-mix(in srgb, var(--roady-text-primary) 10%, transparent);
  font-size: var(--krds-pc-font-size-body-small);
  max-width: calc(100% - 3.2rem);
  text-align: center;
  transform: translateX(-50%);
}

.common-map__summary {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border: 0;
}

:global(.roady-map-marker-wrapper) {
  border: 0;
  background: transparent;
}

:global(.roady-map-marker) {
  position: relative;
  display: block;
  width: 2.8rem;
  height: 2.8rem;
  border: 0.4rem solid var(--roady-surface-default);
  border-radius: 50% 50% 50% 0;
  box-shadow: 0 0.3rem 0.8rem color-mix(in srgb, var(--roady-text-primary) 28%, transparent);
  background: var(--roady-brand-secondary);
  transform: rotate(-45deg);
}

:global(.roady-map-marker__symbol) {
  position: absolute;
  top: 50%;
  left: 50%;
  color: var(--roady-surface-default);
  font-size: 1.4rem;
  font-weight: var(--krds-font-weight-bold);
  line-height: 1;
  transform: translate(-50%, -50%) rotate(45deg);
}

:global(.roady-map-marker--success) {
  background: var(--roady-status-success);
}

:global(.roady-map-marker--warning) {
  background: var(--roady-status-warning);
}

:global(.roady-map-marker--danger) {
  background: var(--roady-status-danger);
}

:global(.roady-map-marker--neutral) {
  background: var(--roady-text-tertiary);
}

:global(.roady-map-popup) {
  min-width: 17rem;
  color: var(--roady-text-primary);
  font-family: inherit;
}

:global(.roady-map-popup__title) {
  display: block;
  padding-bottom: 0.8rem;
  border-bottom: 1px solid var(--roady-border-default);
  font-size: var(--krds-pc-font-size-body-small);
}

:global(.roady-map-popup__details) {
  display: grid;
  grid-template-columns: auto 1fr;
  gap: 0.5rem 1.2rem;
  margin: 0.8rem 0 0;
  font-size: var(--krds-pc-font-size-label-small);
}

:global(.roady-map-popup__details dt) {
  color: var(--roady-text-tertiary);
}

:global(.roady-map-popup__details dd) {
  margin: 0;
  font-weight: var(--krds-font-weight-bold);
  overflow-wrap: anywhere;
}

:global(.leaflet-marker-icon:focus-visible),
:global(.leaflet-control-zoom a:focus-visible) {
  outline: 0.3rem solid var(--roady-brand-secondary);
  outline-offset: 0.2rem;
  box-shadow: 0 0 0 0.4rem var(--roady-focus-ring);
}
</style>
