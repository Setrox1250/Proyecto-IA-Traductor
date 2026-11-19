import { useEffect, useRef, useState } from 'react';
import {
  ActivityIndicator,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  useWindowDimensions,
  View,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import * as DocumentPicker from 'expo-document-picker';

import { translateAudio } from '../api/client';
import BrandMark from '../components/BrandMark';
import EngineStatusPill from '../components/EngineStatusPill';
import ErrorBubble from '../components/ErrorBubble';
import FileDropCard from '../components/FileDropCard';
import ProcessingBubble from '../components/ProcessingBubble';
import ResultCard from '../components/ResultCard';
import SelectedAudioBubble from '../components/SelectedAudioBubble';
import useEngineStatus from '../hooks/useEngineStatus';
import { colors, fonts, shadows } from '../theme';
import {
  DEFAULT_MAX_AUDIO_SECONDS,
  DEFAULT_MAX_UPLOAD_MB,
  formatDuration,
  getAudioDuration,
  validateAudioFile,
} from '../utils/audio';

const AUDIO_TYPES = [
  'audio/wav',
  'audio/mpeg',
  'audio/mp4',
  'audio/ogg',
  'audio/flac',
  'audio/webm',
  'audio/*',
];

function StatusNotice({ status, statusError }) {
  if (statusError) {
    return (
      <View style={[styles.notice, styles.noticeError]} accessibilityRole="alert">
        <Ionicons name="cloud-offline-outline" size={18} color={colors.danger} />
        <View style={styles.noticeCopy}>
          <Text style={styles.noticeTitle}>Motor no disponible</Text>
          <Text style={styles.noticeText}>
            No se pudo consultar el servicio. Puedes elegir un archivo, pero no lo envíes
            hasta que el estado vuelva a estar disponible.
          </Text>
        </View>
      </View>
    );
  }

  if (status?.status === 'degraded') {
    return (
      <View style={[styles.notice, styles.noticeWarning]} accessibilityRole="alert">
        <Ionicons name="warning-outline" size={18} color="#A4682C" />
        <View style={styles.noticeCopy}>
          <Text style={styles.noticeTitle}>Motor degradado</Text>
          <Text style={styles.noticeText}>
            XTTS-v2 no está habilitado. El operador debe aceptar la licencia CPML antes de
            poder generar el WAV en inglés.
          </Text>
        </View>
      </View>
    );
  }

  if (status?.pipeline?.busy) {
    return (
      <View style={[styles.notice, styles.noticeBusy]}>
        <ActivityIndicator size="small" color={colors.primary} />
        <View style={styles.noticeCopy}>
          <Text style={styles.noticeTitle}>El motor está procesando</Text>
          <Text style={styles.noticeText}>
            La GPU procesa una solicitud a la vez. Espera a que termine antes de enviar un
            nuevo audio.
          </Text>
        </View>
      </View>
    );
  }

  return null;
}

export default function TranslatorScreen() {
  const insets = useSafeAreaInsets();
  const { width } = useWindowDimensions();
  const isWide = width >= 760;
  const scrollRef = useRef(null);
  const durationRequest = useRef(0);
  const activeRequest = useRef(false);
  const objectUrl = useRef(null);

  const {
    status,
    error: statusError,
    loading: statusLoading,
    refresh: refreshStatus,
  } = useEngineStatus();
  const [selectedFile, setSelectedFile] = useState(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [isValidating, setIsValidating] = useState(false);
  const [picking, setPicking] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [elapsed, setElapsed] = useState(0);

  const limits = {
    maxUploadMb: status?.limits?.max_upload_mb ?? DEFAULT_MAX_UPLOAD_MB,
    maxAudioSeconds: status?.limits?.max_audio_seconds ?? DEFAULT_MAX_AUDIO_SECONDS,
  };

  const releaseObjectUrl = () => {
    if (objectUrl.current && typeof URL !== 'undefined') {
      URL.revokeObjectURL(objectUrl.current);
      objectUrl.current = null;
    }
  };

  useEffect(() => () => releaseObjectUrl(), []);

  useEffect(() => {
    if (!isProcessing) return undefined;
    const started = Date.now();
    const timer = setInterval(() => setElapsed((Date.now() - started) / 1000), 1000);
    return () => clearInterval(timer);
  }, [isProcessing]);

  useEffect(() => {
    if (!result && !isProcessing && !error) return undefined;
    const timer = setTimeout(() => scrollRef.current?.scrollToEnd({ animated: true }), 120);
    return () => clearTimeout(timer);
  }, [result, isProcessing, error]);

  const applyPickedAsset = async (asset, { fromDrop = false } = {}) => {
    if (!asset || isProcessing || isValidating) return;
    const candidate = {
      uri: asset.uri,
      name: asset.name,
      size: asset.size,
      mimeType: asset.mimeType || asset.type,
      file: asset.file,
      durationSec: null,
    };
    const validation = validateAudioFile(candidate, limits);
    if (!validation.ok) {
      if (fromDrop) releaseObjectUrl();
      setError({ message: validation.message, code: 'client_validation' });
      return;
    }

    durationRequest.current += 1;
    const requestId = durationRequest.current;
    setIsValidating(true);
    setSelectedFile(null);
    setResult(null);
    setError(null);
    setElapsed(0);

    const duration = await getAudioDuration(candidate.uri);
    if (durationRequest.current !== requestId) return;

    const updated = { ...candidate, durationSec: duration };
    const durationValidation = validateAudioFile(updated, limits);
    if (!durationValidation.ok) {
      if (fromDrop) releaseObjectUrl();
      setError({ message: durationValidation.message, code: 'client_validation' });
      setIsValidating(false);
      return;
    }

    setSelectedFile(updated);
    setIsValidating(false);
  };

  const handlePick = async () => {
    if (isProcessing || isValidating || picking) return;
    setPicking(true);
    try {
      const selection = await DocumentPicker.getDocumentAsync({
        type: AUDIO_TYPES,
        multiple: false,
        copyToCacheDirectory: true,
        base64: false,
      });
      if (!selection.canceled && selection.assets?.[0]) {
        releaseObjectUrl();
        await applyPickedAsset(selection.assets[0]);
      }
    } catch {
      setError({
        message: 'No se pudo abrir el selector de archivos. Inténtalo de nuevo.',
        code: 'picker_error',
      });
    } finally {
      setPicking(false);
    }
  };

  const handleDrop = async (file) => {
    if (!file || isProcessing || isValidating) return;
    releaseObjectUrl();
    const uri = URL.createObjectURL(file);
    objectUrl.current = uri;
    await applyPickedAsset(
      {
        uri,
        name: file.name,
        size: file.size,
        mimeType: file.type,
        file,
      },
      { fromDrop: true },
    );
  };

  const handleProcess = async () => {
    if (!selectedFile || isProcessing || isValidating || activeRequest.current) return;
    activeRequest.current = true;
    setIsProcessing(true);
    setResult(null);
    setError(null);
    setElapsed(0);
    try {
      const payload = await translateAudio(selectedFile);
      setResult(payload);
      refreshStatus();
    } catch (requestError) {
      setError({
        message: requestError?.message || 'No se pudo procesar el audio. Inténtalo nuevamente.',
        code: requestError?.code || 'request_failed',
        requestId: requestError?.requestId,
      });
    } finally {
      activeRequest.current = false;
      setIsProcessing(false);
    }
  };

  const handleReset = () => {
    if (isProcessing) return;
    durationRequest.current += 1;
    releaseObjectUrl();
    setSelectedFile(null);
    setResult(null);
    setError(null);
    setElapsed(0);
    setIsValidating(false);
  };

  const processingBlocked = isProcessing || isValidating || picking;
  const engineAccepting = Boolean(status?.pipeline?.ready) && !status?.pipeline?.busy;
  const canTranslate = Boolean(selectedFile) && !processingBlocked && engineAccepting;

  return (
    <View style={styles.root}>
      <ScrollView
        ref={scrollRef}
        contentContainerStyle={[
          styles.scrollContent,
          { paddingTop: Math.max(insets.top, 20), paddingBottom: Math.max(insets.bottom, 24) },
        ]}
        showsVerticalScrollIndicator={false}
      >
        <View style={styles.shell}>
          <View style={styles.header}>
            <View style={styles.brandRow}>
              <BrandMark size={44} />
              <View style={styles.brandCopy}>
                <Text style={styles.brand}>Hilo Audio</Text>
                <Text style={styles.brandSub}>TRADUCCIÓN DE AUDIO · ES → EN</Text>
              </View>
            </View>
            <EngineStatusPill
              status={status}
              error={statusError}
              loading={statusLoading}
              onRefresh={refreshStatus}
            />
          </View>

          <View style={[styles.hero, isWide && styles.heroWide]}>
            <View style={styles.heroCopy}>
              <Text style={styles.eyebrow}>UNA TAREA, UN RESULTADO</Text>
              <Text style={styles.title}>Traduce un audio en español al inglés.</Text>
              <Text style={styles.lead}>
                Sube una grabación. El sistema transcribe, traduce y genera un WAV en inglés
                condicionado por el audio de referencia.
              </Text>
            </View>
            <View style={styles.flow} accessibilityLabel="Flujo de procesamiento">
              {['Audio ES', 'Transcripción', 'Traducción EN', 'WAV EN'].map((item, index) => (
                <View key={item} style={styles.flowItem}>
                  <Text style={styles.flowText}>{item}</Text>
                  {index < 3 ? <Ionicons name="arrow-forward" size={13} color={colors.inkFaint} /> : null}
                </View>
              ))}
            </View>
          </View>

          <StatusNotice status={status} statusError={statusError} />

          {!selectedFile && !isProcessing && !result ? (
            <FileDropCard
              onPick={handlePick}
              onDrop={handleDrop}
              picking={picking}
              disabled={isValidating}
              maxUploadMb={limits.maxUploadMb}
              maxAudioSeconds={limits.maxAudioSeconds}
            />
          ) : null}

          {isValidating ? (
            <View style={styles.validating} accessibilityRole="status">
              <ActivityIndicator size="small" color={colors.primary} />
              <Text style={styles.validatingText}>Verificando formato, peso y duración del audio…</Text>
            </View>
          ) : null}

          {selectedFile ? (
            <View style={styles.selectedSection}>
              <SelectedAudioBubble file={selectedFile} onRemove={handleReset} disabled={isProcessing} />
              {!isProcessing && !result ? (
                <View style={styles.actions}>
                  <Pressable
                    accessibilityRole="button"
                    accessibilityLabel="Elegir otro audio"
                    onPress={handlePick}
                    style={({ pressed }) => [styles.secondaryButton, pressed && styles.pressed]}
                  >
                    <Ionicons name="folder-open-outline" size={16} color={colors.primary} />
                    <Text style={styles.secondaryButtonText}>Cambiar audio</Text>
                  </Pressable>
                  <Pressable
                    accessibilityRole="button"
                    accessibilityLabel="Traducir"
                    onPress={handleProcess}
                    disabled={!canTranslate}
                    style={({ pressed }) => [
                      styles.primaryButton,
                      pressed && styles.pressed,
                      !canTranslate && styles.disabled,
                    ]}
                  >
                    <Ionicons name="language-outline" size={16} color={colors.white} />
                    <Text style={styles.primaryButtonText}>Traducir audio</Text>
                  </Pressable>
                </View>
              ) : null}
            </View>
          ) : null}

          {isProcessing ? <ProcessingBubble elapsedSeconds={elapsed} /> : null}
          {error ? (
            <ErrorBubble
              message={error.message}
              requestId={error.requestId}
              onRetry={selectedFile && !isProcessing ? handleProcess : undefined}
            />
          ) : null}
          {result ? (
            <View style={styles.resultSection}>
              <ResultCard result={result} />
              <Pressable
                accessibilityRole="button"
                accessibilityLabel="Traducir otro audio"
                onPress={handleReset}
                style={({ pressed }) => [styles.anotherButton, pressed && styles.pressed]}
              >
                <Ionicons name="add" size={17} color={colors.primary} />
                <Text style={styles.anotherButtonText}>Traducir otro audio</Text>
              </Pressable>
            </View>
          ) : null}

          <View style={styles.notes}>
            <View style={styles.noteRow}>
              <Ionicons name="time-outline" size={15} color={colors.primary} />
              <Text style={styles.noteText}>
                La primera carga puede tardar. Las solicitudes se procesan en secuencia; no es
                una herramienta de tiempo real.
              </Text>
            </View>
            <View style={styles.noteRow}>
              <Ionicons name="shield-checkmark-outline" size={15} color={colors.primary} />
              <Text style={styles.noteText}>
                El resultado se conserva de forma temporal y se elimina según el TTL del
                servicio. No hay cuentas ni historial persistente.
              </Text>
            </View>
            <View style={styles.noteRow}>
              <Ionicons name="volume-medium-outline" size={15} color={colors.primary} />
              <Text style={styles.noteText}>
                La voz generada usa el audio como referencia y solo busca similitud; no
                garantiza identidad, emoción ni prosodia.
              </Text>
            </View>
          </View>
        </View>
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  root: { flex: 1, backgroundColor: colors.background },
  scrollContent: { flexGrow: 1, paddingHorizontal: 16 },
  shell: { width: '100%', maxWidth: 900, alignSelf: 'center' },
  header: {
    flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', gap: 12,
    marginBottom: 36,
  },
  brandRow: { flexDirection: 'row', alignItems: 'center', gap: 10 },
  brandCopy: { minWidth: 0 },
  brand: { fontFamily: fonts.extrabold, fontSize: 20, letterSpacing: -0.5, color: colors.ink },
  brandSub: { fontFamily: fonts.bold, fontSize: 8.5, letterSpacing: 0.9, color: colors.inkFaint, marginTop: 2 },
  hero: { alignItems: 'center', marginBottom: 24 },
  heroWide: { flexDirection: 'row', alignItems: 'flex-end', justifyContent: 'space-between', gap: 28 },
  heroCopy: { flex: 1, maxWidth: 590 },
  eyebrow: { fontFamily: fonts.extrabold, fontSize: 9.5, letterSpacing: 1.2, color: colors.primary },
  title: { fontFamily: fonts.extrabold, fontSize: 34, lineHeight: 42, letterSpacing: -1.2, color: colors.ink, marginTop: 8 },
  lead: { fontFamily: fonts.medium, fontSize: 14, lineHeight: 22, color: colors.inkSoft, marginTop: 10, maxWidth: 580 },
  flow: { flexDirection: 'row', flexWrap: 'wrap', alignItems: 'center', gap: 5, marginTop: 16 },
  flowItem: { flexDirection: 'row', alignItems: 'center', gap: 5 },
  flowText: { fontFamily: fonts.bold, fontSize: 9.5, color: colors.inkSoft },
  notice: { flexDirection: 'row', alignItems: 'flex-start', gap: 10, borderRadius: 16, padding: 13, marginBottom: 18 },
  noticeError: { backgroundColor: '#FFF4F1', borderWidth: 1, borderColor: '#F4D8D1' },
  noticeWarning: { backgroundColor: colors.accentSoft, borderWidth: 1, borderColor: '#F4DCBE' },
  noticeBusy: { backgroundColor: colors.primarySoft, borderWidth: 1, borderColor: '#CDEBDF' },
  noticeCopy: { flex: 1 },
  noticeTitle: { fontFamily: fonts.bold, fontSize: 12, color: colors.ink },
  noticeText: { fontFamily: fonts.medium, fontSize: 11, lineHeight: 16, color: colors.inkSoft, marginTop: 2 },
  validating: { flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 9, minHeight: 150 },
  validatingText: { fontFamily: fonts.medium, fontSize: 12, color: colors.inkSoft },
  selectedSection: { alignItems: 'center' },
  actions: { width: '100%', maxWidth: 580, flexDirection: 'row', justifyContent: 'flex-end', flexWrap: 'wrap', gap: 9, marginTop: 14 },
  secondaryButton: { flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 6, minHeight: 44, paddingHorizontal: 14, borderRadius: 13, borderWidth: 1, borderColor: colors.line, backgroundColor: colors.surface },
  secondaryButtonText: { fontFamily: fonts.bold, fontSize: 11.5, color: colors.primary },
  primaryButton: { flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 7, minHeight: 44, paddingHorizontal: 16, borderRadius: 13, backgroundColor: colors.primary, ...shadows.floating },
  primaryButtonText: { fontFamily: fonts.bold, fontSize: 11.5, color: colors.white },
  resultSection: { alignItems: 'center' },
  anotherButton: { flexDirection: 'row', alignItems: 'center', gap: 6, marginTop: 16, paddingHorizontal: 14, paddingVertical: 10, borderRadius: 12, backgroundColor: colors.surface, borderWidth: 1, borderColor: colors.line },
  anotherButtonText: { fontFamily: fonts.bold, fontSize: 11.5, color: colors.primary },
  notes: { marginTop: 32, marginBottom: 8, paddingTop: 18, borderTopWidth: 1, borderTopColor: colors.line, gap: 9 },
  noteRow: { flexDirection: 'row', alignItems: 'flex-start', gap: 8 },
  noteText: { flex: 1, fontFamily: fonts.medium, fontSize: 10.5, lineHeight: 16, color: colors.inkFaint },
  pressed: { opacity: 0.75 },
  disabled: { opacity: 0.55 },
});
