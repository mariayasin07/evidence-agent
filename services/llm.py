"""Single provider interface used by every agent (Ollama or Cloud API)."""
import requests

from utils.config import PRESETS


class LLMError(Exception):
    pass


class LLMProvider:
    def __init__(self, cfg, api_key=""):
        self.cfg = cfg
        self.api_key = (api_key or "").strip()
        self.is_ollama = cfg["provider"] == "Ollama"
        self.timeout = int(cfg.get("llm_timeout", 120))
        self._cache = {}

    # ---- basics
    @property
    def model(self):
        return self.cfg["ollama_model"] if self.is_ollama else self.cfg["cloud_model"]

    @property
    def label(self):
        name = "Ollama" if self.is_ollama else self.cfg["cloud_provider"]
        return f"{name} · {self.model or 'no model'}"

    def _anthropic(self):
        return (not self.is_ollama) and self.cfg["cloud_provider"] == "Anthropic"

    def _base(self):
        if self.is_ollama:
            return self.cfg["ollama_host"].rstrip("/")
        b = PRESETS.get(self.cfg["cloud_provider"], "") or self.cfg.get("cloud_base_url", "")
        return b.rstrip("/")

    def _headers(self):
        if self._anthropic():
            return {"x-api-key": self.api_key, "anthropic-version": "2023-06-01", "content-type": "application/json"}
        return {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}

    def ready(self):
        if not self._base():
            return False, "Set the host / base URL in Settings → AI / Model."
        if not self.model:
            return False, "Select a model in Settings → AI / Model."
        if not self.is_ollama and not self.api_key:
            return False, "Add your API key in Settings → AI / Model (or LLM_API_KEY in .env)."
        return True, ""

    # ---- discovery / connection
    def list_models(self, timeout=8):
        try:
            if self.is_ollama:
                r = requests.get(self._base() + "/api/tags", timeout=timeout)
                r.raise_for_status()
                return sorted({m.get("name") or m.get("model") for m in r.json().get("models", []) if m.get("name") or m.get("model")})
            r = requests.get(self._base() + "/models", headers=self._headers(), timeout=timeout)
            r.raise_for_status()
            ids = [m.get("id") or m.get("name") for m in r.json().get("data", [])]
            return sorted({i.replace("models/", "") for i in ids if i})
        except requests.RequestException as e:
            raise LLMError(f"Could not reach {self._base() or 'provider'}: {e}")
        except ValueError:
            raise LLMError("Provider returned an unexpected response while listing models.")

    def check(self):
        try:
            models = self.list_models()
            return True, f"Connected — {len(models)} model(s) available.", models
        except LLMError as e:
            return False, str(e), []

    # ---- generation
    def chat(self, system, user, json_mode=False, max_tokens=3000, timeout=None):
        to = int(timeout or self.timeout)
        key = (system, user, json_mode)
        if key in self._cache:
            return self._cache[key]
        if json_mode:
            system += "\nRespond with a single valid JSON object only. No markdown fences, no commentary."
        try:
            if self.is_ollama:
                out = self._ollama(system, user, json_mode, max_tokens, to)
            elif self._anthropic():
                out = self._claude(system, user, max_tokens, to)
            else:
                out = self._openai(system, user, json_mode, max_tokens, to)
        except requests.Timeout:
            raise LLMError(f"Model call timed out after {to}s.")
        except requests.RequestException as e:
            raise LLMError(f"Model call failed: {e}")
        self._cache[key] = out
        return out

    def _ollama(self, system, user, json_mode, max_tokens, to):
        body = {
            "model": self.model,
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
            "stream": False,
            "options": {"temperature": 0.2, "num_ctx": 4096, "num_predict": int(max_tokens)},
        }
        if json_mode:
            body["format"] = "json"
        r = requests.post(self._base() + "/api/chat", json=body, timeout=to)
        if r.status_code >= 400:
            raise LLMError(f"Ollama error {r.status_code}: {r.text[:200]}")
        return r.json().get("message", {}).get("content", "")

    def _openai(self, system, user, json_mode, max_tokens, to):
        body = {
            "model": self.model,
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
            "temperature": 0.2,
        }
        if json_mode:
            body["response_format"] = {"type": "json_object"}
        r = requests.post(self._base() + "/chat/completions", headers=self._headers(), json=body, timeout=to)
        if r.status_code == 400 and json_mode:
            body.pop("response_format", None)
            r = requests.post(self._base() + "/chat/completions", headers=self._headers(), json=body, timeout=to)
        if r.status_code >= 400:
            raise LLMError(f"API error {r.status_code}: {r.text[:200]}")
        return r.json()["choices"][0]["message"]["content"] or ""

    def _claude(self, system, user, max_tokens, to):
        body = {"model": self.model, "max_tokens": max_tokens, "system": system, "messages": [{"role": "user", "content": user}], "temperature": 0.2}
        r = requests.post(self._base() + "/messages", headers=self._headers(), json=body, timeout=to)
        if r.status_code >= 400:
            raise LLMError(f"API error {r.status_code}: {r.text[:200]}")
        return "".join(b.get("text", "") for b in r.json().get("content", []) if b.get("type") == "text")
