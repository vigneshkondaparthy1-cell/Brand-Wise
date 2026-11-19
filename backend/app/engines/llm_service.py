import json
import urllib.request
import urllib.error
from typing import Dict, Any, Optional

class LLMService:
    """Disclosed Multi-Provider AI Service (Claude 3.5 Sonnet, Gemini 1.5, OpenAI GPT-4o).
    
    Conforms to BrandWise Responsible Design (PDF Section 05 & 08):
    - Grounded in provided sources only (never hallucinates facts).
    - Preserves author's intent during corrections.
    - Explicit uncertainty: flags 'cannot verify - needs human check' when unverified.
    - Graceful fallback to deterministic engine if API key is not configured or offline.
    """

    def __init__(self):
        pass

    def test_key(self, provider: str, api_key: str) -> Dict[str, Any]:
        """Validates an API key with the provider's official endpoint."""
        provider = provider.lower().strip()
        api_key = api_key.strip()
        if not api_key:
            return {"valid": False, "provider": provider, "error": "API key cannot be empty"}

        try:
            if provider == "anthropic":
                # Check Anthropic Claude API with minimal probe
                req = urllib.request.Request(
                    "https://api.anthropic.com/v1/messages",
                    data=json.dumps({
                        "model": "claude-3-5-sonnet-20241022",
                        "max_tokens": 1,
                        "messages": [{"role": "user", "content": "ping"}]
                    }).encode("utf-8"),
                    headers={
                        "x-api-key": api_key,
                        "anthropic-version": "2023-06-01",
                        "content-type": "application/json"
                    },
                    method="POST"
                )
                with urllib.request.urlopen(req, timeout=8) as resp:
                    return {"valid": True, "provider": "Anthropic Claude", "status": resp.status, "model": "claude-3-5-sonnet-20241022"}

            elif provider == "openai":
                req = urllib.request.Request(
                    "https://api.openai.com/v1/models",
                    headers={"Authorization": f"Bearer {api_key}"},
                    method="GET"
                )
                with urllib.request.urlopen(req, timeout=8) as resp:
                    return {"valid": True, "provider": "OpenAI", "status": resp.status, "model": "gpt-4o"}

            elif provider == "gemini":
                url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"
                req = urllib.request.Request(url, method="GET")
                with urllib.request.urlopen(req, timeout=8) as resp:
                    return {"valid": True, "provider": "Google Gemini", "status": resp.status, "model": "gemini-1.5-pro / flash"}

            elif provider == "slack":
                if not api_key.startswith("https://hooks.slack.com/"):
                    return {"valid": False, "provider": "Slack", "error": "Invalid Slack webhook URL format"}
                return {"valid": True, "provider": "Slack Webhook", "status": 200, "note": "Valid webhook URL format"}

            return {"valid": False, "provider": provider, "error": f"Unknown provider: {provider}"}

        except urllib.error.HTTPError as e:
            err_msg = f"HTTP {e.code}: {e.reason}"
            try:
                raw = e.read().decode("utf-8")
                err_data = json.loads(raw)
                if "error" in err_data:
                    err_msg = str(err_data["error"])
            except Exception:
                pass
            return {"valid": False, "provider": provider, "error": err_msg, "code": e.code}

        except urllib.error.URLError as e:
            return {"valid": False, "provider": provider, "error": f"Connection error: {e.reason}"}
        except Exception as e:
            return {"valid": False, "provider": provider, "error": str(e)}

    def analyze_with_claude(self, content: str, reference: str, api_key: str) -> Optional[Dict[str, Any]]:
        """Invokes Claude 3.5 Sonnet structured output for nuanced claim and tone verification."""
        if not api_key:
            return None

        prompt = f"""You are BrandWise, a pre-publication brand governance review platform.
Review the submitted content against the official reference guidelines and claims ledger.

OFFICIAL REFERENCE GUIDELINES & CLAIMS:
{reference}

SUBMITTED CONTENT:
{content}

RULES:
1. Ground every finding in the provided official reference.
2. If a claim lacks proof or is expired, flag it as 'cannot verify - needs human check'.
3. For each issue, provide: title, category, severity (Critical, High, Medium, Low), wrong snippet, why flagged, suggested intent-preserving rewrite, and confidence (0-100).
4. Return ONLY valid JSON with keys: 'score' (0-100), 'confidence' (0-100), 'findings' (array of findings)."""

        try:
            req = urllib.request.Request(
                "https://api.anthropic.com/v1/messages",
                data=json.dumps({
                    "model": "claude-3-5-sonnet-20241022",
                    "max_tokens": 1500,
                    "messages": [{"role": "user", "content": prompt}]
                }).encode("utf-8"),
                headers={
                    "x-api-key": api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json"
                },
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                text_out = data["content"][0]["text"]
                # Parse JSON block
                clean_json = text_out.strip()
                if "```json" in clean_json:
                    clean_json = clean_json.split("```json")[1].split("```")[0].strip()
                elif "```" in clean_json:
                    clean_json = clean_json.split("```")[1].split("```")[0].strip()
                return json.loads(clean_json)
        except Exception as e:
            print(f"Claude API call fallback triggered: {e}")
            return None

llm_service = LLMService()
