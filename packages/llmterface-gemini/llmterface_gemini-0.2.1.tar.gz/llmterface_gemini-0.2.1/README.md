# LLMterface
**LLMterface is under active development. APIs may change and the README may lag slightly behind implementation.**
**Until v1.0, minor releases may introduce breaking changes.**

---

A small, opinionated, provider-agnostic interface for working with LLMs in Python.

LLMterface focuses on one **thing**: submitting prompts to AI providers and getting back structured, validated responses.

No agents.
No chains.
No workflows.
No hidden control flow.

If you want a thin abstraction layer you can understand in one sitting, this is for you.

## Why LLMterface?

LLMterface exists to solve a narrow problem: sending prompts to LLMs and getting validated responses while avoiding vendor lock-in and minimizing complexity.

It intentionally avoids orchestration, memory, agents, and workflow abstractions so those concerns remain explicit and application-owned. This makes LLMterface easy to reason about, debug, and integrate alongside other tools rather than replacing them.

## Goals

- **Minimal**: A small, readable interface with very few moving parts.
- **Generic**: Universal configuration primitives that map cleanly to provider defaults, with optional provider-specific overrides.
- **Unobtrusive**: Designed to coexist with other LLM libraries without forcing architectural decisions.
- **Extensible**: Providers can be added via entry points without modifying core code.

## Non-Goals
If you want any of the following, build them on top of LLMterface or use a different library:

- Agent orchestration
- Tool calling frameworks
- Prompt chains or workflow systems
- Long-term memory systems

---

## Installation

```bash
pip install llmterface
```

## Provider Specific installation

```bash
pip install llmterface[gemini]
pip install llmterface[openai]  # TODO
pip install llmterface[openai,anthropic]  # TODO
# or to install all currently supported providers
pip install llmterface[all]
```

## Basic Usage

```python
import llmterface as llm

handler = llm.LLMterface(
    config=llm.GenericConfig(
        api_key="<YOUR GEMINI API KEY>",
        provider="gemini",
    )
)
res = handler.ask(
    "how many LLMs does it take to screw in a lightbulb? Explain your reasoning."
)
print(res)
# -> “Depends. One to do it, five to argue about alignment, and twelve to hallucinate that the room is already bright.”
```
## Basic Configuration
configuration of the handler is done through the `GenericConfig` class
which can be supplied at three levels:

1. Handler
2. Chat
3. Question

Overrides apply in that order, with the most specific configuration winning.

```python
import llmterface as llm
import llmterface_gemini as gemini
from functools import partial

gemini_config = partial(
    llm.GenericConfig,
    provider=gemini.GeminiConfig.PROVIDER,
    api_key="<YOUR GEMINI API KEY>",
)
handler_config = gemini_config(response_model=int)
chat_config = gemini_config(response_model=float)
handler = llm.LLMterface(config=handler_config)
chat_id = handler.create_chat(chat_config.provider, config=chat_config)

Q = "What is the airspeed velocity of an unladen swallow?"
question = llm.Question(
    question=Q,
    config=gemini_config() # response_model defaults to str
)
int_res = handler.ask(Q)
print(int_res, type(int_res))
# 42 <class 'int'>

float_res = handler.ask(Q, chat_id=chat_id)
print(float_res, type(float_res))
# 42.0 <class 'float'>

str_res = handler.ask(question, chat_id=chat_id)
print(str_res, type(str_res))
# african or european swallow? <class 'str'>
```
## Provider-specific overrides

If you need access to vendor-specific features, you can supply provider overrides explicitly.
```python
import llmterface as llm
import llmterface_gemini as gemini

gemini_override = gemini.GeminiConfig(
    api_key="<YOUR GEMINI API KEY>",
    model=gemini.GeminiTextModelType.CHAT_2_0_FLASH_LITE,
)

config = llm.GenericConfig(
    provider=gemini.GeminiConfig.PROVIDER,
    provider_overrides={
        gemini.GeminiConfig.PROVIDER: gemini_override
    },
)

handler = llm.LLMterface(config=config)

res = handler.ask("How many LLMs does it take to screw in a lightbulb?")
print(res)
# -> 6
```

## Structured Responses

LLMterface is designed to work naturally with Pydantic models.
```python
from pydantic import BaseModel, Field
import llmterface as llm

class WeatherResponse(BaseModel):
    temperature_c: float = Field(..., description="Temperature in Celsius")
    condition: str = Field(
        ..., description="Weather described in a silly way"
    )

question = llm.Question(
    question="What is the current weather in Paris?",
    config=llm.GenericConfig(
        api_key="<YOUR GEMINI API KEY>",
        provider="gemini",
        response_model=WeatherResponse,
    ),
)

res = llm.LLMterface().ask(question)

assert isinstance(res, WeatherResponse)
print(res.temperature_c)
# -> 12.0
print(res.condition)
# -> 'Sunny with a chance of croissants'
```

## Key Objects

LLMterface is built around a small set of core objects.

---

### `Question[TRes: AllowedResponseTypes](BaseModel):`

A `Question` represents a **single prompt submission** to an LLM, along with optional configuration, retry behavior, and response typing.

At its simplest, a `Question` is just text:

```python
import llmterface as llm
question = llm.Question(
    question="What is the answer to life, the universe, and everything?"
)
```
But `Question` is also **generic over the expected response type**:
```python
import llmterface as llm
question = llm.Question[llm.simple_answers.SimpleInteger](
    question="What is 6 * 7?",
    config=llm.GenericConfig(
        provider="gemini",
        api_key="<YOUR GEMINI API KEY>",
        response_model=int)
)
```
This allows LLMterface to validate and return structured responses automatically.

---

#### Prompt normalization

Before submission, the question text is normalized via `get_question()`:
- Dedented
- Stripped of leading/trailing whitespace

This makes multiline prompts predictable and easy to format.
You can override this behavior by subclassing `Question`.

---

#### Retry behavior

`Question` defines how retries are handled, not the client.

Retries occur when:

- The provider errors

- The response fails schema validation

The `on_retry()` method can be overridden to implement custom retry behavior, including modifying the prompt, incorporating the previous response, or stopping retries entirely.

By default, schema validation failures cause the prompt to be augmented with a strict formatting reminder and the previous response content.

---

### `GenericConfig[TRes: AllowedResponseTypes = str](BaseModel)`

`GenericConfig` is the provider-agnostic configuration model used throughout LLMterface.

It defines a **common set of fields** that map cleanly onto most LLM providers. The goal is that your application code can stay stable even if you switch providers, because you configure *intent* (model tier, temperature, response model), not vendor-specific knobs.

If a field is not supported by a given provider, it is simply ignored by that provider integration.

If vendor-specific configuration is required, it can be supplied via `provider_overrides`.


---

#### Example

```python
import llmterface as llm
import llmterface_gemini as gemini

config = llm.GenericConfig(
    provider="gemini",
    api_key="<YOUR API KEY>",
    model=llm.GenericModelType.text_lite,
    temperature=0.2,
    response_model=float,
    provider_overrides={
        "gemini": gemini.GeminiConfig(
            api_key="<YOUR GEMINI API KEY>",
            # provider-specific fields here
        )
    },
)
```

---

#### Override behavior

Configurations in LLMterface are **not merged field-by-field.**

When one configuration takes precedence over another, it **fully replaces** the lower-precedence configuration at that level.

For example:
- A question-level config completely overrides a chat-level config
- A chat-level config completely overrides a handler-level config

This keeps configuration resolution simple, explicit, and predictable.

---

#### Provider-specific configs

Vendor-specific configuration objects inherit from:

```python
llmterface.providers.provider_config.ProviderConfig
```

Provider configs may expose additional fields beyond `GenericConfig`. These are only interpreted by the corresponding provider integration and are ignored elsewhere.

This design allows provider integrations to evolve independently without leaking provider-specific concerns into application code.