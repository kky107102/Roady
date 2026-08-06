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
import type { MapBounds, MapMarkerItem, MapPathItem } from '@/types/map'

const POPUP_MARKER_VERTICAL_OFFSET_PX = 80
const POPUP_CENTER_PAN_DURATION_SECONDS = 0.2
const PROGRAMMATIC_MOVE_GUARD_MS = 500

interface Props {
  markers?: MapMarkerItem[]
  paths?: MapPathItem[]
  center?: [number, number]
  zoom?: number
  focusedCenter?: [number, number] | null
  viewportBounds?: MapBounds | null
  focusZoom?: number
  rightInset?: number
  centerPopupOnSelect?: boolean
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
  centerPopupOnSelect: false,
  emptyMessage: '표시할 위치 정보가 없습니다.',
  mapLabel: '지도',
})
const emit = defineEmits<{
  markerSelect: [id: MapMarkerItem['id']]
  boundsChange: [bounds: MapBounds]
}>()

const mapElement = ref<HTMLElement | null>(null)
let mapInstance: Map | null = null
let markerInstances: Marker[] = []
let pathInstances: Polyline[] = []
let resizeObserver: ResizeObserver | null = null
let focusSettleTimer: ReturnType<typeof setTimeout> | null = null
let programmaticMoveTimer: ReturnType<typeof setTimeout> | null = null
let hasAutoFittedContent = false
let openPopupMarkerId: MapMarkerItem['id'] | null = null
let renderedContentKey: string | null = null
let suppressProgrammaticMoveEnd = false

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
    iconSize: [44, 44],
    iconAnchor: [22, 42],
    popupAnchor: [0, -38],
  })
}

function popupContent(item: MapMarkerItem): HTMLElement {
  const container = document.createElement('div')
  container.className = 'roady-map-popup'

  const header = document.createElement('div')
  header.className = 'roady-map-popup__header'

  const title = document.createElement('strong')
  title.className = 'roady-map-popup__title'
  title.textContent = item.title
  header.append(title)

  if (item.actionHref) {
    const action = document.createElement('a')
    action.className = 'roady-map-popup__action'
    action.href = item.actionHref
    action.textContent = item.actionLabel ?? '상세보기'
    action.addEventListener('click', (event) => {
      event.preventDefault()
      emit('markerSelect', item.id)
    })
    header.append(action)
  }

  container.append(header)

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

function centerMarkerPopup(item: MapMarkerItem) {
  if (!props.centerPopupOnSelect || !mapInstance) return
  mapInstance.stop()
  const zoom = mapInstance.getZoom()
  const markerPx = mapInstance.project([item.latitude, item.longitude], zoom)
  // Offset center upward so the marker appears below viewport center,
  // leaving the popup (which opens above the marker) visible near the center.
  const center = mapInstance.unproject(
    markerPx.subtract([0, POPUP_MARKER_VERTICAL_OFFSET_PX]),
    zoom,
  )
  suppressProgrammaticMoveEnd = true
  if (programmaticMoveTimer) clearTimeout(programmaticMoveTimer)
  programmaticMoveTimer = setTimeout(() => {
    suppressProgrammaticMoveEnd = false
    programmaticMoveTimer = null
  }, PROGRAMMATIC_MOVE_GUARD_MS)
  const reduceMotion = window.matchMedia?.('(prefers-reduced-motion: reduce)').matches ?? false
  mapInstance.panTo(
    center,
    reduceMotion
      ? { animate: false }
      : { animate: true, duration: POPUP_CENTER_PAN_DURATION_SECONDS },
  )
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
  hasAutoFittedContent = true
  const center = insetAdjustedCenter(props.focusedCenter)
  if (animate) {
    mapInstance.flyTo(center, props.focusZoom, { duration: 0.4 })
  } else {
    mapInstance.setView(center, props.focusZoom, { animate: false })
  }
}

function fitViewportBounds(animate: boolean) {
  if (!mapInstance || !props.viewportBounds) return
  hasAutoFittedContent = true
  const { south, north, west, east } = props.viewportBounds
  mapInstance.fitBounds(
    latLngBounds([
      [south, west],
      [north, east],
    ]),
    { padding: [32, 32], animate },
  )
}

function emitCurrentBounds() {
  if (!mapInstance) return
  const bounds = mapInstance.getBounds()
  emit('boundsChange', {
    south: bounds.getSouth(),
    north: bounds.getNorth(),
    west: bounds.getWest(),
    east: bounds.getEast(),
  })
}

function handleMapMoveEnd() {
  if (suppressProgrammaticMoveEnd) {
    suppressProgrammaticMoveEnd = false
    if (programmaticMoveTimer) clearTimeout(programmaticMoveTimer)
    programmaticMoveTimer = null
    return
  }
  emitCurrentBounds()
}

function handleUserMapMoveStart() {
  hasAutoFittedContent = true
  suppressProgrammaticMoveEnd = false
  if (programmaticMoveTimer) clearTimeout(programmaticMoveTimer)
  programmaticMoveTimer = null
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

function mapContentKey(): string {
  return JSON.stringify({
    markers: props.markers.map((item) => ({
      id: item.id,
      latitude: item.latitude,
      longitude: item.longitude,
      title: item.title,
      tone: item.tone ?? 'primary',
      actionHref: item.actionHref ?? null,
      actionLabel: item.actionLabel ?? null,
      details: item.details ?? [],
    })),
    paths: props.paths.map((path) => ({
      id: path.id,
      label: path.label ?? null,
      tone: path.tone ?? 'primary',
      points: path.points,
    })),
  })
}

function renderMarkers() {
  if (!mapInstance) return
  const contentKey = mapContentKey()
  if (contentKey === renderedContentKey) return

  const popupToRestore = openPopupMarkerId
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
    }).addTo(mapInstance as Map)

    marker.on('click', () => {
      openPopupMarkerId = item.id
      if (!item.actionHref) emit('markerSelect', item.id)
      centerMarkerPopup(item)
      queueMicrotask(() => {
        if (mapInstance) marker.openPopup()
      })
    })
    marker.on('popupclose', () => {
      if (openPopupMarkerId === item.id) openPopupMarkerId = null
    })

    marker.bindPopup(popupContent(item), {
      minWidth: 190,
      autoPan: false,
    })

    if (popupToRestore === item.id) {
      openPopupMarkerId = item.id
      queueMicrotask(() => {
        if (mapInstance) marker.openPopup()
      })
    }

    return marker
  })

  renderedContentKey = contentKey

  if (props.focusedCenter) {
    focusSelectedLocation(false)
  } else if (!props.viewportBounds && !hasAutoFittedContent) {
    const allCoordinates = [
      ...props.markers.map((item) => [item.latitude, item.longitude] as [number, number]),
      ...props.paths.flatMap((path) =>
        path.points.map((point) => [point.latitude, point.longitude] as [number, number]),
      ),
    ]

    if (allCoordinates.length === 1) {
      const coordinate = allCoordinates[0]
      if (coordinate) {
        mapInstance.setView(coordinate, 15)
        hasAutoFittedContent = true
      }
    } else if (allCoordinates.length > 1) {
      const bounds = latLngBounds(allCoordinates)
      mapInstance.fitBounds(bounds, { padding: [40, 40], maxZoom: 15, animate: false })
      hasAutoFittedContent = true
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

  mapInstance.on('moveend', handleMapMoveEnd)
  mapInstance.on('dragstart zoomstart', handleUserMapMoveStart)

  renderMarkers()
  fitViewportBounds(false)

  if (typeof ResizeObserver !== 'undefined') {
    resizeObserver = new ResizeObserver(() =>
      mapInstance?.invalidateSize({ animate: false, pan: false }),
    )
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
    props.viewportBounds?.south ?? null,
    props.viewportBounds?.north ?? null,
    props.viewportBounds?.west ?? null,
    props.viewportBounds?.east ?? null,
  ],
  ([south, north, west, east], previous) => {
    if (south == null || north == null || west == null || east == null) return
    const changed =
      !previous ||
      south !== previous[0] ||
      north !== previous[1] ||
      west !== previous[2] ||
      east !== previous[3]
    if (changed) fitViewportBounds(true)
  },
  { flush: 'post' },
)

watch(
  () =>
    [
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
  if (programmaticMoveTimer) clearTimeout(programmaticMoveTimer)
  resizeObserver?.disconnect()
  clearMarkers()
  clearPaths()
  renderedContentKey = null
  mapInstance?.remove()
  mapInstance = null
})
</script>

<template>
  <div class="common-map">
    <div ref="mapElement" class="common-map__canvas" :aria-label="mapLabel"></div>
    <slot />
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
  pointer-events: none;
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
  display: flex;
  align-items: center;
  justify-content: center;
  border: 0;
  background: transparent;
  cursor: pointer;
  touch-action: manipulation;
}

:global(.roady-map-marker) {
  position: relative;
  display: block;
  box-sizing: border-box;
  width: 2.8rem;
  height: 2.8rem;
  border: 0.4rem solid var(--roady-surface-default);
  border-radius: 50% 50% 50% 0;
  box-shadow: 0 0.3rem 0.8rem color-mix(in srgb, var(--roady-text-primary) 28%, transparent);
  background: var(--roady-brand-secondary);
  transform: rotate(-45deg);
  pointer-events: none;
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
  pointer-events: none;
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
  min-width: 0;
  font-size: var(--krds-pc-font-size-body-small);
}

:global(.roady-map-popup__header) {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1.2rem;
  padding-bottom: 0.8rem;
  border-bottom: 1px solid var(--roady-border-default);
}

:global(.roady-map-popup__action) {
  flex-shrink: 0;
  color: var(--roady-brand-secondary);
  font-size: var(--krds-pc-font-size-label-small);
  font-weight: var(--krds-font-weight-bold);
  text-decoration: underline;
  text-underline-offset: 0.2rem;
}

:global(.roady-map-popup__action:hover) {
  color: var(--roady-brand-primary);
}

:global(.roady-map-popup__action:focus-visible) {
  border-radius: 0.2rem;
  outline: 0.2rem solid var(--roady-brand-secondary);
  outline-offset: 0.2rem;
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
