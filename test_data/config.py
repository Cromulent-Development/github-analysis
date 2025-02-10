"""Configuration for test PR processing."""

# Database settings
DB_URL = "postgresql+asyncpg://user:pass@localhost/dbname"

# OpenAI settings
OPENAI_API_KEY = "your-openai-key"  # Replace with actual key

# Qdrant settings
QDRANT_HOST = "localhost"
QDRANT_PORT = 6333

# Collection settings
COLLECTION_NAME = "github_changes"
VECTOR_SIZE = 1536  # Size for text-embedding-3-small model
