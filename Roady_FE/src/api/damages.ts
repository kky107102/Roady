import http from './http'
import type { DamageSearchResponse, DamageStatus, DamageDetail, DamageAnalysis } from '@/types/damage'

export interface DamageListQuery {
  from?: string
  to?: string
  status?: DamageStatus
  robotId?: number
  assignedTo?: number
  page?: number
  size?: number
}

// 상세 조회 결과를 메모리에 캐시 (목록 → 상세 패널 전환 시 재요청 없음)
const detailCache = new Map<number, DamageDetail>()

export const damagesApi = {
  async list(query?: DamageListQuery) {
    const { data } = await http.get<DamageSearchResponse>('/damages', { params: query })
    return data
  },

  async getDetail(damageId: number): Promise<DamageDetail> {
    if (detailCache.has(damageId)) return detailCache.get(damageId)!
    const { data } = await http.get<DamageDetail>(`/damages/${damageId}`)
    detailCache.set(damageId, data)
    return data
  },

  async getImageContent(damageId: number, imageId: number): Promise<Blob> {
    const { data } = await http.get<Blob>(`/damages/${damageId}/images/${imageId}/content`, {
      responseType: 'blob',
    })
    return data
  },

  async getAnalysisJobs(damageId: number): Promise<DamageAnalysis[]> {
    const { data } = await http.get<DamageAnalysis[]>(`/damages/${damageId}/analysis-jobs`)
    return data
  },

  async updateReview(
    damageId: number,
    status: 'AI_ANALYZED' | 'REQUESTED' | 'CANCELED',
    processingPriority?: string | null,
    reviewDamageType?: string | null,
    reviewNote?: string | null,
  ): Promise<void> {
    await http.patch(`/damages/${damageId}/review`, {
      status,
      processingPriority: processingPriority || null,
      reviewDamageType: reviewDamageType || null,
      reviewNote: reviewNote?.trim() || null,
    })
    detailCache.delete(damageId)
  },

  clearDetailCache(damageId?: number) {
    if (damageId == null) {
      detailCache.clear()
      return
    }
    detailCache.delete(damageId)
  },
}
