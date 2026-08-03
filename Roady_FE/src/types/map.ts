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
}

export interface MapCoordinate {
  latitude: number
  longitude: number
}

export interface MapPathItem {
  id: string | number
  points: MapCoordinate[]
  tone?: 'primary' | 'success' | 'warning' | 'danger' | 'neutral'
  label?: string
}
