export type RobotOperationStatus =
  | 'STANDBY'
  | 'MOVING'
  | 'INSPECTING'
  | 'CHARGING'
  | 'STOPPED'
  | 'ERROR'

export type RobotConnectionStatus = 'CONNECTED' | 'DISCONNECTED'

export type RobotCommandType =
  | 'START_PATROL'
  | 'STOP_PATROL'
  | 'EMERGENCY_STOP'
  | 'RETURN_HOME'

export type RobotCommandStatus =
  | 'PENDING'
  | 'IN_PROGRESS'
  | 'SUCCEEDED'
  | 'FAILED'
  | 'CANCELED'

export interface RobotCommand {
  id: number
  robotId: number
  requestedBy: number
  commandType: RobotCommandType
  commandStatus: RobotCommandStatus
  resultMessage: string | null
  requestedAt: string
  completedAt: string | null
}

export interface RobotLatestStatus {
  id: number
  latitude: number | null
  longitude: number | null
  batteryLevel: number | null
  operationStatus: RobotOperationStatus | null
  connectionStatus: RobotConnectionStatus | null
  errorCode: string | null
  errorMessage: string | null
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
