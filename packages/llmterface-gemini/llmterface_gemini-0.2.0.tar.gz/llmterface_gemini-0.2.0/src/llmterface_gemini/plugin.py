from llmterface.providers.provider_spec import ProviderSpec

from llmterface_gemini.chat import GeminiChat
from llmterface_gemini.config import GeminiConfig

PROVIDER = ProviderSpec(
    provider=GeminiConfig.PROVIDER,
    config_cls=GeminiConfig,
    chat_cls=GeminiChat,
)
