import { afterEach, describe, expect, it, vi } from 'vitest'
import { mount } from '@vue/test-utils'

const leaflet = vi.hoisted(() => {
  const markerInstances: Array<Record<string, ReturnType<typeof vi.fn>>> = []
  const mapInstance = {
    remove: vi.fn(),
    setView: vi.fn(),
    panTo: vi.fn(),
    fitBounds: vi.fn(),
    getBounds: vi.fn(() => ({
      getSouth: () => 37.4,
      getNorth: () => 37.6,
      getWest: () => 126.8,
      getEast: () => 127.1,
    })),
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
    expect(leaflet.mapInstance.panTo).toHaveBeenCalledWith([37.51, 127], {
      animate: true,
      duration: 0.2,
    })
    expect(wrapper.emitted('markerSelect')).toBeUndefined()
    expect(marker?.openPopup).toHaveBeenCalledOnce()

    const moveEndHandler = leaflet.mapInstance.on.mock.calls.find(
      ([event]) => event === 'moveend',
    )?.[1] as (() => void) | undefined
    moveEndHandler?.()
    expect(wrapper.emitted('boundsChange')).toBeUndefined()

    wrapper.unmount()
  })

  it('emits a selection directly for markers without a popup action', async () => {
    const wrapper = mount(CommonMap, {
      props: {
        markers: [{ id: 10, latitude: 37.5, longitude: 127, title: 'damage #10' }],
      },
    })

    const marker = leaflet.markerInstances[0]
    const clickHandler = marker?.on?.mock.calls.find(([event]) => event === 'click')?.[1] as
      (() => void) | undefined
    clickHandler?.()
    await Promise.resolve()

    expect(wrapper.emitted('markerSelect')).toEqual([[10]])
    expect(marker?.openPopup).toHaveBeenCalledOnce()
    expect(leaflet.mapInstance.setView).toHaveBeenCalledTimes(1)

    wrapper.unmount()
  })

  it('emits a selection only when the popup action is clicked', async () => {
    const wrapper = mount(CommonMap, {
      props: {
        markers: [
          {
            id: 10,
            latitude: 37.5,
            longitude: 127,
            title: 'damage #10',
            actionHref: '/damages?damageId=10',
          },
        ],
      },
    })

    const popup = leaflet.markerInstances[0]?.bindPopup?.mock.calls[0]?.[0] as HTMLElement
    popup.querySelector<HTMLAnchorElement>('.roady-map-popup__action')?.click()
    await wrapper.vm.$nextTick()

    expect(wrapper.emitted('markerSelect')).toEqual([[10]])

    wrapper.unmount()
  })

  it('does not reset the viewport when marker data refreshes', async () => {
    const wrapper = mount(CommonMap, {
      props: {
        markers: [{ id: 10, latitude: 37.5, longitude: 127, title: 'damage #10' }],
      },
    })

    expect(leaflet.mapInstance.setView).toHaveBeenCalledTimes(1)
    const clickHandler = leaflet.markerInstances[0]?.on?.mock.calls.find(
      ([event]) => event === 'click',
    )?.[1] as (() => void) | undefined
    clickHandler?.()
    await Promise.resolve()

    await wrapper.setProps({
      markers: [
        { id: 10, latitude: 37.5, longitude: 127, title: 'damage #10' },
        { id: 11, latitude: 37.51, longitude: 127.01, title: 'damage #11' },
      ],
    })

    expect(leaflet.mapInstance.setView).toHaveBeenCalledTimes(1)
    expect(leaflet.mapInstance.fitBounds).not.toHaveBeenCalled()
    expect(leaflet.markerInstances[1]?.openPopup).toHaveBeenCalledOnce()

    wrapper.unmount()
  })

  it('동일한 마커 데이터가 다시 전달되면 열린 팝업을 재생성하지 않는다', async () => {
    const markerItem = {
      id: 10,
      latitude: 37.5,
      longitude: 127,
      title: 'damage #10',
      details: [{ label: '상태', value: '미확인' }],
    }
    const wrapper = mount(CommonMap, {
      props: { markers: [markerItem] },
    })
    const marker = leaflet.markerInstances[0]
    const clickHandler = marker?.on?.mock.calls.find(([event]) => event === 'click')?.[1] as
      (() => void) | undefined
    clickHandler?.()
    await Promise.resolve()

    await wrapper.setProps({
      markers: [{ ...markerItem, details: markerItem.details.map((detail) => ({ ...detail })) }],
    })

    expect(leaflet.createMarker).toHaveBeenCalledOnce()
    expect(marker?.remove).not.toHaveBeenCalled()
    expect(marker?.openPopup).toHaveBeenCalledOnce()

    wrapper.unmount()
  })

  it('지정한 행정구역 경계로 이동하고 현재 지도 경계를 알린다', async () => {
    const wrapper = mount(CommonMap, {
      props: {
        viewportBounds: { south: 37.4, north: 37.6, west: 126.8, east: 127.1 },
      },
    })

    expect(leaflet.mapInstance.fitBounds).toHaveBeenCalledWith(undefined, {
      padding: [32, 32],
      animate: false,
    })

    const moveEndHandler = leaflet.mapInstance.on.mock.calls.find(
      ([event]) => event === 'moveend',
    )?.[1] as (() => void) | undefined
    moveEndHandler?.()
    await wrapper.vm.$nextTick()

    expect(wrapper.emitted('boundsChange')).toEqual([
      [{ south: 37.4, north: 37.6, west: 126.8, east: 127.1 }],
    ])

    wrapper.unmount()
  })
})
