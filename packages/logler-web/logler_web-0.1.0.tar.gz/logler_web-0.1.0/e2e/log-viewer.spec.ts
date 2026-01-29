import { test, expect } from '@playwright/test'

test.describe('Log Viewer', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/')
  })

  test('shows empty state when no file is opened', async ({ page }) => {
    // When no file is opened, should show empty state
    await expect(page.locator('text=No file opened')).toBeVisible()
    await expect(page.locator('text=Click "Open File" to get started')).toBeVisible()
  })

  test('displays sidebar with statistics', async ({ page }) => {
    // Sidebar should show statistics
    await expect(page.locator('text=Total')).toBeVisible()
    await expect(page.locator('text=Errors')).toBeVisible()
    await expect(page.locator('text=Warnings')).toBeVisible()
  })

  test('has search input in sidebar', async ({ page }) => {
    // Look for search input with placeholder
    const searchInput = page.locator('input[placeholder="Search logs..."]')
    await expect(searchInput).toBeVisible()
  })

  test('has log levels section in sidebar', async ({ page }) => {
    // Look for log levels section
    await expect(page.locator('text=Log Levels')).toBeVisible()
  })

  test('can enter search query', async ({ page }) => {
    const searchInput = page.locator('input[placeholder="Search logs..."]')

    await searchInput.fill('error')

    await expect(searchInput).toHaveValue('error')
  })

  test('shows main content area', async ({ page }) => {
    await expect(page.locator('.main-content')).toBeVisible()
  })

  test('shows threads section in sidebar', async ({ page }) => {
    await expect(page.getByText('Threads (0)')).toBeVisible()
  })
})
