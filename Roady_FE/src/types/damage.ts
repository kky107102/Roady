export type DamageStatus =
  | 'COLLECTED'
  | 'AI_ANALYZING'
  | 'AI_ANALYZED'
  | 'REQUESTED'
  | 'REPAIR_IN_PROGRESS'
  | 'REPAIR_COMPLETED'
  | 'CANCELED'

export interface DamageListItem {
  id: number
  robotId: number | null
  assignedTo: number | null
  description: string | null
  addressName?: string | null
  roadAddressName?: string | null
  regionCode?: string | null
  region1DepthName?: string | null
  region2DepthName?: string | null
  region3DepthName?: string | null
  geocodedAt?: string | null
  latitude: number | null
  longitude: number | null
  capturedAt: string | null
  currentStatus: DamageStatus
  processingPriority?: string | null
  reviewDamageType?: string | null
  reviewNote?: string | null
  imageCount: number
  damageScore: number | null
  damageType?: string | null
  repairRequired: boolean | null
  repairPriority: string | null
  confidenceScore: number | null
  createdAt: string
  updatedAt?: string | null
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
  addressName?: string | null
  roadAddressName?: string | null
  regionCode?: string | null
  region1DepthName?: string | null
  region2DepthName?: string | null
  region3DepthName?: string | null
  geocodedAt?: string | null
  latitude: number | null
  longitude: number | null
  capturedAt: string | null
  currentStatus: DamageStatus
  processingPriority?: string | null
  reviewDamageType?: string | null
  reviewNote?: string | null
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
  damageType: string | null
  repairRequired: boolean | null
  repairPriority: string | null
  confidenceScore: number | null
  analysisStatus: string
  analyzedAt: string | null
  createdAt: string
}
