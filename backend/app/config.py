import os
from pathlib import Path
from typing import Dict, Optional, Any

BACKEND_ROOT = Path(__file__).resolve().parent.parent
WORKSPACE_ROOT = BACKEND_ROOT.parent
DATA_DIR = WORKSPACE_ROOT
ENV_FILE = WORKSPACE_ROOT / ".env"

def load_env_file():
    """Loads key-value pairs from .env into os.environ if not already set."""
    if ENV_FILE.exists():
        try:
            for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, val = line.split("=", 1)
                    key = key.strip()
                    val = val.strip().strip('"').strip("'")
                    if key and not os.environ.get(key):
                        os.environ[key] = val
        except Exception:
            pass

load_env_file()

class Settings:
    APP_NAME: str = "BrandWise"
    APP_TITLE: str = "BrandWise Brand Governance Platform"
    VERSION: str = "2.4.0"
    PREPARED_BY: str = "The Final Draft"
    HOST: str = "127.0.0.1"
    PORT: int = 8765

    # Storage paths
    AUDITS_FILE: Path = DATA_DIR / "audit-data.json"
    CLAIMS_FILE: Path = DATA_DIR / "claims-data.json"
    GUIDELINES_FILE: Path = DATA_DIR / "guidelines-data.json"
    FRONTEND_FILE: Path = WORKSPACE_ROOT / "The-Final-Draft-Hackathon-Updated.html"
    ENV_FILE_PATH: Path = ENV_FILE

    # Disclosed AI Services & Models (PDF Page 8 & 10)
    DISCLOSED_MODELS: dict = {
        "reasoning": "Claude 3.5 Sonnet (Structured Reasoning & Claim Verification)",
        "vision": "Multimodal Vision Model (Visual & Logo Verification)",
        "rules": "Deterministic WCAG 2.1 & Terminology Engine (Exact Math & Regex)",
        "uncertaintyEngine": "Active (Flag: 'Cannot verify - needs human check' on expired/missing proof)"
    }

    ZERO_DATA_RETENTION_TRAINING: bool = True
    TENANT_ISOLATION_ENABLED: bool = True

    # API Keys
    @property
    def anthropic_api_key(self) -> str:
        return os.environ.get("ANTHROPIC_API_KEY", "").strip()

    @property
    def gemini_api_key(self) -> str:
        return os.environ.get("GEMINI_API_KEY", "").strip()

    @property
    def openai_api_key(self) -> str:
        return os.environ.get("OPENAI_API_KEY", "").strip()

    @property
    def slack_webhook_url(self) -> str:
        return os.environ.get("SLACK_WEBHOOK_URL", "").strip()

    def get_masked_keys(self) -> Dict[str, Dict[str, Any]]:
        def mask(key_val: str, prefix_len=7, suffix_len=4):
            if not key_val:
                return {"configured": False, "masked": "Not configured"}
            if len(key_val) <= prefix_len + suffix_len:
                return {"configured": True, "masked": "••••••••"}
            return {
                "configured": True,
                "masked": f"{key_val[:prefix_len]}...{key_val[-suffix_len:]}"
            }

        return {
            "anthropic": {
                **mask(self.anthropic_api_key, 7, 4),
                "service": "Claude 3.5 Sonnet",
                "role": "Deep Claim Reasoning & Tone Analysis"
            },
            "gemini": {
                **mask(self.gemini_api_key, 6, 4),
                "service": "Google Gemini 1.5 Pro / Flash",
                "role": "Multimodal Vision & Document Ingestion"
            },
            "openai": {
                **mask(self.openai_api_key, 7, 4),
                "service": "OpenAI GPT-4o",
                "role": "Structured JSON & Format Normalization"
            },
            "slack": {
                **mask(self.slack_webhook_url, 12, 5),
                "service": "Slack Incoming Webhook",
                "role": "#brand-governance-alerts Channel Notifications"
            }
        }

    def save_keys(self, new_keys: Dict[str, str]) -> bool:
        """Saves keys to .env and updates current process environment."""
        for k, v in new_keys.items():
            if v is not None and v != "••••••••":
                os.environ[k] = v.strip()

        # Write to .env file
        try:
            lines = [
                "# BrandWise Platform Configuration & API Keys",
                "# Grounded, explainable and human-controlled brand governance",
                f"ANTHROPIC_API_KEY={self.anthropic_api_key}",
                f"GEMINI_API_KEY={self.gemini_api_key}",
                f"OPENAI_API_KEY={self.openai_api_key}",
                f"SLACK_WEBHOOK_URL={self.slack_webhook_url}",
                "BRANDWISE_PORT=8765",
                "BRANDWISE_ENV=production"
            ]
            ENV_FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")
            return True
        except Exception as e:
            print(f"Error saving .env: {e}")
            return False

settings = Settings()
