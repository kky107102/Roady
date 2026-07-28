export type RobotOperationStatus =
  | 'STANDBY'
  | 'MOVING'
  | 'INSPECTING'
  | 'CHARGING'
  | 'STOPPED'
  | 'ERROR'

export type RobotConnectionStatus = 'CONNECTED' | 'DISCONNECTED'

export interface RobotLatestStatus {
  latitude: number | null
  longitude: number | null
  batteryLevel: number | null
  operationStatus: RobotOperationStatus | null
  connectionStatus: RobotConnectionStatus | null
  recordedAt: string | null
}

export interface Robot {
  id: number
  userId: number
  name: string
  serialNumber: string
  status: RobotOperationStatus
  active: boolean
  latestStatus: RobotLatestStatus | null
  createdAt: string
  updatedAt: string
}
