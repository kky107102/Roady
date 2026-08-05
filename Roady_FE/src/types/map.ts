export interface MapMarkerDetail {
  label: string
  value: string
}

export interface MapMarkerItem {
  id: string | number
  latitude: number
  longitude: number
  title: string
  details?: MapMarkerDetail[]
  tone?: 'primary' | 'success' | 'warning' | 'danger' | 'neutral'
  actionLabel?: string
  actionHref?: string
}

export interface MapCoordinate {
  latitude: number
  longitude: number
}

export interface MapBounds {
  south: number
  north: number
  west: number
  east: number
}

export interface MapRegionOption {
  code: string
  name: string
  bounds: MapBounds
}

export interface AssignedMapRegions {
  regionCode: string
  regionName: string
  bounds: MapBounds
  emds: MapRegionOption[]
}

export interface MapPathItem {
  id: string | number
  points: MapCoordinate[]
  tone?: 'primary' | 'success' | 'warning' | 'danger' | 'neutral'
  label?: string
}
