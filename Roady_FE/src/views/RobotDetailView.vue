<script setup lang="ts">
import axios from 'axios'
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { robotsApi } from '@/api/robots'
import EmptyState from '@/components/common/EmptyState.vue'
import ErrorState from '@/components/common/ErrorState.vue'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import CommonMap from '@/components/common/CommonMap.vue'
import type {
  Robot,
  RobotCommand,
  RobotCommandType,
  RobotOperationStatus,
} from '@/types/robot'
import {
  connectionBadge,
  formatBattery,
  formatCoordinate,
  formatDateTime,
  operationBadge,
} from '@/utils/robotDisplay'
import { toRobotMapMarkers } from '@/utils/robotMap'

const route = useRoute()
const robot = ref<Robot | null>(null)
const loading = ref(true)
const error = ref(false)
const notFound = ref(false)
const commandLoading = ref(false)
const commandError = ref('')
const currentCommand = ref<RobotCommand | null>(null)
const optimisticOperationStatus = ref<RobotOperationStatus | null>(null)
let commandPollTimer: ReturnType<typeof setInterval> | null = null
const robotId = computed(() => Number(route.params.id))
const currentOperationStatus = computed(
  () => optimisticOperationStatus.value ?? robot.value?.latestStatus?.operationStatus ?? null,
)
const isInspecting = computed(() => currentOperationStatus.value === 'INSPECTING')
const isOperating = computed(() => currentOperationStatus.value === 'MOVING')
const commandInProgress = computed(
  () =>
    currentCommand.value?.commandStatus === 'PENDING' ||
    currentCommand.value?.commandStatus === 'IN_PROGRESS',
)
const returnInProgress = computed(
  () => currentCommand.value?.commandType === 'RETURN_HOME' && commandInProgress.value,
)
const emergencyInProgress = computed(
  () => currentCommand.value?.commandType === 'EMERGENCY_STOP' && commandInProgress.value,
)
const startInProgress = computed(
  () => currentCommand.value?.commandType === 'START_PATROL' && commandInProgress.value,
)
const canResumeAfterEmergency = computed(
  () =>
    currentCommand.value?.commandType === 'EMERGENCY_STOP' &&
    currentCommand.value.commandStatus === 'SUCCEEDED',
)
const robotMarkers = computed(() => robot.value ? toRobotMapMarkers([robot.value]) : [])
const commandFeedbackLines = computed(() => {
  const command = currentCommand.value
  if (!command) return []

  const labels: Record<RobotCommandType, string> = {
    START_PATROL: '운행 시작',
    STOP_PATROL: '운행 중지',
    RETURN_HOME: '스테이션 복귀',
    EMERGENCY_STOP: '긴급 정지',
  }
  const label = labels[command.commandType]

  if (command.commandStatus === 'PENDING') {
    return [`${label} 명령을 전송했습니다.`, '로봇 응답을 기다리는 중입니다.']
  }
  if (command.commandStatus === 'IN_PROGRESS') {
    if (command.commandType === 'RETURN_HOME') return ['스테이션으로 복귀 중입니다.']
    if (command.commandType === 'EMERGENCY_STOP') return ['긴급 정지를 처리 중입니다.']
    if (command.commandType === 'START_PATROL') return ['운행 시작을 처리 중입니다.']
    return ['명령을 처리 중입니다.']
  }
  if (command.commandStatus === 'SUCCEEDED') return [`${label} 명령 처리가 완료되었습니다.`]
  if (command.commandStatus === 'FAILED') {
    return command.resultMessage
      ? [`${label} 명령 처리에 실패했습니다.`, command.resultMessage]
      : [`${label} 명령 처리에 실패했습니다.`]
  }
  return [`${label} 명령이 취소되었습니다.`]
})

async function fetchRobot() {
  loading.value = true
  error.value = false
  notFound.value = false
  robot.value = null
  optimisticOperationStatus.value = null
  commandError.value = ''
  currentCommand.value = null
  stopCommandPolling()

  if (!Number.isInteger(robotId.value) || robotId.value <= 0) {
    notFound.value = true
    loading.value = false
    return
  }

  try {
    robot.value = await robotsApi.get(robotId.value)
  } catch (requestError) {
    if (axios.isAxiosError(requestError) && requestError.response?.status === 404) {
      notFound.value = true
    } else {
      error.value = true
    }
  } finally {
    loading.value = false
  }
}

function stopCommandPolling() {
  if (commandPollTimer !== null) {
    clearInterval(commandPollTimer)
    commandPollTimer = null
  }
}

function applyCommandOutcome(command: RobotCommand) {
  if (command.commandType === 'START_PATROL') {
    if (['PENDING', 'IN_PROGRESS', 'SUCCEEDED'].includes(command.commandStatus)) {
      optimisticOperationStatus.value = 'MOVING'
    } else {
      optimisticOperationStatus.value = null
    }
  }

  if (
    command.commandType === 'EMERGENCY_STOP' &&
    command.commandStatus === 'SUCCEEDED'
  ) {
    optimisticOperationStatus.value = 'STOPPED'
  }
}

async function refreshCommandStatus() {
  if (!robot.value || !currentCommand.value) return

  try {
    const commands = await robotsApi.commands(robot.value.id)
    const updatedCommand = commands.find((command) => command.id === currentCommand.value?.id)
    if (!updatedCommand) return

    currentCommand.value = updatedCommand
    applyCommandOutcome(updatedCommand)
    if (!['PENDING', 'IN_PROGRESS'].includes(updatedCommand.commandStatus)) {
      stopCommandPolling()
    }
  } catch {
    // 일시적인 상태 조회 실패는 다음 주기에서 다시 확인한다.
  }
}

function startCommandPolling() {
  stopCommandPolling()
  commandPollTimer = setInterval(refreshCommandStatus, 2_000)
}

async function sendCommand(commandType: RobotCommandType) {
  if (!robot.value || commandLoading.value) return

  commandLoading.value = true
  commandError.value = ''

  try {
    currentCommand.value = await robotsApi.command(robot.value.id, commandType)
    applyCommandOutcome(currentCommand.value)
    if (commandInProgress.value) startCommandPolling()
  } catch {
    commandError.value = '원격 제어 명령을 전송하지 못했습니다. 잠시 후 다시 시도해 주세요.'
  } finally {
    commandLoading.value = false
  }
}

onMounted(fetchRobot)
onUnmounted(stopCommandPolling)
watch(robotId, fetchRobot)
</script>

<template>
  <div class="robot-detail">
    <RouterLink class="back-link" :to="{ name: 'robots' }">← 로봇 목록</RouterLink>

    <LoadingSpinner v-if="loading" label="로봇 상세 정보를 불러오는 중" />
    <EmptyState
      v-else-if="notFound"
      title="존재하지 않는 로봇입니다."
      description="주소를 확인하거나 로봇 목록으로 돌아가 주세요."
    >
      <RouterLink class="krds-btn medium primary" :to="{ name: 'robots' }">목록으로</RouterLink>
    </EmptyState>
    <ErrorState
      v-else-if="error"
      message="로봇 상세 정보를 불러오지 못했습니다."
      retry-label="다시 시도"
      @retry="fetchRobot"
    />

    <template v-else-if="robot">
      <header class="page-header">
        <div>
          <h1>{{ robot.name }}</h1>
          <p>{{ robot.serialNumber }}</p>
        </div>
        <div class="remote-control" aria-label="로봇 원격 제어">
          <p v-if="isInspecting" class="inspection-notice">
            현재 점검 중이라 원격 운행이 불가합니다.
          </p>
          <div v-else-if="isOperating" class="control-actions">
            <button
              type="button"
              class="control-button return-button"
              :disabled="
                commandLoading || startInProgress || returnInProgress || emergencyInProgress
              "
              @click="sendCommand('RETURN_HOME')"
            >
              {{ returnInProgress ? '복귀 요청됨…' : '스테이션 복귀' }}
            </button>
            <button
              type="button"
              class="control-button emergency-button"
              :disabled="commandLoading || startInProgress || emergencyInProgress"
              @click="sendCommand('EMERGENCY_STOP')"
            >
              {{ emergencyInProgress ? '정지 확인 중…' : '긴급 정지' }}
            </button>
          </div>
          <button
            v-else
            type="button"
            class="control-button start-button"
            :disabled="commandLoading"
            @click="sendCommand('START_PATROL')"
          >
            {{
              commandLoading
                ? '명령 전송 중'
                : canResumeAfterEmergency
                  ? '다시 운행'
                  : '운행 시작'
            }}
          </button>
          <p
            v-if="commandFeedbackLines.length > 0"
            class="command-feedback"
            :class="{ 'is-failed': currentCommand?.commandStatus === 'FAILED' }"
            role="status"
          >
            <span v-for="line in commandFeedbackLines" :key="line">{{ line }}</span>
          </p>
          <p v-if="commandError" class="command-error" role="alert">{{ commandError }}</p>
        </div>
      </header>

      <div class="overview-grid">
        <section class="detail-card map-card" aria-labelledby="robot-map-title">
          <div class="section-header">
            <div>
              <h2 id="robot-map-title">로봇 위치</h2>
              <p>현재 수집된 로봇 위치를 지도에서 확인합니다.</p>
            </div>
          </div>
          <CommonMap
            class="robot-detail-map"
            :markers="robotMarkers"
            :map-label="`${robot.name} 최신 위치 지도`"
            empty-message="수집된 로봇 위치 정보가 없습니다."
          />
        </section>

        <section class="detail-card basic-card" aria-labelledby="basic-info-title">
          <h2 id="basic-info-title">기본 정보</h2>
          <dl class="basic-info-list">
            <div><dt>로봇 ID</dt><dd>{{ robot.id }}</dd></div>
            <div><dt>로봇명</dt><dd>{{ robot.name }}</dd></div>
            <div><dt>시리얼 번호</dt><dd>{{ robot.serialNumber }}</dd></div>
            <div><dt>운영 상태</dt><dd>{{ robot.active ? '활성' : '비활성' }}</dd></div>
            <div><dt>등록 시각</dt><dd>{{ formatDateTime(robot.createdAt) }}</dd></div>
            <div><dt>정보 수정 시각</dt><dd>{{ formatDateTime(robot.updatedAt) }}</dd></div>
          </dl>
        </section>
      </div>

      <section class="detail-card" aria-labelledby="latest-status-title">
        <div class="section-header">
          <div>
            <h2 id="latest-status-title">최신 상태</h2>
            <p v-if="robot.latestStatus">
              {{ formatDateTime(robot.latestStatus.recordedAt) }} 기준
            </p>
          </div>
        </div>

        <EmptyState
          v-if="!robot.latestStatus"
          title="수집된 최신 상태가 없습니다."
          description="로봇에서 상태 정보가 수집되면 이곳에 표시됩니다."
        />
        <dl v-else class="status-grid">
          <div>
            <dt>운행 상태</dt>
            <dd>
              <StatusBadge
                :type="operationBadge(robot.latestStatus.operationStatus).type"
                :label="operationBadge(robot.latestStatus.operationStatus).label"
              />
            </dd>
          </div>
          <div>
            <dt>연결 상태</dt>
            <dd>
              <StatusBadge
                :type="connectionBadge(robot.latestStatus.connectionStatus).type"
                :label="connectionBadge(robot.latestStatus.connectionStatus).label"
              />
            </dd>
          </div>
          <div>
            <dt>배터리</dt>
            <dd :class="{ 'low-battery': robot.latestStatus.batteryLevel != null && robot.latestStatus.batteryLevel <= 10 }">
              {{ formatBattery(robot.latestStatus.batteryLevel) }}
            </dd>
          </div>
          <div>
            <dt>마지막 갱신</dt>
            <dd>{{ formatDateTime(robot.latestStatus.recordedAt) }}</dd>
          </div>
          <div>
            <dt>마지막 위치 위도</dt>
            <dd>{{ formatCoordinate(robot.latestStatus.latitude) }}</dd>
          </div>
          <div>
            <dt>마지막 위치 경도</dt>
            <dd>{{ formatCoordinate(robot.latestStatus.longitude) }}</dd>
          </div>
        </dl>
      </section>
    </template>
  </div>
</template>

<style scoped>
.robot-detail {
  display: flex;
  flex-direction: column;
  gap: 2rem;
  padding: 2.4rem 3.2rem;
}

.back-link {
  align-self: flex-start;
  color: var(--roady-brand-secondary);
  font-size: var(--krds-pc-font-size-body-small);
  font-weight: var(--krds-font-weight-bold);
  text-decoration: none;
}

.page-header,
.section-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 2rem;
}

.page-header h1,
.detail-card h2 {
  margin: 0;
}

.page-header h1 {
  font-size: var(--krds-pc-font-size-heading-medium);
}

.remote-control {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 0.8rem;
}

.control-actions {
  display: flex;
  gap: 0.8rem;
}

.control-button {
  min-width: 11rem;
  height: 4.8rem;
  padding: 0 1.6rem;
  border-radius: 0.6rem;
  font-size: var(--krds-pc-font-size-body-small);
  font-weight: var(--krds-font-weight-bold);
  cursor: pointer;
}

.control-button:disabled {
  cursor: wait;
  opacity: 0.55;
}

.start-button {
  border: 1px solid var(--roady-brand-primary);
  color: var(--roady-surface-default);
  background: var(--roady-brand-primary);
}

.start-button:hover:not(:disabled) {
  background: var(--roady-brand-primary-hover);
}

.return-button {
  border: 1px solid var(--roady-brand-secondary);
  color: var(--roady-brand-secondary);
  background: var(--roady-surface-default);
}

.emergency-button {
  border: 1px solid var(--roady-status-danger);
  color: var(--roady-surface-default);
  background: var(--roady-status-danger);
}

.inspection-notice,
.command-feedback,
.command-error {
  max-width: 52rem;
  margin: 0;
  font-size: var(--krds-pc-font-size-body-small);
  text-align: right;
}

.command-feedback {
  color: var(--roady-text-secondary);
}

.command-feedback span {
  display: block;
  white-space: nowrap;
}

.command-feedback.is-failed {
  color: var(--roady-status-danger);
}

.inspection-notice {
  color: var(--roady-status-warning-text);
  font-weight: var(--krds-font-weight-bold);
}

.command-error {
  color: var(--roady-status-danger);
}

.page-header p,
.section-header p {
  margin: 0.5rem 0 0;
  color: var(--roady-text-tertiary);
  font-size: var(--krds-pc-font-size-body-small);
}

.detail-card {
  display: flex;
  flex-direction: column;
  padding: 2.4rem;
  border: 1px solid var(--roady-border-default);
  border-radius: 0.8rem;
  background: var(--roady-surface-default);
}

.detail-card h2 {
  font-size: var(--krds-pc-font-size-heading-xsmall);
}

.overview-grid {
  display: grid;
  grid-template-columns: minmax(0, 2fr) minmax(30rem, 1fr);
  gap: 1.6rem;
  min-height: 36rem;
}

.map-card {
  gap: 1.6rem;
}

.robot-detail-map {
  flex: 1;
  min-height: 26rem;
}

.basic-info-list {
  display: flex;
  flex-direction: column;
  margin: 2rem 0 0;
  border-top: 1px solid var(--roady-border-default);
}

.basic-info-list div {
  display: grid;
  grid-template-columns: 11rem minmax(0, 1fr);
  align-items: center;
  min-height: 5.2rem;
  border-bottom: 1px solid var(--roady-border-default);
}

.status-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 0;
  margin: 2rem 0 0;
  border-top: 1px solid var(--roady-border-default);
}

.status-grid div {
  display: grid;
  grid-template-columns: 14rem minmax(0, 1fr);
  align-items: center;
  min-height: 6rem;
  border-bottom: 1px solid var(--roady-border-default);
}

dt {
  color: var(--roady-text-secondary);
  font-size: var(--krds-pc-font-size-body-small);
  font-weight: var(--krds-font-weight-bold);
}

dd {
  margin: 0;
  color: var(--roady-text-primary);
  font-size: var(--krds-pc-font-size-body-small);
}

.basic-info-list dd {
  overflow-wrap: anywhere;
}

.low-battery {
  color: var(--roady-status-danger);
  font-weight: var(--krds-font-weight-bold);
}

@media (max-width: 900px) {
  .overview-grid,
  .status-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .robot-detail {
    padding: 2rem;
  }

  .page-header {
    flex-direction: column;
  }

  .remote-control {
    align-items: flex-start;
  }

  .command-error,
  .command-feedback,
  .inspection-notice {
    text-align: left;
  }

  .command-feedback span {
    white-space: normal;
  }

  .basic-info-list div,
  .status-grid div {
    grid-template-columns: 11rem minmax(0, 1fr);
  }
}
</style>
