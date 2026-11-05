const path = require('node:path');
const { test, expect } = require('@playwright/test');

const SAMPLE = path.resolve(__dirname, 'fixtures/fleurs_es_419_test_0000.wav');

test.describe('E2E real con pipeline', () => {
  test.skip(!process.env.E2E_LIVE, 'Define E2E_LIVE=1 y arranca el backend real.');
  test.setTimeout(600_000);

  test('sube FLEURS, traduce y descarga el WAV generado', async ({ page }) => {
    await page.goto('/');
    await expect(page.getByRole('button', { name: /Motor (listo|disponible)\. Actualizar estado/ }).first()).toBeVisible({ timeout: 30_000 });

    const [chooser] = await Promise.all([
      page.waitForEvent('filechooser'),
      page.getByLabel('Seleccionar archivo de audio').click(),
    ]);
    await chooser.setFiles(SAMPLE);
    await expect(page.getByText('fleurs_es_419_test_0000.wav').first()).toBeVisible();

    await page.getByRole('button', { name: 'Traducir' }).click();
    await expect(page.getByText('Traducción completada')).toBeVisible({
      timeout: 300_000,
    });

    await expect(page.getByText(/Se recomienda enfáticamente a los viajeros/)).toBeVisible();
    await expect(page.getByText(/Travelers are strongly advised/)).toBeVisible();
    await expect(page.getByText('Similitud ECAPA', { exact: true })).toBeVisible();
    await expect(page.getByText('MarianMT base', { exact: true })).toBeVisible();

    const downloadPromise = page.waitForEvent('download');
    await page.getByRole('button', { name: 'Descargar audio traducido' }).click();
    const download = await downloadPromise;
    expect(download.suggestedFilename()).toMatch(/^hilo_[0-9a-f]{8}_en\.wav$/);
  });
});
