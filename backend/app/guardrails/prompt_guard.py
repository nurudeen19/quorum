
from __future__ import annotations
import os
from typing import Any
from app.config.settings import get_settings
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")

_pipeline: Any | None = None
_MAX_GUARD_MODEL_TOKENS = 512



def is_prompt_guard_loaded() -> bool:
    return _pipeline is not None



def setup_prompt_guard(settings=None) -> None:
    global _pipeline
    if _pipeline is not None:
        return
    s = settings or get_settings()
    if not s.enable_promtpt_guard:
        return
    token_secret = s.hf_token
    token = token_secret.get_secret_value() if token_secret else ""
    if not token.strip():
        raise RuntimeError("Prompt guard needs a Hugging Face token: set HF_TOKEN (or HUGGING_FACE_HUB_TOKEN)")
    from transformers import pipeline
    _pipeline = pipeline(
        task="text-classification",
        model=s.model_id,
        truncation=True,
        max_length=_MAX_GUARD_MODEL_TOKENS,
        device=s.device,
        token=token,
    )
    _pipeline("ok", truncation=True, max_length=_MAX_GUARD_MODEL_TOKENS)



def teardown_prompt_guard() -> None:
    global _pipeline
    _pipeline = None



def _malicious_class_index(model: Any) -> int:
    id2label = getattr(getattr(model, "config", None), "id2label", None)
    if isinstance(id2label, dict):
        for k, v in id2label.items():
            if "MALICIOUS" in str(v).upper():
                try:
                    return int(k)
                except Exception:
                    pass
    return 1



def _softmax_malicious_probability(text: str) -> float:
    import torch
    from torch.nn.functional import softmax
    pipe = _pipeline
    if pipe is None:
        raise RuntimeError("prompt_guard pipeline is not loaded")
    model = pipe.model
    tokenizer = pipe.tokenizer
    device = next(model.parameters()).device
    inputs = tokenizer(text, return_tensors="pt", padding=True, truncation=True, max_length=_MAX_GUARD_MODEL_TOKENS)
    inputs = {k: v.to(device) for k, v in inputs.items()}
    with torch.no_grad():
        logits = model(**inputs).logits
    probs = softmax(logits, dim=-1)
    idx = _malicious_class_index(model)
    if idx < 0 or idx >= probs.shape[-1]:
        return 1.0
    return float(probs[0, idx].item())



def classify_prompt(text: str, settings=None, *, malicious_threshold: float | None = None) -> tuple[bool, str | None]:
    s = settings or get_settings()
    if not s.enable_promtpt_guard:
        return True, None
    if _pipeline is None:
        return True, None
    threshold = float(malicious_threshold) if malicious_threshold is not None else float(s.malicious_probability_threshold)
    try:
        p_mal = _softmax_malicious_probability(text)
    except Exception as exc:
        return False, f"Prompt guard failed: {exc}"
    if p_mal >= threshold:
        return (
            False,
            "This message was blocked by automated prompt safety checks. Please ask a normal career question without instructions aimed at overriding the assistant.",
        )
    return True, None
