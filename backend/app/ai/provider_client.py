"""Unified AI provider client supporting multiple providers via platform settings."""

import json
import logging
import os
from typing import Optional

logger = logging.getLogger(__name__)

OPENAI_AVAILABLE = False
try:
    from openai import OpenAI as OpenAI_Client, AzureOpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OpenAI_Client = None
    AzureOpenAI = None

EMBEDDING_MODEL_PATTERNS = [
    "embed", "embedding", "nomic", "e5-", "bge-", "gte-",
    "jina-embed", "mxbai-embed", "snowflake-arctic-embed",
    "minilm", "all-mpnet", "all-minilm", "text-embedding",
    "voyage-", "cohere-embed", "stella_en", "dpr-",
    "nemotron-3-embed", "nemotron-4-embed",
]


def is_embedding_model(model: str) -> bool:
    """Check if a model is an embedding model (not usable for chat)."""
    model_lower = model.lower()
    return any(pattern in model_lower for pattern in EMBEDDING_MODEL_PATTERNS)

ANTHROPIC_AVAILABLE = False
try:
    import anthropic as anthropic_sdk
    ANTHROPIC_AVAILABLE = True
except ImportError:
    anthropic_sdk = None

GOOGLE_AVAILABLE = False
try:
    import google.generativeai as genai
    GOOGLE_AVAILABLE = True
except ImportError:
    genai = None


SUPPORTED_PROVIDERS = {
    "openai": {"name": "OpenAI", "env_key": "OPENAI_API_KEY"},
    "groq": {"name": "Groq", "env_key": "GROQ_API_KEY"},
    "openrouter": {"name": "OpenRouter", "env_key": "OPENROUTER_API_KEY"},
    "minimax": {"name": "MiniMax", "env_key": "MINIMAX_API_KEY"},
    "anthropic": {"name": "Anthropic", "env_key": "ANTHROPIC_API_KEY"},
    "azure": {"name": "Azure OpenAI", "env_key": "AZURE_OPENAI_KEY"},
    "google": {"name": "Google AI", "env_key": "GOOGLE_API_KEY"},
    "freetokenfaucet": {"name": "FreeTokenFaucet", "env_key": "FREETOKENFAUCET_API_KEY"},
    "nvidia": {"name": "NVIDIA", "env_key": "NVIDIA_API_KEY"},
}


def load_providers_config(db) -> dict:
    """Load ai_providers_config from PlatformSetting table."""
    from app.models import PlatformSetting
    setting = db.query(PlatformSetting).filter(
        PlatformSetting.key == "ai_providers_config",
        PlatformSetting.value.isnot(None),
        PlatformSetting.value != "",
    ).first()
    if setting and setting.value:
        try:
            return json.loads(setting.value)
        except (json.JSONDecodeError, TypeError):
            logger.warning("Failed to parse ai_providers_config JSON")
    return {}


def get_enabled_provider(db) -> tuple[Optional[str], Optional[dict]]:
    """Return (provider_id, provider_config) for the first enabled provider."""
    config = load_providers_config(db)
    for provider_id in ["freetokenfaucet", "nvidia", "openai", "groq", "openrouter", "minimax", "anthropic", "azure", "google"]:
        provider = config.get(provider_id, {})
        if provider.get("enabled") and provider.get("key"):
            return provider_id, provider
    return None, None


def generate_chat(
    db,
    messages: list,
    model: Optional[str] = None,
    temperature: float = 0.7,
    max_tokens: int = 4000,
) -> str:
    """Call the first enabled AI provider with the given messages.

    Falls back to OPENAI_API_KEY env var if no provider is configured in DB.
    Returns the response text.
    """
    provider_id, provider_config = get_enabled_provider(db)

    if not provider_id:
        raise RuntimeError(
            "Aucun fournisseur IA configuré. "
            "Configurez un fournisseur dans Paramètres → Fournisseurs IA."
        )

    model = model or provider_config.get("model", "gpt-4o-mini")
    api_key = provider_config.get("key", "")
    extra_config = provider_config.get("extra", {})

    if is_embedding_model(model):
        raise RuntimeError(
            f"Le modèle '{model}' est un modèle d'embedding, pas un modèle de chat. "
            f"Configurez un modèle de chat dans les paramètres du fournisseur."
        )

    try:
        if provider_id == "freetokenfaucet":
            base_url = extra_config.get("base_url", "https://freetokenfaucet.com/v1")
            return _call_openai_compatible(
                api_key, model, messages, temperature, max_tokens,
                base_url=base_url,
            )

        elif provider_id == "nvidia":
            base_url = extra_config.get("base_url", "https://integrate.api.nvidia.com/v1")
            return _call_openai_compatible(
                api_key, model, messages, temperature, max_tokens,
                base_url=base_url,
            )

        elif provider_id == "openai":
            return _call_openai_compatible(api_key, model, messages, temperature, max_tokens)

        elif provider_id == "groq":
            return _call_openai_compatible(
                api_key, model, messages, temperature, max_tokens,
                base_url="https://api.groq.com/openai/v1",
            )

        elif provider_id == "openrouter":
            return _call_openai_compatible(
                api_key, model, messages, temperature, max_tokens,
                base_url="https://openrouter.ai/api/v1",
            )

        elif provider_id == "minimax":
            base_url = extra_config.get("base_url", os.environ.get("MINIMAX_BASE_URL", "https://inference.dahl.global/v1"))
            return _call_openai_compatible(
                api_key, model, messages, temperature, max_tokens,
                base_url=base_url,
            )

        elif provider_id == "azure":
            endpoint = extra_config.get("endpoint", os.environ.get("AZURE_OPENAI_ENDPOINT", ""))
            return _call_azure_openai(api_key, endpoint, model, messages, temperature, max_tokens)

        elif provider_id == "anthropic":
            return _call_anthropic(api_key, model, messages, temperature, max_tokens)

        elif provider_id == "google":
            return _call_google(api_key, model, messages, temperature, max_tokens)

        else:
            raise ValueError(f"Fournisseur IA non supporté: {provider_id}")

    except Exception as e:
        logger.error(f"Provider {provider_id} error: {e}")
        raise


def generate_chat_stream(
    db,
    messages: list,
    model: Optional[str] = None,
    temperature: float = 0.7,
    max_tokens: int = 4000,
):
    """Yield streaming chunks from the first enabled AI provider.

    Yields tuples of (chunk_text, None) or (None, error_str).
    """
    provider_id, provider_config = get_enabled_provider(db)
    if not provider_id:
        api_key = os.environ.get("OPENAI_API_KEY", "")
        if not api_key:
            yield None, "Aucun fournisseur IA configuré."
            return
        provider_id = "openai"
        provider_config = {"key": api_key, "model": "gpt-4o-mini"}

    model = model or provider_config.get("model", "gpt-4o-mini")
    api_key = provider_config.get("key", "")
    extra_config = provider_config.get("extra", {})

    try:
        base_url = None
        if provider_id == "freetokenfaucet":
            base_url = extra_config.get("base_url", "https://freetokenfaucet.com/v1")
        elif provider_id == "nvidia":
            base_url = extra_config.get("base_url", "https://integrate.api.nvidia.com/v1")
        elif provider_id == "groq":
            base_url = "https://api.groq.com/openai/v1"
        elif provider_id == "openrouter":
            base_url = "https://openrouter.ai/api/v1"
        elif provider_id == "minimax":
            base_url = extra_config.get("base_url", os.environ.get("MINIMAX_BASE_URL", "https://inference.dahl.global/v1"))
        elif provider_id == "azure":
            base_url = extra_config.get("endpoint", os.environ.get("AZURE_OPENAI_ENDPOINT", ""))

        if provider_id in ("openai", "groq", "openrouter", "minimax", "azure", "freetokenfaucet", "nvidia"):
            client_kwargs = {"api_key": api_key, "timeout": 60.0}
            if base_url:
                client_kwargs["base_url"] = base_url
            client = OpenAI_Client(**client_kwargs)
            stream = client.chat.completions.create(
                model=model, messages=messages,
                temperature=temperature, max_tokens=max_tokens, stream=True,
            )
            for chunk in stream:
                delta = chunk.choices[0].delta if chunk.choices else None
                if delta and delta.content:
                    yield delta.content, None
            return

        elif provider_id == "anthropic":
            if not ANTHROPIC_AVAILABLE:
                yield None, "anthropic SDK n'est pas installé"
                return
            client = anthropic_sdk.Anthropic(api_key=api_key, timeout=60.0)
            system_msg = ""
            user_msgs = []
            for m in messages:
                if m["role"] == "system":
                    system_msg = m["content"]
                else:
                    user_msgs.append(m["content"])
            with client.messages.stream(
                model=model, max_tokens=max_tokens, temperature=temperature,
                system=system_msg, messages=[{"role": "user", "content": "\n".join(user_msgs)}],
            ) as stream:
                for text in stream.text_stream:
                    yield text, None
            return

        elif provider_id == "google":
            if not GOOGLE_AVAILABLE:
                yield None, "google-generativeai SDK n'est pas installé"
                return
            genai.configure(api_key=api_key)
            model_obj = genai.GenerativeModel(model)
            prompt = "\n".join(m["content"] for m in messages)
            response = model_obj.generate_content(prompt, stream=True)
            for chunk in response:
                if chunk.text:
                    yield chunk.text, None
            return

        else:
            yield None, f"Fournisseur IA non supporté: {provider_id}"

    except Exception as e:
        logger.error(f"Stream provider {provider_id} error: {e}")
        yield None, str(e)


def _call_openai_compatible(
    api_key: str,
    model: str,
    messages: list,
    temperature: float,
    max_tokens: int,
    base_url: Optional[str] = None,
) -> str:
    if not OPENAI_AVAILABLE:
        raise RuntimeError("OpenAI SDK (openai) n'est pas installé")
    kwargs = {"api_key": api_key, "timeout": 180.0}
    if base_url:
        kwargs["base_url"] = base_url
    client = OpenAI_Client(**kwargs)
    response = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
    )
    return response.choices[0].message.content or ""


def _call_azure_openai(
    api_key: str,
    endpoint: str,
    model: str,
    messages: list,
    temperature: float,
    max_tokens: int,
) -> str:
    if not OPENAI_AVAILABLE or AzureOpenAI is None:
        raise RuntimeError("AzureOpenAI n'est pas disponible")
    client = AzureOpenAI(api_key=api_key, azure_endpoint=endpoint, api_version="2024-02-01")
    response = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
    )
    return response.choices[0].message.content or ""


def _call_anthropic(
    api_key: str,
    model: str,
    messages: list,
    temperature: float,
    max_tokens: int,
) -> str:
    if not ANTHROPIC_AVAILABLE:
        raise RuntimeError("Anthropic SDK (anthropic) n'est pas installé")
    client = anthropic_sdk.Anthropic(api_key=api_key, timeout=60.0)
    # Convert OpenAI-style messages to Anthropic format
    system_msg = None
    anthropic_messages = []
    for msg in messages:
        if msg.get("role") == "system":
            system_msg = msg["content"]
        else:
            anthropic_messages.append({
                "role": "user" if msg.get("role") in ("user", "assistant") else msg["role"],
                "content": msg["content"],
            })
    kwargs = {
        "model": model,
        "max_tokens": max_tokens,
        "temperature": temperature,
        "messages": anthropic_messages,
    }
    if system_msg:
        kwargs["system"] = system_msg
    response = client.messages.create(**kwargs)
    return response.content[0].text if response.content else ""


def _call_google(
    api_key: str,
    model: str,
    messages: list,
    temperature: float,
    max_tokens: int,
) -> str:
    if not GOOGLE_AVAILABLE:
        raise RuntimeError("Google AI SDK (google-generativeai) n'est pas installé")
    genai.configure(api_key=api_key)
    client = genai.GenerativeModel(model_name=model)
    # Convert OpenAI-style messages to Google format
    prompt = ""
    for msg in messages:
        role = msg.get("role", "user")
        content = msg.get("content", "")
        prompt += f"{role}: {content}\n"
    response = client.generate_content(
        prompt,
        generation_config=genai.types.GenerationConfig(
            temperature=temperature,
            max_output_tokens=max_tokens,
        ),
    )
    return response.text or ""


def test_connection(provider_id: str, config: dict) -> str:
    """Test connection to a specific provider. Returns 'ok' or raises."""
    api_key = config.get("key", "")
    model = config.get("model", "gpt-4o-mini")
    messages = [{"role": "user", "content": "Réponds uniquement 'ok'."}]

    if is_embedding_model(model):
        raise RuntimeError(
            f"Le modèle '{model}' est un modèle d'embedding, pas un modèle de chat. "
            f"Utilisez un modèle de chat comme: google/gemma-3-1b-it:free, "
            f"meta-llama/llama-4-scout:free, mistralai/mistral-small-3.2-24b:free, "
            f"ou deepseek/deepseek-chat-v3-0324:free"
        )

    try:
        if provider_id == "freetokenfaucet":
            base_url = config.get("extra", {}).get("base_url", "https://freetokenfaucet.com/v1")
            _call_openai_compatible(api_key, model, messages, 0.5, 10,
                                    base_url=base_url)
        elif provider_id == "nvidia":
            base_url = config.get("extra", {}).get("base_url", "https://integrate.api.nvidia.com/v1")
            _call_openai_compatible(api_key, model, messages, 0.5, 10,
                                    base_url=base_url)
        elif provider_id == "openai":
            _call_openai_compatible(api_key, model, messages, 0.5, 10)
        elif provider_id == "groq":
            _call_openai_compatible(api_key, model, messages, 0.5, 10,
                                    base_url="https://api.groq.com/openai/v1")
        elif provider_id == "openrouter":
            _call_openai_compatible(api_key, model, messages, 0.5, 10,
                                    base_url="https://openrouter.ai/api/v1")
        elif provider_id == "minimax":
            base_url = config.get("extra", {}).get("base_url", os.environ.get("MINIMAX_BASE_URL", "https://inference.dahl.global/v1"))
            _call_openai_compatible(api_key, model, messages, 0.5, 10,
                                    base_url=base_url)
        elif provider_id == "azure":
            endpoint = config.get("extra", {}).get("endpoint", "")
            _call_azure_openai(api_key, endpoint, model, messages, 0.5, 10)
        elif provider_id == "anthropic":
            _call_anthropic(api_key, model, messages, 0.5, 10)
        elif provider_id == "google":
            _call_google(api_key, model, messages, 0.5, 10)
        else:
            return f"Fournisseur non supporté: {provider_id}"
        return "ok"
    except Exception as e:
        raise RuntimeError(f"Échec de connexion à {provider_id}: {e}")
