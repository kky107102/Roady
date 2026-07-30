export type DamageStatus =
  | 'COLLECTED'
  | 'REVIEW_REQUIRED'
  | 'RECEIVED'
  | 'REPAIR_SCHEDULED'
  | 'REPAIRING'
  | 'REPAIR_COMPLETED'
  | 'REPAIR_NOT_REQUIRED'

export interface DamageListItem {
  id: number
  robotId: number | null
  assignedTo: number | null
  description: string | null
  latitude: number | null
  longitude: number | null
  capturedAt: string | null
  currentStatus: DamageStatus
  imageCount: number
  damageScore: number | null
  repairRequired: boolean | null
  repairPriority: string | null
  confidenceScore: number | null
  createdAt: string
}

export interface DamageSearchResponse {
  content: DamageListItem[]
  page: number
  size: number
  totalElements: number
  totalPages: number
}

export interface DamageImage {
  id: number
  damageId: number
  sortOrder: number
  originalFilename: string
  contentType: string
  sizeBytes: number
  createdAt: string
}

export interface DamageDetail {
  id: number
  robotId: number | null
  reportedBy: number | null
  assignedTo: number | null
  description: string | null
  latitude: number | null
  longitude: number | null
  capturedAt: string | null
  currentStatus: DamageStatus
  imageCount: number
  images: DamageImage[]
  createdAt: string
  updatedAt: string
}

export interface DamageAnalysis {
  id: number
  damageId: number
  damaged: boolean | null
  damageScore: number | null
  repairRequired: boolean | null
  repairPriority: string | null
  confidenceScore: number | null
  analysisStatus: string
  analyzedAt: string | null
  createdAt: string
}
