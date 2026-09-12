# Contexto y Alcance Funcional

## 1. Contexto del Proyecto
**Título:** Traducción de Mensajes de Audio con Clonación de Voz mediante Inteligencia Artificial

El proyecto busca resolver una limitación en los sistemas convencionales de traducción de voz (ASR -> Traducción -> TTS), donde la etapa final suele sintetizar el mensaje con una voz genérica, perdiendo la identidad vocal del emisor original. Apoyándose en antecedentes como Translatotron y modelos Zero-Shot (YourTTS, XTTS, OpenVoice), el sistema propone mantener la continuidad de identidad en la voz traducida utilizando arquitecturas modulares. 

Se desarrolla como un **prototipo académico reproducible en Google Colab** para estudiar el procesamiento del lenguaje hablado, separando cada etapa (reconocimiento, traducción y síntesis) para evaluar los errores y la calidad de forma independiente.

## 2. Alcance Funcional (Requerimientos)
El sistema integra reconocimiento del habla, procesamiento de lenguaje natural y síntesis de voz condicionada.

### Entradas y Salidas
*   **Entrada:** Un mensaje completo de audio (o video del que se extraerá la pista de audio) en español, emitido por **un solo hablante**.
*   **Procesamiento:** El sistema utiliza la totalidad de este archivo tanto para generar la transcripción (reconocimiento) como de referencia de identidad (clonación).
*   **Salida:** Un nuevo archivo de audio en inglés sintetizado que aproxima la identidad vocal del emisor original. Adicionalmente, el sistema expone y almacena las transcripciones intermedias (en español e inglés) para fines de validación.

### Funcionalidades Clave
1.  **Carga y verificación:** Procesar archivos de audio compatibles (y extraer audio de video si aplica).
2.  **Transcripción:** Mostrar el texto reconocido del audio origen en español.
3.  **Traducción:** Mostrar el texto traducido al inglés.
4.  **Generación de audio:** Sintetizar el texto en inglés mediante clonación Zero-Shot usando las características del audio base.
5.  **Evaluación modular:** Registrar resultados intermedios y permitir pruebas independientes y de extremo a extremo.

## 3. Condiciones y Restricciones (Exclusiones del alcance)
Para mantener la viabilidad computacional y enfocarse en los objetivos, el proyecto **excluye** explícitamente:
*   Traducción en tiempo real (streaming) o exigencias de baja latencia.
*   Diarización o procesamiento de múltiples hablantes en un mismo mensaje.
*   Preservación garantizada y explícita de emociones, ritmo o prosodia exacta. Se busca similitud vocal, no una copia idéntica.
*   Análisis del contenido visual si la entrada es un video (solo se usa la pista de audio).
