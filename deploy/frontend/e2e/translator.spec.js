const path = require('node:path');
const { test, expect } = require('@playwright/test');

const SAMPLE = path.resolve(__dirname, 'fixtures/fleurs_es_419_test_0000.wav');
const INVALID = path.resolve(__dirname, 'fixtures/nota.txt');
const RESULT_ID = 'a'.repeat(32);

const STATUS = {
  status: 'ok',
  service: 'hilo-translation-api',
  version: '1.0.0',
  timestamp: '2026-11-05T03:00:00Z',
  pipeline: {
    ready: true,
    busy: false,
    warm: true,
    mode: 'sequential',
    device: 'cuda',
    gpu: { available: true, name: 'GPU de prueba', total_memory_gb: 8 },
    xtts_license_accepted: true,
    requests_total: 1,
    completed_total: 1,
    last_error_code: null,
    last_completed_at: '2026-11-05T03:00:00Z',
    models: {
      asr: 'openai/whisper-small',
      translation: 'Helsinki-NLP/opus-mt-es-en',
      translation_checkpoint: 'base',
      tts: 'coqui/XTTS-v2',
      speaker_encoder: 'speechbrain/spkrec-ecapa-voxceleb',
    },
  },
  limits: {
    max_upload_mb: 20,
    max_audio_seconds: 120,
    result_ttl_seconds: 3600,
  },
  capabilities: {
    translation_direction: 'es-en',
    speaker_similarity: true,
    background_jobs: false,
  },
};

const RESULT = {
  id: RESULT_ID,
  status: 'completed',
  transcription_es: 'Se recomienda a los viajeros informarse sobre el clima extremo.',
  translation_en: 'Travelers are advised to inform themselves about extreme weather.',
  speaker_similarity: 0.512,
  audio: {
    url: `/api/v1/results/${RESULT_ID}/audio`,
    download_url: `/api/v1/results/${RESULT_ID}/audio?download=1`,
    mime_type: 'audio/wav',
    sample_rate: 24000,
    duration_sec: 7.8,
    filename: 'hilo_test_en.wav',
  },
  input: { duration_sec: 12.84 },
  timings: {
    preprocessing_sec: 0.02,
    asr_sec: 1.2,
    translation_sec: 0.4,
    xtts_sec: 2.1,
    speaker_evaluation_sec: 0.3,
    total_sec: 4.02,
    api_sec: 4.3,
  },
  models: {
    asr: 'openai/whisper-small',
    translation: 'Helsinki-NLP/opus-mt-es-en',
    translation_checkpoint: 'base',
    tts: 'coqui/XTTS-v2',
    speaker_encoder: 'speechbrain/spkrec-ecapa-voxceleb',
  },
  created_at: '2026-11-05T03:01:00Z',
  expires_at: '2026-11-05T04:01:00Z',
};

async function mockApi(page, { translateStatus = 200, translateDelay = 0 } = {}) {
  await page.route('**/api/v1/status', (route) =>
    route.fulfill({ status: 200, json: STATUS }),
  );
  await page.route('**/api/v1/translate', async (route) => {
    if (translateDelay) await new Promise((resolve) => setTimeout(resolve, translateDelay));
    if (translateStatus !== 200) {
      return route.fulfill({
        status: translateStatus,
        json: {
          error: {
            code: 'pipeline_error',
            message: 'El procesamiento falló en el servidor de prueba.',
            request_id: 'req-test-123',
          },
        },
      });
    }
    return route.fulfill({ status: 200, json: RESULT });
  });
  await page.route(/\/api\/v1\/results\/.+\/audio.*/, (route) => {
    const isDownload = route.request().url().includes('download=1');
    return route.fulfill({
      status: 200,
      path: SAMPLE,
      contentType: 'audio/wav',
      headers: {
        'Content-Disposition': `${isDownload ? 'attachment' : 'inline'}; filename="hilo_test_en.wav"`,
      },
    });
  });
}

async function pickFile(page, file = SAMPLE) {
  const [chooser] = await Promise.all([
    page.waitForEvent('filechooser'),
    page.getByLabel('Seleccionar archivo de audio').click(),
  ]);
  await chooser.setFiles(file);
}

test('muestra la pantalla principal y el estado real del motor', async ({ page }) => {
  await mockApi(page);
  await page.goto('/');
  await expect(page.getByText('Traduce un audio en español al inglés.')).toBeVisible();
  await expect(page.getByText('Carga un audio en español', { exact: true })).toBeVisible();
  await expect(page.getByRole('button', { name: 'Disponible. Actualizar estado' })).toBeVisible();
  await expect(page.getByRole('button', { name: 'Seleccionar archivo de audio' })).toBeVisible();
});

test('selecciona un audio, lo muestra y habilita la traducción', async ({ page }) => {
  await mockApi(page);
  await page.goto('/');
  await pickFile(page);
  await expect(page.getByText('fleurs_es_419_test_0000.wav').first()).toBeVisible();
  await expect(page.getByRole('button', { name: 'Traducir' })).toBeEnabled();
  await expect(page.getByRole('button', { name: 'Quitar audio seleccionado' })).toBeVisible();
});

test('acepta un archivo soltado en la zona de carga', async ({ page }) => {
  await mockApi(page);
  await page.goto('/');
  const dataTransfer = await page.evaluateHandle(() => {
    const transfer = new DataTransfer();
    transfer.items.add(new File(['audio de prueba'], 'audio_arrastrado.wav', { type: 'audio/wav' }));
    return transfer;
  });
  const dropZone = page.getByLabel('Zona para soltar un archivo de audio');
  await dropZone.dispatchEvent('dragenter', { dataTransfer });
  await expect(page.getByText('Suelta el audio aquí')).toBeVisible();
  await dropZone.dispatchEvent('drop', { dataTransfer });
  await expect(page.getByText('audio_arrastrado.wav').first()).toBeVisible();
});

test('muestra el procesamiento y luego los resultados reales del contrato', async ({ page }) => {
  await mockApi(page, { translateDelay: 1200 });
  await page.goto('/');
  await pickFile(page);
  await page.getByRole('button', { name: 'Traducir' }).click();
  await expect(page.getByText('Procesando tu audio…')).toBeVisible();
  await expect(page.getByText('Traducción completada')).toBeVisible();
  await expect(page.getByText(/Se recomienda a los viajeros/)).toBeVisible();
  await expect(page.getByText(/Travelers are advised/)).toBeVisible();
  await expect(page.getByText('Similitud ECAPA', { exact: true })).toBeVisible();
  await expect(page.getByText('Tiempos del pipeline')).toBeVisible();
  await expect(page.getByRole('button', { name: 'Traducir otro audio' })).toBeVisible();

  await page.getByRole('button', { name: 'Reproducir audio traducido' }).click();
  await expect(
    page.getByRole('button', { name: 'Pausar audio traducido' }),
  ).toBeVisible();
});

test('evita envíos duplicados mientras procesa el mismo audio', async ({ page }) => {
  let translations = 0;
  await mockApi(page, { translateDelay: 500 });
  page.on('request', (request) => {
    if (request.url().includes('/api/v1/translate')) translations += 1;
  });
  await page.goto('/');
  await pickFile(page);
  await page.getByRole('button', { name: 'Traducir' }).evaluate((button) => {
    button.click();
    button.click();
  });
  await expect(page.getByText('Traducción completada')).toBeVisible();
  expect(translations).toBe(1);
});

test('permite descargar el audio generado', async ({ page }) => {
  await mockApi(page);
  await page.goto('/');
  await pickFile(page);
  await page.getByRole('button', { name: 'Traducir' }).click();
  await expect(page.getByText('Traducción completada')).toBeVisible();
  const downloadPromise = page.waitForEvent('download');
  await page.getByRole('button', { name: 'Descargar audio traducido' }).click();
  const download = await downloadPromise;
  expect(download.suggestedFilename()).toBe('hilo_test_en.wav');
});

test('valida la extensión antes de enviar', async ({ page }) => {
  await mockApi(page);
  await page.goto('/');
  await pickFile(page, INVALID);
  await expect(page.getByText(/Formato .txt no permitido/)).toBeVisible();
  await expect(page.getByRole('button', { name: 'Traducir' })).toHaveCount(0);
});

test('muestra un error comprensible y permite reintentar', async ({ page }) => {
  await mockApi(page, { translateStatus: 500 });
  await page.goto('/');
  await pickFile(page);
  await page.getByRole('button', { name: 'Traducir' }).click();
  await expect(page.getByText('No pudimos completar la traducción')).toBeVisible();
  await expect(page.getByText('El procesamiento falló en el servidor de prueba.')).toBeVisible();
  await expect(page.getByRole('button', { name: 'Reintentar' })).toBeVisible();
});

test('maneja una conexión perdida durante el procesamiento', async ({ page }) => {
  await mockApi(page);
  await page.unroute('**/api/v1/translate');
  await page.route('**/api/v1/translate', (route) => route.abort('failed'));
  await page.goto('/');
  await pickFile(page);
  await page.getByRole('button', { name: 'Traducir' }).click();
  await expect(
    page.getByText('Se perdió la conexión durante el procesamiento.'),
  ).toBeVisible();
  await expect(page.getByRole('button', { name: 'Reintentar' })).toBeVisible();
});

test('adaptación móvil sin sidebar', async ({ page }) => {
  await mockApi(page);
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto('/');
  await expect(page.getByText('Cómo funciona')).toHaveCount(0);
  await expect(page.getByText('Carga un audio en español', { exact: true })).toBeVisible();
  await expect(page.getByLabel('Zona para soltar un archivo de audio')).toBeVisible();
});

test('muestra estados de motor degradado y no disponible de forma explícita', async ({ page }) => {
  await page.route('**/api/v1/status', (route) =>
    route.fulfill({ status: 200, json: { ...STATUS, status: 'degraded', pipeline: { ...STATUS.pipeline, ready: false } } }),
  );
  await page.goto('/');
  await expect(page.getByRole('button', { name: 'Degradado. Actualizar estado' })).toBeVisible();
  await expect(page.getByText('Motor degradado')).toBeVisible();

  await page.unroute('**/api/v1/status');
  await page.route('**/api/v1/status', (route) => route.abort('failed'));
  await page.getByRole('button', { name: 'Degradado. Actualizar estado' }).click();
  await expect(page.getByRole('button', { name: 'No disponible. Actualizar estado' })).toBeVisible();
  await expect(page.getByText('Motor no disponible')).toBeVisible();
});
