from sqlalchemy.orm import Session
from app.models import FallbackLog
COMPANY_MAP = {
    "openai": ["OpenAI", "OpenAI Blog"],
    "google": ["Google", "Google DeepMind", "Google Cloud", "Google Research"],
    "anthropic": ["Anthropic"],
    "microsoft": ["Microsoft", "Microsoft Research", "Azure"],
    "nvidia": ["NVIDIA", "Nvidia"],
    "meta": ["Meta", "Meta AI", "Facebook"],
    "mistral": ["Mistral AI"],
    "huggingface": ["Hugging Face"],
    "apple": ["Apple"],
}

# Reverse lookup — "Google DeepMind" -> "google"
SOURCE_TO_SLUG = {}
for slug, sources in COMPANY_MAP.items():
    for source in sources:
        SOURCE_TO_SLUG[source] = slug


def get_company_slug(source: str, db: Session | None = None, news_run_id: int | None = None) -> str | None:
    slug = SOURCE_TO_SLUG.get(source, None)

    if slug is None and db is not None:
        
        db.add(FallbackLog(
            fallback_type="unmapped_company_source",
            entity_type="story",
            entity_id=None,
            detail=f"Source '{source}' did not match any known company mapping",
            news_run_id=news_run_id,
        ))

    return slug