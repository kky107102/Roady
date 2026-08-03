import type { UserRole } from '@/types/auth'

export interface NavItem {
  key: string
  label: string
  routeName: string
  roles?: UserRole[]
}

export interface NavGroup {
  label: string
  items: NavItem[]
}

export const navGroups: NavGroup[] = [
  {
    label: '주요 메뉴',
    items: [
      { key: 'dashboard', label: '대시보드', routeName: 'dashboard' },
      { key: 'damages', label: '탐지 검토', routeName: 'damages' },
      { key: 'repairs', label: '보수 관리', routeName: 'repairs' },
      { key: 'robots', label: '로디 운행', routeName: 'robots' },
    ],
  },
  {
    label: '시스템 설정',
    items: [
      {
        key: 'admin',
        label: '설정 관리',
        routeName: 'admin-users',
        roles: ['ADMIN'],
      },
    ],
  },
]

export const roleLabels: Record<UserRole, string> = {
  ADMIN: '관리자',
  INSPECTOR: '점검 담당자',
  REPAIRER: '보수 담당자',
  VIEWER: '조회 사용자',
}
