// NOTE: Backend state transition APIs are not yet implemented (2026-08-04).
// Required endpoints:
//   POST /api/damages/{id}/repair-request    (REQUESTED → REPAIR_IN_PROGRESS)
//   DELETE /api/damages/{id}/repair-request  (REPAIR_IN_PROGRESS → REQUESTED)
//   POST /api/damages/{id}/repair-completion (REPAIR_IN_PROGRESS → REPAIR_COMPLETED)

export interface RepairRequestPayload {
  note?: string | null
}

export interface RepairCompletePayload {
  completedAt: string // YYYY-MM-DD
}
