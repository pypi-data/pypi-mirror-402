import { test, expect } from '@playwright/test'

test.describe('Waterfall View', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/')
  })

  test('shows empty state when no file is opened', async ({ page }) => {
    // When no file is opened, tabs are not shown
    await expect(page.locator('text=No file opened')).toBeVisible()
  })

  test('main content area is visible', async ({ page }) => {
    await expect(page.locator('.main-content')).toBeVisible()
  })

  test('empty state suggests opening a file', async ({ page }) => {
    await expect(page.locator('text=Click "Open File" to get started')).toBeVisible()
  })
})
