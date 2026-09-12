# Responsabilidades de Modelos en el Pipeline y Estrategia de Aprendizaje

El sistema se basa en una arquitectura modular que interconecta distintos modelos de inteligencia artificial en un pipeline secuencial. Para distinguir la integración del aprendizaje académico, el proyecto diferencia qué modelos se emplean listos para usarse y cuáles reciben entrenamiento específico.

## 1. Módulo de Reconocimiento Automático del Habla (ASR/STT)
*   **Responsabilidad:** Extraer el contenido lingüístico del audio de entrada transformándolo de voz a texto en español.
*   **Posición en el pipeline:** Primera etapa. Recibe el archivo de audio original y entrega una transcripción textual en español.
*   **Estrategia de Entrenamiento:** **Solo Inferencia.** Se utilizará un modelo ASR preentrenado (ej. Whisper u otro que soporte español). No se entrenará desde cero ni se le aplicará fine-tuning.

## 2. Módulo de Traducción Automática Neuronal (NMT)
*   **Responsabilidad:** Trasladar el contenido lingüístico reconociendo el significado y contexto, transformando el texto en español a texto en inglés.
*   **Posición en el pipeline:** Segunda etapa. Recibe la transcripción en español del módulo ASR y entrega un texto equivalente en inglés.
*   **Estrategia de Entrenamiento:** **Fine-Tuning.** Este es el núcleo de "aprendizaje propio" del proyecto. Se tomará un modelo preentrenado base (ej. OPUS-MT, Marian, etc.) y se someterá a una adaptación de pesos (fine-tuning) utilizando un corpus paralelo español-inglés, dividido en fases de entrenamiento, validación y prueba.

## 3. Módulo de Síntesis y Clonación de Voz (Zero-Shot TTS)
*   **Responsabilidad:** Sintetizar el texto en inglés de manera que el audio resultante suene con características vocales reconocibles del hablante original, preservando la continuidad de la identidad.
*   **Posición en el pipeline:** Tercera etapa (final). Recibe el texto en inglés del módulo NMT y utiliza el audio original de entrada del usuario para extraer el "speaker embedding" (referencia vocal) condicionado para la síntesis de voz generada cruzando idiomas (cross-lingual).
*   **Estrategia de Entrenamiento:** **Solo Inferencia (Zero-Shot).** Se integrará un modelo preentrenado de clonación de voz capaz de generalizar y clonar a partir de una referencia breve (zero-shot) sin requerir entrenamiento ni ajuste específico por cada usuario individual.

## 4. Módulo Codificador de Hablante (Evaluación)
*   **Responsabilidad:** Extraer representaciones vectoriales (embeddings) de los audios para medir objetivamente la similitud vocal entre el locutor original y el audio generado sintéticamente.
*   **Posición en el pipeline:** Etapa de evaluación post-procesamiento.
*   **Estrategia de Entrenamiento:** **Solo Inferencia.** Se utilizará un codificador preentrenado para verificar métricas de similitud sin reentrenarlo dentro del alcance del proyecto.
