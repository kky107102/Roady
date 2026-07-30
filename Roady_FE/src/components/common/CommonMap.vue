<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref, watch } from 'vue'
import {
  divIcon,
  latLngBounds,
  map as createMap,
  marker as createMarker,
  tileLayer,
  type Map,
  type Marker,
} from 'leaflet'
import 'leaflet/dist/leaflet.css'
import type { MapMarkerItem } from '@/types/map'

interface Props {
  markers?: MapMarkerItem[]
  center?: [number, number]
  zoom?: number
  emptyMessage?: string
}

const props = withDefaults(defineProps<Props>(), {
  markers: () => [],
  center: () => [37.5665, 126.978],
  zoom: 12,
  emptyMessage: '표시할 위치 정보가 없습니다.',
})
const emit = defineEmits<{
  markerSelect: [id: MapMarkerItem['id']]
}>()

const mapElement = ref<HTMLElement | null>(null)
let mapInstance: Map | null = null
let markerInstances: Marker[] = []
let resizeObserver: ResizeObserver | null = null

function markerIcon(tone: MapMarkerItem['tone']) {
  return divIcon({
    className: 'roady-map-marker-wrapper',
    html: `<span class="roady-map-marker roady-map-marker--${tone ?? 'primary'}"></span>`,
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

function renderMarkers() {
  if (!mapInstance) return
  clearMarkers()

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

  if (props.markers.length === 1) {
    const marker = props.markers[0]
    if (marker) mapInstance.setView([marker.latitude, marker.longitude], 15)
  } else if (props.markers.length > 1) {
    const bounds = latLngBounds(
      props.markers.map((item) => [item.latitude, item.longitude] as [number, number]),
    )
    mapInstance.fitBounds(bounds, { padding: [40, 40], maxZoom: 15 })
  } else {
    mapInstance.setView(props.center, props.zoom)
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
  () => props.markers,
  () => renderMarkers(),
  { deep: true },
)

onBeforeUnmount(() => {
  resizeObserver?.disconnect()
  clearMarkers()
  mapInstance?.remove()
  mapInstance = null
})
</script>

<template>
  <div class="common-map">
    <div ref="mapElement" class="common-map__canvas" aria-label="지도"></div>
    <div v-if="markers.length === 0" class="common-map__empty" role="status">
      {{ emptyMessage }}
    </div>
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
  background: rgb(255 255 255 / 92%);
  box-shadow: 0 0.4rem 1.2rem rgb(17 24 39 / 10%);
  font-size: var(--krds-pc-font-size-body-small);
  transform: translateX(-50%);
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
  box-shadow: 0 0.3rem 0.8rem rgb(17 24 39 / 28%);
  background: var(--roady-brand-secondary);
  transform: rotate(-45deg);
}

:global(.roady-map-marker::after) {
  position: absolute;
  top: 50%;
  left: 50%;
  width: 0.8rem;
  height: 0.8rem;
  border-radius: 50%;
  background: var(--roady-surface-default);
  content: '';
  transform: translate(-50%, -50%);
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
}
</style>
