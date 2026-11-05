import { Platform } from 'react-native';

export const ALLOWED_EXTENSIONS = ['wav', 'mp3', 'm4a', 'ogg', 'flac', 'webm'];
export const DEFAULT_MAX_UPLOAD_MB = 20;
export const DEFAULT_MAX_AUDIO_SECONDS = 120;
export const MIN_AUDIO_SECONDS = 0.5;

export function fileExtension(name = '') {
  const parts = String(name).toLowerCase().split('.');
  return parts.length > 1 ? parts.pop() : '';
}

export function validateAudioFile(asset, limits = {}) {
  const maxMb = limits.maxUploadMb || DEFAULT_MAX_UPLOAD_MB;
  const maxSeconds = limits.maxAudioSeconds || DEFAULT_MAX_AUDIO_SECONDS;
  const extension = fileExtension(asset.name);

  if (!asset.name || !extension) {
    return { ok: false, message: 'El archivo no tiene un nombre o extensión válidos.' };
  }
  if (!ALLOWED_EXTENSIONS.includes(extension)) {
    return {
      ok: false,
      message: `Formato .${extension} no permitido. Usa WAV, MP3, M4A, OGG, FLAC o WEBM.`,
    };
  }
  if (asset.mimeType && !asset.mimeType.startsWith('audio/') && asset.mimeType !== 'video/webm') {
    return { ok: false, message: 'El archivo seleccionado no parece ser un audio.' };
  }
  if (!asset.size) {
    return { ok: false, message: 'El archivo está vacío o no se pudo leer.' };
  }
  if (asset.size > maxMb * 1024 * 1024) {
    return { ok: false, message: `El audio supera el límite de ${maxMb} MB.` };
  }
  if (asset.durationSec && asset.durationSec < MIN_AUDIO_SECONDS) {
    return { ok: false, message: 'El audio es demasiado corto (mínimo 0.5 s).' };
  }
  if (asset.durationSec && asset.durationSec > maxSeconds) {
    return {
      ok: false,
      message: `El audio supera la duración máxima de ${maxSeconds} segundos.`,
    };
  }
  return { ok: true, message: null };
}

export function getAudioDuration(uri) {
  if (Platform.OS !== 'web' || typeof window === 'undefined' || !uri) {
    return Promise.resolve(null);
  }
  return new Promise((resolve) => {
    const audio = new window.Audio();
    let settled = false;
    const finish = (value) => {
      if (settled) return;
      settled = true;
      audio.removeAttribute('src');
      audio.load();
      resolve(value);
    };
    audio.preload = 'metadata';
    audio.onloadedmetadata = () => {
      finish(Number.isFinite(audio.duration) ? audio.duration : null);
    };
    audio.onerror = () => finish(null);
    window.setTimeout(() => finish(null), 5000);
    audio.src = uri;
  });
}

export function formatDuration(seconds) {
  if (!Number.isFinite(seconds) || seconds < 0) return '0:00';
  const rounded = Math.round(seconds);
  const minutes = Math.floor(rounded / 60);
  const rest = rounded % 60;
  return `${minutes}:${String(rest).padStart(2, '0')}`;
}

export function formatSeconds(seconds) {
  if (!Number.isFinite(seconds)) return '—';
  return `${seconds.toFixed(seconds >= 10 ? 1 : 2)} s`;
}

export function formatBytes(bytes) {
  if (!Number.isFinite(bytes) || bytes <= 0) return '—';
  if (bytes < 1024 * 1024) return `${Math.max(1, Math.round(bytes / 1024))} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export function formatSimilarity(value) {
  return Number.isFinite(value) ? value.toFixed(3) : '—';
}

export function formatTime(isoString) {
  if (!isoString) return '';
  const date = new Date(isoString);
  if (Number.isNaN(date.getTime())) return '';
  return date.toLocaleTimeString('es', { hour: '2-digit', minute: '2-digit' });
}
