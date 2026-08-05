import { afterEach, describe, expect, it, vi } from 'vitest'
import { mount } from '@vue/test-utils'

const leaflet = vi.hoisted(() => {
  const markerInstances: Array<Record<string, ReturnType<typeof vi.fn>>> = []
  const mapInstance = {
    remove: vi.fn(),
    setView: vi.fn(),
    fitBounds: vi.fn(),
    getSize: vi.fn(() => ({ x: 800 })),
    getZoom: vi.fn(() => 15),
    project: vi.fn(() => ({ subtract: vi.fn(() => ({ x: 100, y: 20 })) })),
    unproject: vi.fn(() => [37.51, 127]),
    on: vi.fn(),
    stop: vi.fn(),
    invalidateSize: vi.fn(),
  }

  return {
    markerInstances,
    mapInstance,
    divIcon: vi.fn((options) => options),
    createMap: vi.fn(() => mapInstance),
    createMarker: vi.fn(() => {
      const marker: Record<string, ReturnType<typeof vi.fn>> = {}
      const popup = { on: vi.fn() }
      marker.bindPopup = vi.fn(() => marker)
      marker.addTo = vi.fn(() => marker)
      marker.on = vi.fn(() => marker)
      marker.getPopup = vi.fn(() => popup)
      marker.openPopup = vi.fn(() => marker)
      marker.setOpacity = vi.fn(() => marker)
      marker.setZIndexOffset = vi.fn(() => marker)
      marker.remove = vi.fn()
      markerInstances.push(marker)
      return marker
    }),
  }
})

vi.mock('leaflet', () => ({
  divIcon: leaflet.divIcon,
  latLngBounds: vi.fn(),
  map: leaflet.createMap,
  marker: leaflet.createMarker,
  polyline: vi.fn(),
  tileLayer: vi.fn(() => ({ addTo: vi.fn() })),
}))

const { default: CommonMap } = await import('@/components/common/CommonMap.vue')

afterEach(() => {
  vi.clearAllMocks()
  leaflet.markerInstances.length = 0
})

describe('CommonMap', () => {
  it('보이는 핀과 일치하는 44px 클릭 영역을 사용하고 팝업 자동 이동을 막는다', () => {
    const wrapper = mount(CommonMap, {
      props: {
        markers: [
          {
            id: 10,
            latitude: 37.5,
            longitude: 127,
            title: '탐지 사건 #10',
            actionHref: '/damages?review=pending&damageId=10',
          },
        ],
      },
    })

    expect(leaflet.divIcon).toHaveBeenCalledWith(
      expect.objectContaining({
        iconSize: [44, 44],
        iconAnchor: [22, 42],
        popupAnchor: [0, -38],
      }),
    )
    expect(leaflet.markerInstances[0]?.bindPopup).toHaveBeenCalledWith(
      expect.any(HTMLElement),
      expect.objectContaining({ autoPan: false }),
    )

    wrapper.unmount()
  })

  it('마커를 첫 클릭에 지도 중앙으로 이동한다', async () => {
    const wrapper = mount(CommonMap, {
      props: {
        centerPopupOnSelect: true,
        markers: [
          {
            id: 10,
            latitude: 37.5,
            longitude: 127,
            title: '탐지 사건 #10',
            actionHref: '/damages?review=pending&damageId=10',
          },
        ],
      },
    })

    const marker = leaflet.markerInstances[0]
    const clickHandler = marker?.on?.mock.calls.find(([event]) => event === 'click')?.[1] as
      (() => void) | undefined
    expect(clickHandler).toBeTypeOf('function')
    clickHandler?.()
    await Promise.resolve()
    await wrapper.vm.$nextTick()

    expect(leaflet.mapInstance.stop).toHaveBeenCalledOnce()
    expect(leaflet.mapInstance.setView).toHaveBeenCalledWith([37.51, 127], 15, {
      animate: false,
    })
    expect(marker?.openPopup).toHaveBeenCalledOnce()

    wrapper.unmount()
  })
})
