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

def get_company_slug(source: str) -> str | None:
    return SOURCE_TO_SLUG.get(source, None)