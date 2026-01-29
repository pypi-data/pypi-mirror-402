import { test, expect } from '@playwright/test'

test.describe('File Browser', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/')
  })

  test('opens file browser modal when clicking open button', async ({ page }) => {
    // Click the open file button in the header
    await page.click('button:has-text("Open")')

    // Verify modal is visible
    await expect(page.locator('.n-modal')).toBeVisible()
    await expect(page.locator('text=Open Log File')).toBeVisible()
  })

  test('has browse and search tabs', async ({ page }) => {
    await page.click('button:has-text("Open")')

    // Check for Browse tab
    await expect(page.locator('.n-tabs-tab:has-text("Browse")')).toBeVisible()

    // Check for Search tab
    await expect(page.locator('.n-tabs-tab:has-text("Search")')).toBeVisible()
  })

  test('shows current directory path', async ({ page }) => {
    await page.click('button:has-text("Open")')

    // Wait for browse to complete and show directory (any path starting with /)
    await expect(page.locator('text=/')).toBeVisible({ timeout: 5000 })
  })

  test('can switch to search tab', async ({ page }) => {
    await page.click('button:has-text("Open")')

    // Click search tab
    await page.click('.n-tabs-tab:has-text("Search")')

    // Verify glob input is visible
    await expect(page.locator('input[placeholder*="glob pattern"]')).toBeVisible()
  })

  test('shows preset glob patterns in search tab', async ({ page }) => {
    await page.click('button:has-text("Open")')
    await page.click('.n-tabs-tab:has-text("Search")')

    // Check for preset buttons using exact text matching
    await expect(page.getByRole('button', { name: '*.log', exact: true })).toBeVisible()
    await expect(page.getByRole('button', { name: '**/*.log' })).toBeVisible()
  })

  test('closes modal with cancel button', async ({ page }) => {
    await page.click('button:has-text("Open")')
    await expect(page.locator('.n-modal')).toBeVisible()

    await page.click('button:has-text("Cancel")')

    await expect(page.locator('.n-modal')).not.toBeVisible()
  })

  test('open selected button is disabled when no files selected', async ({ page }) => {
    await page.click('button:has-text("Open")')

    const openButton = page.locator('button:has-text("Open Selected")')
    await expect(openButton).toBeDisabled()
  })
})
