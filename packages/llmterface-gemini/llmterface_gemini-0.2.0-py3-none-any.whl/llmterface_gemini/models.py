from enum import Enum


class GeminiEmbeddingModelType(Enum):
    EMBEDDING_GECKO_001 = "embedding-gecko-001"  # Obtain a distributed representation of a text.
    EMBEDDING_001 = "embedding-001"  # Obtain a distributed representation of a text.
    TEXT_EMBEDDING_004 = "text-embedding-004"  # Obtain a distributed representation of a text.
    GEMINI_EMBEDDING_EXP_03_07 = "gemini-embedding-exp-03-07"  # Obtain a distributed representation of a text.
    GEMINI_EMBEDDING_EXP = "gemini-embedding-exp"  # Obtain a distributed representation of a text.
    GEMINI_EMBEDDING_001 = "gemini-embedding-001"  # Obtain a distributed representation of a text.


class GeminiAudioModelType(Enum):
    CHAT_2_5_FLASH_NATIVE_AUDIO_LATEST = (
        "gemini-2.5-flash-native-audio-latest"  # Latest release of Gemini 2.5 Flash Native Audio
    )
    CHAT_2_5_FLASH_NATIVE_AUDIO_PREVIEW_09_2025 = (
        "gemini-2.5-flash-native-audio-preview-09-2025"  # Gemini 2.5 Flash Native Audio Preview 09-2025
    )
    CHAT_2_5_FLASH_NATIVE_AUDIO_PREVIEW_12_2025 = (
        "gemini-2.5-flash-native-audio-preview-12-2025"  # Gemini 2.5 Flash Native Audio Preview 12-2025
    )


class GeminiVideoModelType(Enum):
    VEO_2_0_GENERATE_001 = "veo-2.0-generate-001"  # Vertex served Veo 2 model. Access to this model requires billing to be enabled on the associated Google Cloud Platform account. Please visit https://console.cloud.google.com/billing to enable it.
    VEO_3_0_GENERATE_001 = "veo-3.0-generate-001"  # Veo 3
    VEO_3_0_FAST_GENERATE_001 = "veo-3.0-fast-generate-001"  # Veo 3 fast
    VEO_3_1_GENERATE_PREVIEW = "veo-3.1-generate-preview"  # Veo 3.1
    VEO_3_1_FAST_GENERATE_PREVIEW = "veo-3.1-fast-generate-preview"  # Veo 3.1 fast


class GeminiImageModelType(Enum):
    IMAGEN_4_0_GENERATE_PREVIEW_06_06 = "imagen-4.0-generate-preview-06-06"  # Vertex served Imagen 4.0 model
    IMAGEN_4_0_ULTRA_GENERATE_PREVIEW_06_06 = (
        "imagen-4.0-ultra-generate-preview-06-06"  # Vertex served Imagen 4.0 ultra model
    )
    IMAGEN_4_0_GENERATE_001 = "imagen-4.0-generate-001"  # Vertex served Imagen 4.0 model
    IMAGEN_4_0_ULTRA_GENERATE_001 = "imagen-4.0-ultra-generate-001"  # Vertex served Imagen 4.0 ultra model
    IMAGEN_4_0_FAST_GENERATE_001 = "imagen-4.0-fast-generate-001"  # Vertex served Imagen 4.0 Fast model


class GeminiTextModelType(Enum):
    CHAT_2_5_FLASH = "gemini-2.5-flash"  # Stable version of Gemini 2.5 Flash, our mid-size multimodal model that supports up to 1 million tokens, released in June of 2025.
    CHAT_2_5_PRO = "gemini-2.5-pro"  # Stable release (June 17th, 2025) of Gemini 2.5 Pro
    CHAT_2_0_FLASH_EXP = "gemini-2.0-flash-exp"  # Gemini 2.0 Flash Experimental
    CHAT_2_0_FLASH = "gemini-2.0-flash"  # Gemini 2.0 Flash
    CHAT_2_0_FLASH_001 = "gemini-2.0-flash-001"  # Stable version of Gemini 2.0 Flash, our fast and versatile multimodal model for scaling across diverse tasks, released in January of 2025.
    CHAT_2_0_FLASH_EXP_IMAGE_GENERATION = (
        "gemini-2.0-flash-exp-image-generation"  # Gemini 2.0 Flash (Image Generation) Experimental
    )
    CHAT_2_0_FLASH_LITE_001 = "gemini-2.0-flash-lite-001"  # Stable version of Gemini 2.0 Flash-Lite
    CHAT_2_0_FLASH_LITE = "gemini-2.0-flash-lite"  # Gemini 2.0 Flash-Lite
    CHAT_2_0_FLASH_LITE_PREVIEW_02_05 = (
        "gemini-2.0-flash-lite-preview-02-05"  # Preview release (February 5th, 2025) of Gemini 2.0 Flash-Lite
    )
    CHAT_2_0_FLASH_LITE_PREVIEW = (
        "gemini-2.0-flash-lite-preview"  # Preview release (February 5th, 2025) of Gemini 2.0 Flash-Lite
    )
    CHAT_EXP_1206 = "gemini-exp-1206"  # Experimental release (March 25th, 2025) of Gemini 2.5 Pro
    CHAT_2_5_FLASH_PREVIEW_TTS = "gemini-2.5-flash-preview-tts"  # Gemini 2.5 Flash Preview TTS
    CHAT_2_5_PRO_PREVIEW_TTS = "gemini-2.5-pro-preview-tts"  # Gemini 2.5 Pro Preview TTS
    GEMMA_3_1B_IT = "gemma-3-1b-it"
    GEMMA_3_4B_IT = "gemma-3-4b-it"
    GEMMA_3_12B_IT = "gemma-3-12b-it"
    GEMMA_3_27B_IT = "gemma-3-27b-it"
    GEMMA_3N_E4B_IT = "gemma-3n-e4b-it"
    GEMMA_3N_E2B_IT = "gemma-3n-e2b-it"
    CHAT_FLASH_LATEST = "gemini-flash-latest"  # Latest release of Gemini Flash
    CHAT_FLASH_LITE_LATEST = "gemini-flash-lite-latest"  # Latest release of Gemini Flash-Lite
    CHAT_PRO_LATEST = "gemini-pro-latest"  # Latest release of Gemini Pro
    CHAT_2_5_FLASH_LITE = "gemini-2.5-flash-lite"  # Stable version of Gemini 2.5 Flash-Lite, released in July of 2025
    CHAT_2_5_FLASH_IMAGE_PREVIEW = "gemini-2.5-flash-image-preview"  # Gemini 2.5 Flash Preview Image
    CHAT_2_5_FLASH_IMAGE = "gemini-2.5-flash-image"  # Gemini 2.5 Flash Preview Image
    CHAT_2_5_FLASH_PREVIEW_09_2025 = "gemini-2.5-flash-preview-09-2025"  # Gemini 2.5 Flash Preview Sep 2025
    CHAT_2_5_FLASH_LITE_PREVIEW_09_2025 = (
        "gemini-2.5-flash-lite-preview-09-2025"  # Preview release (Septempber 25th, 2025) of Gemini 2.5 Flash-Lite
    )
    CHAT_3_PRO_PREVIEW = "gemini-3-pro-preview"  # Gemini 3 Pro Preview
    CHAT_3_PRO_IMAGE_PREVIEW = "gemini-3-pro-image-preview"  # Gemini 3 Pro Image Preview
    CHAT_NANO_BANANA_PRO_PREVIEW = "nano-banana-pro-preview"  # Gemini 3 Pro Image Preview
    CHAT_ROBOTICS_ER_1_5_PREVIEW = "gemini-robotics-er-1.5-preview"  # Gemini Robotics-ER 1.5 Preview
    CHAT_2_5_COMPUTER_USE_PREVIEW_10_2025 = (
        "gemini-2.5-computer-use-preview-10-2025"  # Gemini 2.5 Computer Use Preview 10-2025
    )
    CHAT_DEEP_RESEARCH_PRO_PREVIEW_12_2025 = (
        "deep-research-pro-preview-12-2025"  # Preview release (December 12th, 2025) of Deep Research Pro
    )
    AQA = "aqa"  # Model trained to return answers to questions that are grounded in provided sources, along with estimating answerable probability.
