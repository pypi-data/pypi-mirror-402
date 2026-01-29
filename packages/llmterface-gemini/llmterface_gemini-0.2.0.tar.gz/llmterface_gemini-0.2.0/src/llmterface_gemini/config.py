import typing as t

import llmterface as llm
from google.genai.types import GenerateContentConfig
from pydantic import Field, field_validator

from llmterface_gemini.models import GeminiTextModelType

AllowedGeminiModels = GeminiTextModelType


class GeminiConfig(llm.ProviderConfig):
    GENERIC_MODEL_MAPPING: t.ClassVar[dict[llm.GenericModelType, AllowedGeminiModels]] = {
        llm.GenericModelType.text_lite: GeminiTextModelType.CHAT_2_0_FLASH_LITE,
        llm.GenericModelType.text_standard: GeminiTextModelType.CHAT_2_0_FLASH,
        llm.GenericModelType.text_heavy: GeminiTextModelType.CHAT_2_5_PRO,
    }
    DEFAULT_MODEL: t.ClassVar[AllowedGeminiModels] = GeminiTextModelType.CHAT_2_0_FLASH
    PROVIDER: t.ClassVar[str] = "gemini"
    api_key: str = Field(..., description="API key for authenticating with the Gemini service.")
    model: GeminiTextModelType = Field(default=DEFAULT_MODEL, description="Gemini model to use for requests.")
    gen_content_config: GenerateContentConfig | None = Field(
        None,
        description="pre-configured GenerateContentConfig to use for requests.",
    )

    @classmethod
    def from_generic_config(
        cls,
        config: llm.GenericConfig,
    ) -> "GeminiConfig":
        gen_content_config = GenerateContentConfig(
            temperature=config.temperature,
            max_output_tokens=config.max_output_tokens,
            system_instruction=config.system_instruction,
            response_mime_type="application/json",
            response_json_schema=config.get_response_schema(),
        )
        return cls(
            api_key=config.api_key,
            model=config.model,
            gen_content_config=gen_content_config,
        )

    @field_validator("model", mode="before")
    @classmethod
    def validate_model(cls, v: AllowedGeminiModels | llm.GenericModelType | str | None) -> GeminiTextModelType | None:
        if v is None:
            return None
        if isinstance(v, AllowedGeminiModels):
            return v
        if isinstance(v, llm.GenericModelType):
            if model := cls.GENERIC_MODEL_MAPPING.get(v):
                return model
            raise NotImplementedError(f"No mapping for generic model type: {v}")
        try:
            return AllowedGeminiModels(v)
        except ValueError as e:
            raise ValueError(f"Invalid Gemini model type: {v}") from e
