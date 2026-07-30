import http from './http'
import type { Robot, RobotCommand, RobotCommandType } from '@/types/robot'

export const robotsApi = {
  async list() {
    const { data } = await http.get<Robot[]>('/robots')
    return data
  },

  async get(robotId: number) {
    const { data } = await http.get<Robot>(`/robots/${robotId}`)
    return data
  },

  async command(robotId: number, commandType: RobotCommandType) {
    const { data } = await http.post<RobotCommand>(`/robots/${robotId}/commands`, {
      commandType,
    })
    return data
  },

  async commands(robotId: number) {
    const { data } = await http.get<RobotCommand[]>(`/robots/${robotId}/commands`)
    return data
  },
}
