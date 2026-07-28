import { test, expect } from '@playwright/test'

test('redirects an unauthenticated user to the login page', async ({ page }) => {
  await page.goto('/')

  await expect(page).toHaveURL(/\/login/)
  await expect(page.getByRole('heading', { name: '로그인' })).toBeVisible()
})
