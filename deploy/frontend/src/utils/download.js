import { Platform, Share } from 'react-native';

export async function downloadAudio(url, filename = 'hilo_traduccion.wav') {
  if (Platform.OS === 'web' && typeof document !== 'undefined') {
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    link.rel = 'noopener';
    document.body.appendChild(link);
    link.click();
    link.remove();
    return;
  }
  await Share.share({
    title: filename,
    message: url,
    url,
  });
}
