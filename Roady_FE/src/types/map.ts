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
