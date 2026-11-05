import { Platform } from 'react-native';

function resolveApiBase() {
  const configured = process.env.EXPO_PUBLIC_API_URL;
  if (configured !== undefined && configured !== null) {
    return String(configured).replace(/\/+$/, '');
  }
  if (Platform.OS === 'web' && typeof window !== 'undefined') {
    const { protocol, hostname, port } = window.location;
    // Expo Web en desarrollo: el backend vive en el mismo host, puerto 8000.
    if (port === '8081' || port === '19006') {
      return `${protocol}//${hostname}:8000`;
    }
    // Build de producción: mismo origen, con proxy inverso para /api y /health.
    return '';
  }
  return 'http://localhost:8000';
}

export const API_BASE = resolveApiBase();

export function apiUrl(path) {
  if (!path) return API_BASE;
  if (/^https?:\/\//i.test(path)) return path;
  return `${API_BASE}${path.startsWith('/') ? path : `/${path}`}`;
}

export class ApiError extends Error {
  constructor(message, { code = 'request_failed', status = 0, requestId = null } = {}) {
    super(message);
    this.name = 'ApiError';
    this.code = code;
    this.status = status;
    this.requestId = requestId;
  }
}

async function parseError(response) {
  let payload = null;
  try {
    payload = await response.json();
  } catch {
    payload = null;
  }
  const detail = payload?.error;
  return new ApiError(
    detail?.message || `El servidor respondió con un error (${response.status}).`,
    {
      code: detail?.code || 'http_error',
      status: response.status,
      requestId: detail?.request_id || response.headers.get('X-Request-ID'),
    },
  );
}

export async function fetchStatus({ signal } = {}) {
  let response;
  try {
    response = await fetch(apiUrl('/api/v1/status'), {
      signal,
      headers: { Accept: 'application/json' },
    });
  } catch (error) {
    if (error?.name === 'AbortError') throw error;
    throw new ApiError(
      'No se pudo conectar con el motor de traducción. Comprueba que el backend esté activo.',
      { code: 'network_error' },
    );
  }
  if (!response.ok) throw await parseError(response);
  return response.json();
}

export async function translateAudio(file, { signal } = {}) {
  const form = new FormData();
  if (Platform.OS === 'web') {
    let blob = file.file;
    if (!blob && file.uri) {
      try {
        blob = await fetch(file.uri).then((response) => response.blob());
      } catch {
        throw new ApiError('No se pudo leer el archivo seleccionado.', {
          code: 'file_read_error',
        });
      }
    }
    if (!blob) {
      throw new ApiError('No se pudo leer el archivo seleccionado.', {
        code: 'file_read_error',
      });
    }
    form.append('file', blob, file.name);
  } else {
    form.append('file', {
      uri: file.uri,
      name: file.name,
      type: file.mimeType || 'audio/wav',
    });
  }

  let response;
  try {
    response = await fetch(apiUrl('/api/v1/translate'), {
      method: 'POST',
      body: form,
      signal,
      headers: { Accept: 'application/json' },
    });
  } catch (error) {
    if (error?.name === 'AbortError') throw error;
    throw new ApiError(
      'Se perdió la conexión durante el procesamiento. Verifica el backend e inténtalo de nuevo.',
      { code: 'network_error' },
    );
  }
  if (!response.ok) throw await parseError(response);
  return response.json();
}
