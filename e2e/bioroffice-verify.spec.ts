/**
 * E2E test: BiorOffice post-install verification — skills discovery + live
 * agent usage. Assumes bioroffice is already installed (bioroffice-install
 * spec tests 1-7).
 *
 * Launches the dev app with ENABLE_PLAYWRIGHT=true and connects over CDP.
 */

import { test, expect, chromium } from '@playwright/test';
import { join } from 'path';
import { spawn } from 'child_process';
import * as fs from 'fs';
import * as os from 'os';
import type { Page, Browser } from '@playwright/test';

const CDP_PORT = 9225;
const EXT_DIR = join(os.homedir(), '.config', 'biorouter', 'extensions', 'bioroffice');
const AGENT_OUT_DIR = '/tmp/bioroffice-e2e';
const AGENT_PPTX = join(AGENT_OUT_DIR, 'demo.pptx');

let browser: Browser;
let mainWindow: Page;
let forgeProcess: ReturnType<typeof spawn>;

test.describe('BiorOffice — skills discovery + live agent usage', () => {
  test.setTimeout(420_000);

  test.beforeAll(async () => {
    if (!fs.existsSync(join(EXT_DIR, 'manifest.json'))) {
      throw new Error('bioroffice extension not installed — run bioroffice-install spec first');
    }
    fs.rmSync(AGENT_OUT_DIR, { recursive: true, force: true });
    fs.mkdirSync(AGENT_OUT_DIR, { recursive: true });

    forgeProcess = spawn('npm', ['run', 'start-gui'], {
      cwd: join(__dirname, '../..'),
      stdio: 'pipe',
      shell: true,
      env: {
        ...process.env,
        ELECTRON_IS_DEV: '1',
        NODE_ENV: 'development',
        BIOROUTER_ALLOWLIST_BYPASS: 'true',
        ENABLE_PLAYWRIGHT: 'true',
        PLAYWRIGHT_CDP_PORT: String(CDP_PORT),
      },
    });
    forgeProcess.stdout?.on('data', (d) => process.stdout.write('[forge] ' + d));
    forgeProcess.stderr?.on('data', (d) => process.stderr.write('[forge] ' + d));

    const deadline = Date.now() + 120_000;
    while (Date.now() < deadline) {
      try {
        const b = await chromium.connectOverCDP(`http://127.0.0.1:${CDP_PORT}`);
        await b.close();
        break;
      } catch {
        await new Promise((r) => setTimeout(r, 2000));
      }
    }
    browser = await chromium.connectOverCDP(`http://127.0.0.1:${CDP_PORT}`);
    const pages = browser.contexts().flatMap((ctx) => ctx.pages());
    mainWindow =
      pages.find((p) => p.url().includes('localhost') || p.url().startsWith('file://')) ?? pages[0];
    await mainWindow.waitForLoadState('domcontentloaded');
    await mainWindow.waitForFunction(() => {
      const root = document.getElementById('root');
      return root && root.children.length > 0;
    });
    await mainWindow.waitForTimeout(3000);
  });

  test.afterAll(async () => {
    if (browser) await browser.close().catch(() => {});
    try {
      forgeProcess?.kill();
    } catch {
      /* ignore */
    }
  });

  async function goHome(): Promise<void> {
    const home = mainWindow
      .locator('[data-testid="sidebar-home-button"], nav >> text=Home, text=Home')
      .first();
    if (await home.isVisible({ timeout: 3000 }).catch(() => false)) {
      await home.click();
      await mainWindow.waitForTimeout(1500);
    }
  }

  test('1. Bundled skills appear in the chat skills dropdown', async () => {
    await goHome();
    await mainWindow.screenshot({ path: 'test-results/bioroffice-v1-home.png' });

    const skillsBtn = mainWindow.locator('button[title="manage skills"]');
    await expect(skillsBtn).toBeVisible({ timeout: 15000 });
    await skillsBtn.click();
    const searchInput = mainWindow.locator('input[placeholder="search skills..."]');
    await expect(searchInput).toBeVisible({ timeout: 5000 });
    await searchInput.fill('bioroffice');
    await mainWindow.waitForTimeout(800);
    await mainWindow.screenshot({ path: 'test-results/bioroffice-v2-skills-dropdown.png' });

    for (const slug of [
      'bioroffice-office-suite',
      'bioroffice-word',
      'bioroffice-excel',
      'bioroffice-powerpoint',
    ]) {
      await expect(mainWindow.locator(`text=${slug}`).first()).toBeVisible({ timeout: 5000 });
    }
    await mainWindow.keyboard.press('Escape');
    console.log('✓ all 4 bundled skills discovered in chat skills dropdown');
  });

  test('2. Agent creates a PowerPoint via the officecli tool in a real chat', async () => {
    await goHome();
    const input = mainWindow.locator('[data-testid="chat-input"]');
    await expect(input).toBeVisible({ timeout: 20000 });
    await input.click();
    await input.fill(
      `Use the officecli tool from the bioroffice extension to create ${AGENT_PPTX} ` +
        `and add one slide with title "BiorOffice E2E". Do not ask questions, just do it, ` +
        `then verify with a view outline call and report the outline.`
    );
    await input.press('Enter');
    await mainWindow.waitForTimeout(1000);
    await mainWindow.screenshot({ path: 'test-results/bioroffice-v3-message-sent.png' });

    const deadline = Date.now() + 300_000;
    let created = false;
    while (Date.now() < deadline) {
      if (fs.existsSync(AGENT_PPTX) && fs.statSync(AGENT_PPTX).size > 1000) {
        created = true;
        break;
      }
      for (const label of ['Always Allow', 'Allow Once', 'Allow']) {
        const allowBtn = mainWindow.locator(`button:has-text("${label}")`).first();
        if (await allowBtn.isVisible({ timeout: 200 }).catch(() => false)) {
          await allowBtn.click().catch(() => {});
          console.log(`clicked "${label}" tool confirmation`);
        }
      }
      await mainWindow.waitForTimeout(2000);
    }
    await mainWindow.screenshot({ path: 'test-results/bioroffice-v4-agent-result.png' });
    expect(created, `agent did not create ${AGENT_PPTX} within timeout`).toBe(true);
    console.log('✓ Agent created', AGENT_PPTX, fs.statSync(AGENT_PPTX).size, 'bytes');

    // Give the agent a moment to finish its verification reply, then capture it
    await mainWindow.waitForTimeout(15000);
    await mainWindow.screenshot({ path: 'test-results/bioroffice-v5-final.png' });
  });
});
