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
import { LinearGradient } from 'expo-linear-gradient';
import { Ionicons } from '@expo/vector-icons';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import * as DocumentPicker from 'expo-document-picker';

import { translateAudio } from '../api/client';
import useEngineStatus from '../hooks/useEngineStatus';
import { colors, fonts, shadows } from '../theme';
import {
  DEFAULT_MAX_AUDIO_SECONDS,
  DEFAULT_MAX_UPLOAD_MB,
  formatBytes,
  formatDuration,
  getAudioDuration,
  validateAudioFile,
} from '../utils/audio';
import BrandMark from '../components/BrandMark';
import ChatPattern from '../components/ChatPattern';
import EngineStatusPill from '../components/EngineStatusPill';
import ErrorBubble from '../components/ErrorBubble';
import FileDropCard from '../components/FileDropCard';
import ProcessingBubble from '../components/ProcessingBubble';
import ResultCard from '../components/ResultCard';
import SelectedAudioBubble from '../components/SelectedAudioBubble';
import TranslatorSidebar from '../components/TranslatorSidebar';

const AUDIO_TYPES = [
  'audio/wav',
  'audio/mpeg',
  'audio/mp4',
  'audio/ogg',
  'audio/flac',
  'audio/webm',
  'audio/*',
];

function AssistantAvatar() {
  return (
    <LinearGradient
      colors={['#16766A', '#073E38']}
      style={styles.botAvatar}
    >
      <Ionicons name="sparkles" size={12} color={colors.white} />
    </LinearGradient>
  );
}

export default function TranslatorScreen() {
  const insets = useSafeAreaInsets();
  const { width } = useWindowDimensions();
  const isDesktop = width >= 980;
  const scrollRef = useRef(null);
  const durationRequest = useRef(0);

  const {
    status,
    error: statusError,
    loading: statusLoading,
    refresh: refreshStatus,
  } = useEngineStatus();

  const [selectedFile, setSelectedFile] = useState(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [picking, setPicking] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [elapsed, setElapsed] = useState(0);

  const limits = {
    maxUploadMb: status?.limits?.max_upload_mb ?? DEFAULT_MAX_UPLOAD_MB,
    maxAudioSeconds: status?.limits?.max_audio_seconds ?? DEFAULT_MAX_AUDIO_SECONDS,
  };

  useEffect(() => {
    if (!isProcessing) return undefined;
    const started = Date.now();
    const timer = setInterval(() => {
      setElapsed((Date.now() - started) / 1000);
    }, 1000);
    return () => clearInterval(timer);
  }, [isProcessing]);

  useEffect(() => {
    if (!result && !isProcessing && !error) return undefined;
    const timer = setTimeout(() => {
      scrollRef.current?.scrollToEnd({ animated: true });
    }, 140);
    return () => clearTimeout(timer);
  }, [result, isProcessing, error]);

  const applyPickedAsset = async (asset) => {
    const candidate = {
      uri: asset.uri,
      name: asset.name,
      size: asset.size,
      mimeType: asset.mimeType,
      file: asset.file,
      durationSec: null,
    };
    const validation = validateAudioFile(candidate, limits);
    if (!validation.ok) {
      setError({ message: validation.message, code: 'client_validation' });
      return;
    }

    setSelectedFile(candidate);
    setResult(null);
    setError(null);
    setElapsed(0);

    const requestId = durationRequest.current + 1;
    durationRequest.current = requestId;
    const duration = await getAudioDuration(asset.uri);
    if (!duration || durationRequest.current !== requestId) return;

    const updated = { ...candidate, durationSec: duration };
    const durationValidation = validateAudioFile(updated, limits);
    if (!durationValidation.ok) {
      setSelectedFile(null);
      setError({ message: durationValidation.message, code: 'client_validation' });
      return;
    }
    setSelectedFile((current) =>
      current && current.uri === candidate.uri ? updated : current,
    );
  };

  const handlePick = async () => {
    if (isProcessing || picking) return;
    setPicking(true);
    try {
      const selection = await DocumentPicker.getDocumentAsync({
        type: AUDIO_TYPES,
        multiple: false,
        copyToCacheDirectory: true,
        base64: false,
      });
      if (!selection.canceled && selection.assets?.[0]) {
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

  const handleProcess = async () => {
    if (!selectedFile || isProcessing) return;
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
        message:
          requestError?.message ||
          'No se pudo procesar el audio. Inténtalo nuevamente.',
        code: requestError?.code || 'request_failed',
        requestId: requestError?.requestId,
      });
    } finally {
      setIsProcessing(false);
    }
  };

  const handleReset = () => {
    if (isProcessing) return;
    durationRequest.current += 1;
    setSelectedFile(null);
    setResult(null);
    setError(null);
    setElapsed(0);
    scrollRef.current?.scrollTo({ y: 0, animated: true });
  };

  const primaryAction = () => {
    if (isProcessing) return undefined;
    if (!selectedFile || result) return handlePick;
    return handleProcess;
  };

  const primaryLabel = isProcessing
    ? 'Procesando'
    : result
      ? 'Nuevo audio'
      : selectedFile
        ? 'Traducir'
        : 'Elegir audio';

  const primaryIcon = isProcessing
    ? null
    : result
      ? 'add'
      : selectedFile
        ? 'send'
        : 'folder-open-outline';

  const showDropCard = !selectedFile && !isProcessing;

  return (
    <View style={styles.root}>
      <View style={styles.ambientOne} />
      <View style={styles.ambientTwo} />

      <View
        style={[
          styles.shell,
          isDesktop ? styles.shellDesktop : styles.shellMobile,
          { paddingTop: isDesktop ? 18 : 0, paddingBottom: isDesktop ? 18 : 0 },
        ]}
      >
        {isDesktop ? (
          <TranslatorSidebar
            status={status}
            statusError={statusError}
            statusLoading={statusLoading}
            onRefreshStatus={refreshStatus}
            limits={limits}
          />
        ) : null}

        <View style={[styles.panel, isDesktop && styles.panelDesktop]}>
          <View
            style={[
              styles.panelHeader,
              {
                paddingTop: isDesktop ? 13 : insets.top + 9,
              },
            ]}
          >
            <BrandMark size={isDesktop ? 38 : 36} />
            <View style={styles.identity}>
              <View style={styles.nameRow}>
                <Text style={styles.name}>Hilo</Text>
                <View style={styles.direction}>
                  <Text style={styles.directionText}>ES → EN</Text>
                </View>
              </View>
              <Text style={styles.subtitle}>
                {isDesktop
                  ? 'Whisper Small · MarianMT · XTTS-v2'
                  : 'Traductor de voz español → inglés'}
              </Text>
            </View>
            <EngineStatusPill
              status={status}
              error={statusError}
              loading={statusLoading}
              onRefresh={refreshStatus}
            />
          </View>

          <View style={styles.chatArea}>
            <ChatPattern />
            <ScrollView
              ref={scrollRef}
              style={styles.scroll}
              showsVerticalScrollIndicator={false}
              contentContainerStyle={styles.scrollContent}
            >
              <View style={styles.thread}>
                <View style={styles.dateChip}>
                  <Ionicons name="lock-closed" size={9} color={colors.inkSoft} />
                  <Text style={styles.dateText}>TRADUCCIÓN PRIVADA · ES → EN</Text>
                </View>

                <View style={styles.assistantRow}>
                  <AssistantAvatar />
                  <View style={styles.assistantBubble}>
                    <Text style={styles.welcomeTitle}>Hola, soy Hilo.</Text>
                    <Text style={styles.welcomeText}>
                      Sube una nota de voz en español. La escucharé, la traduciré
                      al inglés y generaré una nueva voz con tu referencia.
                    </Text>
                    <View style={styles.modelChips}>
                      {['Whisper', 'MarianMT', 'XTTS-v2'].map((model) => (
                        <View key={model} style={styles.modelChip}>
                          <Text style={styles.modelChipText}>{model}</Text>
                        </View>
                      ))}
                    </View>
                  </View>
                </View>

                {status?.status === 'degraded' ? (
                  <View style={styles.warning}>
                    <Ionicons name="warning-outline" size={14} color="#A4682C" />
                    <Text style={styles.warningText}>
                      El motor está en modo degradado: XTTS-v2 no está habilitado.
                      El operador debe aceptar la licencia CPML.
                    </Text>
                  </View>
                ) : null}

                {showDropCard ? (
                  <View style={styles.dropWrap}>
                    <FileDropCard
                      onPick={handlePick}
                      picking={picking}
                      maxUploadMb={limits.maxUploadMb}
                      maxAudioSeconds={limits.maxAudioSeconds}
                    />
                  </View>
                ) : null}

                {selectedFile ? (
                  <View style={styles.userRow}>
                    <SelectedAudioBubble
                      file={selectedFile}
                      onRemove={handleReset}
                      disabled={isProcessing}
                    />
                  </View>
                ) : null}

                {isProcessing ? (
                  <View style={styles.assistantRow}>
                    <AssistantAvatar />
                    <View style={styles.assistantContent}>
                      <ProcessingBubble elapsedSeconds={elapsed} />
                    </View>
                  </View>
                ) : null}

                {error ? (
                  <View style={styles.assistantRow}>
                    <AssistantAvatar />
                    <View style={styles.assistantContent}>
                      <ErrorBubble
                        message={error.message}
                        requestId={error.requestId}
                        onRetry={
                          selectedFile && !isProcessing ? handleProcess : undefined
                        }
                      />
                    </View>
                  </View>
                ) : null}

                {result ? (
                  <View style={styles.assistantRow}>
                    <AssistantAvatar />
                    <View style={styles.assistantContent}>
                      <ResultCard result={result} />
                    </View>
                  </View>
                ) : null}

                {result ? (
                  <View style={styles.endNote}>
                    <Ionicons name="time-outline" size={10} color={colors.inkFaint} />
                    <Text style={styles.endNoteText}>
                      Resultado temporal. El audio se elimina al expirar.
                    </Text>
                  </View>
                ) : null}
              </View>
            </ScrollView>
          </View>

          <View
            style={[
              styles.composer,
              { paddingBottom: Math.max(insets.bottom, 10) },
            ]}
          >
            <View style={styles.composerInner}>
              <Pressable
                accessibilityRole="button"
                accessibilityLabel="Adjuntar archivo de audio"
                onPress={handlePick}
                disabled={isProcessing || picking}
                style={({ pressed }) => [
                  styles.attach,
                  pressed && styles.pressed,
                  (isProcessing || picking) && styles.disabled,
                ]}
              >
                {picking ? (
                  <ActivityIndicator size="small" color={colors.primary} />
                ) : (
                  <Ionicons name="add" size={23} color={colors.primary} />
                )}
              </Pressable>

              <View style={styles.composerPill}>
                <View style={styles.composerCopy}>
                  <Text numberOfLines={1} style={styles.composerTitle}>
                    {isProcessing
                      ? 'Procesando audio…'
                      : result
                        ? 'Traducción lista'
                        : selectedFile
                          ? selectedFile.name
                          : 'Adjunta una nota de voz'}
                  </Text>
                  <Text numberOfLines={1} style={styles.composerSubtitle}>
                    {isProcessing
                      ? 'Puede tardar la primera vez'
                      : result
                        ? 'Escucha o descarga el resultado'
                        : selectedFile
                          ? `${formatBytes(selectedFile.size)}${
                              selectedFile.durationSec
                                ? ` · ${formatDuration(selectedFile.durationSec)}`
                                : ''
                            }`
                          : isDesktop
                            ? `WAV, MP3, M4A, OGG, FLAC o WEBM · máx. ${limits.maxUploadMb} MB`
                            : `WAV, MP3… · máx. ${limits.maxUploadMb} MB`}
                  </Text>
                </View>
                {selectedFile && !isProcessing && !result ? (
                  <Pressable
                    accessibilityRole="button"
                    accessibilityLabel="Quitar audio"
                    onPress={handleReset}
                    hitSlop={6}
                    style={styles.clear}
                  >
                    <Ionicons name="close" size={13} color={colors.inkFaint} />
                  </Pressable>
                ) : null}
              </View>

              <Pressable
                accessibilityRole="button"
                accessibilityLabel={primaryLabel}
                onPress={primaryAction()}
                disabled={isProcessing || picking}
                style={({ pressed }) => [
                  styles.primary,
                  selectedFile || result ? styles.primaryActive : styles.primaryIdle,
                  pressed && styles.pressed,
                  (isProcessing || picking) && styles.primaryProcessing,
                ]}
              >
                {isProcessing ? (
                  <ActivityIndicator size="small" color={colors.white} />
                ) : (
                  <Ionicons name={primaryIcon} size={15} color={colors.white} />
                )}
                <Text style={styles.primaryText}>{primaryLabel}</Text>
              </Pressable>
            </View>
          </View>
        </View>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  root: {
    flex: 1,
    backgroundColor: colors.background,
    overflow: 'hidden',
  },
  ambientOne: {
    position: 'absolute',
    width: 360,
    height: 360,
    borderRadius: 180,
    backgroundColor: 'rgba(244,161,92,0.08)',
    top: -160,
    right: -100,
  },
  ambientTwo: {
    position: 'absolute',
    width: 300,
    height: 300,
    borderRadius: 150,
    backgroundColor: 'rgba(103,93,224,0.05)',
    bottom: -140,
    left: -80,
  },
  shell: {
    flex: 1,
    width: '100%',
    maxWidth: 1240,
    alignSelf: 'center',
  },
  shellDesktop: {
    flexDirection: 'row',
    gap: 18,
    paddingHorizontal: 18,
  },
  shellMobile: {
    paddingHorizontal: 0,
  },
  panel: {
    flex: 1,
    overflow: 'hidden',
    backgroundColor: colors.surface,
  },
  panelDesktop: {
    borderRadius: 30,
    borderWidth: 1,
    borderColor: 'rgba(21,35,32,0.06)',
    ...shadows.card,
  },
  panelHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 9,
    paddingHorizontal: 14,
    paddingBottom: 10,
    backgroundColor: colors.background,
    borderBottomWidth: 1,
    borderBottomColor: 'rgba(21,35,32,0.045)',
    zIndex: 2,
  },
  identity: {
    flex: 1,
    minWidth: 0,
  },
  nameRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  name: {
    fontFamily: fonts.extrabold,
    fontSize: 17,
    letterSpacing: -0.4,
    color: colors.ink,
  },
  direction: {
    backgroundColor: colors.primarySoft,
    borderRadius: 99,
    paddingHorizontal: 6,
    paddingVertical: 2,
  },
  directionText: {
    fontFamily: fonts.extrabold,
    fontSize: 8,
    letterSpacing: 0.4,
    color: colors.primary,
  },
  subtitle: {
    fontFamily: fonts.medium,
    fontSize: 10,
    color: colors.inkFaint,
    marginTop: 2,
  },
  chatArea: {
    flex: 1,
    backgroundColor: colors.chatBackground,
  },
  scroll: {
    flex: 1,
  },
  scrollContent: {
    flexGrow: 1,
    paddingHorizontal: 13,
    paddingTop: 13,
    paddingBottom: 18,
    alignItems: 'center',
  },
  thread: {
    width: '100%',
    maxWidth: 730,
    gap: 11,
  },
  dateChip: {
    alignSelf: 'center',
    flexDirection: 'row',
    alignItems: 'center',
    gap: 5,
    backgroundColor: 'rgba(255,255,255,0.82)',
    borderRadius: 99,
    paddingHorizontal: 10,
    paddingVertical: 5,
    marginBottom: 2,
    ...shadows.soft,
  },
  dateText: {
    fontFamily: fonts.extrabold,
    fontSize: 8.5,
    letterSpacing: 0.85,
    color: colors.inkSoft,
  },
  assistantRow: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: 7,
    width: '100%',
  },
  botAvatar: {
    width: 30,
    height: 30,
    borderRadius: 10,
    alignItems: 'center',
    justifyContent: 'center',
    marginTop: 3,
    shadowColor: colors.primaryDeep,
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.15,
    shadowRadius: 6,
    elevation: 2,
  },
  assistantBubble: {
    maxWidth: 600,
    flexShrink: 1,
    backgroundColor: colors.surface,
    borderRadius: 20,
    borderTopLeftRadius: 7,
    borderWidth: 1,
    borderColor: 'rgba(21,35,32,0.045)',
    paddingHorizontal: 14,
    paddingVertical: 12,
    ...shadows.soft,
  },
  assistantContent: {
    flex: 1,
    maxWidth: 690,
  },
  welcomeTitle: {
    fontFamily: fonts.extrabold,
    fontSize: 15,
    letterSpacing: -0.25,
    color: colors.ink,
    marginBottom: 4,
  },
  welcomeText: {
    fontFamily: fonts.medium,
    fontSize: 13.5,
    lineHeight: 20,
    color: colors.inkSoft,
  },
  modelChips: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 4,
    marginTop: 9,
  },
  modelChip: {
    borderRadius: 99,
    paddingHorizontal: 7,
    paddingVertical: 3,
    backgroundColor: colors.surfaceMuted,
  },
  modelChipText: {
    fontFamily: fonts.bold,
    fontSize: 8.5,
    color: colors.inkSoft,
  },
  warning: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: 7,
    marginLeft: 35,
    padding: 10,
    borderRadius: 14,
    backgroundColor: '#FFF5E8',
    borderWidth: 1,
    borderColor: '#F4DCBE',
  },
  warningText: {
    flex: 1,
    fontFamily: fonts.medium,
    fontSize: 10,
    lineHeight: 15,
    color: '#8A5A23',
  },
  dropWrap: {
    width: '100%',
    alignItems: 'center',
    marginTop: 1,
    marginBottom: 2,
  },
  userRow: {
    width: '100%',
    alignItems: 'flex-end',
    paddingLeft: 35,
  },
  endNote: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 4,
    paddingVertical: 2,
  },
  endNoteText: {
    fontFamily: fonts.medium,
    fontSize: 9,
    color: colors.inkFaint,
  },
  composer: {
    backgroundColor: colors.background,
    borderTopWidth: 1,
    borderTopColor: 'rgba(21,35,32,0.045)',
    paddingHorizontal: 11,
    paddingTop: 9,
  },
  composerInner: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 7,
    width: '100%',
    maxWidth: 780,
    alignSelf: 'center',
  },
  attach: {
    width: 48,
    height: 48,
    borderRadius: 16,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: colors.surface,
    borderWidth: 1,
    borderColor: colors.line,
    ...shadows.soft,
  },
  composerPill: {
    flex: 1,
    minWidth: 0,
    height: 50,
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    paddingHorizontal: 12,
    borderRadius: 16,
    backgroundColor: colors.surface,
    borderWidth: 1,
    borderColor: 'rgba(21,35,32,0.05)',
    ...shadows.soft,
  },
  composerCopy: {
    flex: 1,
    minWidth: 0,
  },
  composerTitle: {
    fontFamily: fonts.semibold,
    fontSize: 12,
    color: colors.ink,
  },
  composerSubtitle: {
    fontFamily: fonts.medium,
    fontSize: 9.5,
    color: colors.inkFaint,
    marginTop: 1,
  },
  clear: {
    width: 22,
    height: 22,
    borderRadius: 11,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: colors.surfaceMuted,
  },
  primary: {
    minWidth: 104,
    height: 50,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 5,
    paddingHorizontal: 12,
    borderRadius: 16,
  },
  primaryActive: {
    backgroundColor: colors.primary,
    shadowColor: colors.primary,
    shadowOffset: { width: 0, height: 6 },
    shadowOpacity: 0.22,
    shadowRadius: 10,
    elevation: 4,
  },
  primaryIdle: {
    backgroundColor: colors.primary,
  },
  primaryProcessing: {
    backgroundColor: colors.primaryBright,
  },
  primaryText: {
    fontFamily: fonts.bold,
    fontSize: 11,
    color: colors.white,
  },
  pressed: {
    opacity: 0.8,
  },
  disabled: {
    opacity: 0.6,
  },
});
