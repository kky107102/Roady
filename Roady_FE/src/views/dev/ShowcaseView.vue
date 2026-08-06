<script setup lang="ts">
import { ref } from 'vue'
import KrdsTextInput from '@/components/common/KrdsTextInput.vue'
import KrdsSelect from '@/components/common/KrdsSelect.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import ErrorState from '@/components/common/ErrorState.vue'
import { useNotificationStore } from '@/stores/notification'
import type { BadgeType } from '@/components/common/StatusBadge.vue'
import type { SelectOption } from '@/components/common/KrdsSelect.vue'

const notif = useNotificationStore()

// 입력 컴포넌트 상태
const textNormal = ref('')
const textError = ref('잘못된 입력')
const textDisabled = ref('비활성화 값')
const selectNormal = ref('')
const selectError = ref('')
const selectDisabled = ref('option2')

const regionOptions: SelectOption[] = [
  { value: 'seoul', label: '서울특별시' },
  { value: 'busan', label: '부산광역시' },
  { value: 'daegu', label: '대구광역시' },
  { value: 'incheon', label: '인천광역시' },
  { value: 'gwangju', label: '광주광역시' },
]

// 상태 배지
const badges: { type: BadgeType; label: string }[] = [
  { type: 'danger', label: '위험' },
  { type: 'warning', label: '주의' },
  { type: 'info', label: '정보' },
  { type: 'success', label: '정상' },
  { type: 'neutral', label: '비활성' },
  { type: 'new', label: '신규' },
]

// 배지 크기
const badgeSizes = ['small', 'medium', 'large'] as const
</script>

<template>
  <div class="showcase-page">
    <div class="showcase-banner">
      <span class="dev-tag">DEV ONLY</span>
      <span>이 페이지는 개발 환경에서만 표시됩니다. 프로덕션 빌드에 포함되지 않습니다.</span>
    </div>

    <!-- ─────────────── 1. 입력 컴포넌트 ─────────────── -->
    <section class="showcase-section">
      <h2 class="section-title">입력 컴포넌트</h2>

      <div class="card-grid cols-3">
        <div class="card">
          <p class="card-label">텍스트 입력 — 기본</p>
          <KrdsTextInput
            id="demo-text-normal"
            name="demo-text-normal"
            label="지역명"
            placeholder="지역명을 입력하세요"
            v-model="textNormal"
            hint="도·시·군·구 단위로 입력"
          />
        </div>

        <div class="card">
          <p class="card-label">텍스트 입력 — 오류</p>
          <KrdsTextInput
            id="demo-text-error"
            name="demo-text-error"
            label="지역명"
            placeholder="지역명을 입력하세요"
            v-model="textError"
            error="올바른 지역명을 입력해주세요."
            required
          />
        </div>

        <div class="card">
          <p class="card-label">텍스트 입력 — 비활성</p>
          <KrdsTextInput
            id="demo-text-disabled"
            name="demo-text-disabled"
            label="지역명"
            v-model="textDisabled"
            disabled
          />
        </div>

        <div class="card">
          <p class="card-label">셀렉트 — 기본</p>
          <KrdsSelect
            id="demo-select-normal"
            name="demo-select-normal"
            label="지역 선택"
            placeholder="지역을 선택하세요"
            v-model="selectNormal"
            :options="regionOptions"
            hint="탐지 데이터 조회 지역"
          />
        </div>

        <div class="card">
          <p class="card-label">셀렉트 — 오류</p>
          <KrdsSelect
            id="demo-select-error"
            name="demo-select-error"
            label="지역 선택"
            placeholder="지역을 선택하세요"
            v-model="selectError"
            :options="regionOptions"
            error="지역을 선택해주세요."
            required
          />
        </div>

        <div class="card">
          <p class="card-label">셀렉트 — 비활성</p>
          <KrdsSelect
            id="demo-select-disabled"
            name="demo-select-disabled"
            label="지역 선택"
            v-model="selectDisabled"
            :options="regionOptions"
            disabled
          />
        </div>
      </div>
    </section>

    <!-- ─────────────── 2. 상태 배지 ─────────────── -->
    <section class="showcase-section">
      <h2 class="section-title">상태 배지</h2>

      <div class="card">
        <p class="card-label">타입별 (small)</p>
        <div class="badge-row">
          <StatusBadge
            v-for="b in badges"
            :key="b.type"
            :type="b.type"
            :label="b.label"
            size="small"
          />
        </div>
      </div>

      <div class="card-grid card-grid--spaced cols-3">
        <div class="card" v-for="size in badgeSizes" :key="size">
          <p class="card-label">크기 — {{ size }}</p>
          <div class="badge-row">
            <StatusBadge
              v-for="b in badges"
              :key="b.type"
              :type="b.type"
              :label="b.label"
              :size="size"
            />
          </div>
        </div>
      </div>
    </section>

    <!-- ─────────────── 3. 상태 화면 ─────────────── -->
    <section class="showcase-section">
      <h2 class="section-title">상태 화면</h2>

      <div class="card-grid cols-3">
        <div class="card state-card">
          <p class="card-label">로딩 화면</p>
          <div class="state-preview">
            <LoadingSpinner label="데이터 불러오는 중" />
          </div>
        </div>

        <div class="card state-card">
          <p class="card-label">빈 화면</p>
          <div class="state-preview">
            <EmptyState
              title="탐지 이력이 없습니다."
              description="선택한 기간에 탐지된 노면 손상이 없습니다."
            />
          </div>
        </div>

        <div class="card state-card">
          <p class="card-label">오류 화면</p>
          <div class="state-preview">
            <ErrorState
              message="데이터를 불러오는 중 문제가 발생했습니다."
              @retry="notif.info('재시도 버튼이 눌렸습니다.')"
            />
          </div>
        </div>
      </div>
    </section>

    <!-- ─────────────── 4. 전역 알림 ─────────────── -->
    <section class="showcase-section">
      <h2 class="section-title">전역 알림 (Toast)</h2>

      <div class="card">
        <p class="card-label">타입별 토스트 트리거</p>
        <div class="button-row">
          <button
            type="button"
            class="krds-btn medium filled success"
            @click="notif.success('데이터를 성공적으로 저장했습니다.')"
          >
            Success
          </button>
          <button
            type="button"
            class="krds-btn medium filled danger"
            @click="notif.error('서버 연결에 실패했습니다.')"
          >
            Error
          </button>
          <button
            type="button"
            class="krds-btn medium filled warning"
            @click="notif.warning('세션이 30분 후 만료됩니다.')"
          >
            Warning
          </button>
          <button
            type="button"
            class="krds-btn medium filled primary"
            @click="notif.info('새로운 탐지 이벤트가 발생했습니다.')"
          >
            Info
          </button>
          <button
            type="button"
            class="krds-btn medium secondary"
            @click="
              notif.success('저장 완료');
              notif.error('처리 실패');
              notif.warning('주의 필요');
              notif.info('새 이벤트');
            "
          >
            전체 동시 표시
          </button>
        </div>
      </div>
    </section>
  </div>
</template>

<style scoped>
.showcase-page {
  padding: 2.4rem 3.2rem;
  display: flex;
  flex-direction: column;
  gap: 3.2rem;
}

.showcase-banner {
  display: flex;
  align-items: center;
  gap: 1.2rem;
  padding: 1.2rem 1.6rem;
  border-radius: 0.6rem;
  border: 1px dashed var(--roady-status-warning);
  color: var(--roady-text-secondary);
  background: color-mix(in srgb, var(--roady-status-warning) 8%, transparent);
  font-size: var(--krds-pc-font-size-body-small);
}

.dev-tag {
  flex-shrink: 0;
  padding: 0.2rem 0.8rem;
  border-radius: 0.4rem;
  color: #fff;
  background: var(--roady-status-warning);
  font-size: 1.1rem;
  font-weight: var(--krds-font-weight-bold);
  letter-spacing: 0.05em;
}

.showcase-section {
  display: flex;
  flex-direction: column;
  gap: 1.6rem;
}

.section-title {
  margin: 0;
  padding-bottom: 1.2rem;
  border-bottom: 1px solid var(--roady-border-default);
  color: var(--roady-text-primary);
  font-size: var(--krds-pc-font-size-body-medium);
  font-weight: var(--krds-font-weight-bold);
}

.card-grid {
  display: grid;
  gap: 1.6rem;
}

.card-grid--spaced {
  margin-top: 1.6rem;
}

.card-grid.cols-3 {
  grid-template-columns: repeat(3, 1fr);
}

.card {
  padding: 2rem;
  border: 1px solid var(--roady-border-default);
  border-radius: 0.8rem;
  background: var(--roady-surface-default);
}

.card-label {
  margin: 0 0 1.6rem;
  color: var(--roady-text-tertiary);
  font-size: var(--krds-pc-font-size-body-small);
  font-weight: var(--krds-font-weight-bold);
}

.state-card {
  padding: 0;
  overflow: hidden;
}

.state-card .card-label {
  padding: 1.2rem 1.6rem 0;
  margin-bottom: 0;
}

.state-preview {
  border-top: 1px solid var(--roady-border-default);
  margin-top: 1.2rem;
  background: var(--roady-surface-background);
}

.badge-row {
  display: flex;
  flex-wrap: wrap;
  gap: 0.8rem;
  align-items: center;
}

.button-row {
  display: flex;
  flex-wrap: wrap;
  gap: 1.2rem;
  align-items: center;
}
</style>
