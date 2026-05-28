from pydantic_settings import BaseSettings
from dotenv import load_dotenv
from pathlib import Path

env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)


class Settings(BaseSettings):
    deepseek_api_key: str
    deepseek_base_url: str = "https://api.deepseek.com"
    deepseek_model_name: str = "deepseek-chat"
    deepseek_temperature: float = 0.7
    deepseek_reasoning_effort: str = "medium"
    tavily_api_key: str
    tavily_max_results: int = 8
    tavily_search_depth: str = "basic"
    tavily_include_images: bool = False
    tavily_include_image_descriptions: bool = False
    tavily_include_favicon: bool = False
    tavily_include_usage: bool = False
    cache_expire: str = "24h"
    sim_threshold: float = 0.75
    rate_limit_per_minute: int = 30
    rate_limit_search_per_minute: int = 10
    enable_injection_detection: bool = True
    injection_block_threshold: float = 0.85


settings = Settings()
