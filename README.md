# GitHub PR Analysis

A tool for analyzing GitHub Pull Requests, their code changes, and generating AI-powered summaries.

## Setup

### Prerequisites
- Docker and Docker Compose
- Python 3.11+
- Poetry (Python package manager)

### First-time Setup
1. Clone the repository
```bash
git clone [repository-url]
cd [repository-name]
```

2. Install dependencies
```bash
make install
```

3. Create a `.env` file in the root directory:
```bash
GITHUB_TOKEN=your_github_token_here
```

4. Initialize the database
```bash
# Start the database
make up

# Run database migrations
make db-migrate
```

### Development Commands
- `make up` - Start the database container
- `make down` - Stop the database container
- `make run` - Start the FastAPI development server
- `make test` - Run tests
- `make clean` - Remove all containers and volumes
- `make db-revision message="your message"` - Create a new database migration
- `make db-migrate` - Apply all pending migrations
- `make db-downgrade` - Rollback the last migration

### Checking Database Status
```bash
# Connect to database
docker compose exec db psql -U github_analysis -d github_analysis

# Common PSQL commands:
\dt    # List all tables
\d     # List table details
\q     # Quit psql
```

## Project Structure
```
.
├── src/
│   └── github_analysis/
│       ├── api/          # API endpoints
│       ├── models/       # Database models
│       └── services/     # Business logic
├── tests/               # Test files
├── migrations/         # Database migrations
├── docker-compose.yml  # Docker configuration
└── Makefile           # Development commands
```

## Database Schema

### Tables
1. pull_requests
   - Stores basic PR information
   - Contains title, body, and creation date
   - Linked to comments and diffs

2. pr_comments
   - Stores PR comments
   - Links back to parent PR
   - Contains comment body and author

3. pr_diffs
   - Stores file changes from PRs
   - Contains file paths and change content
   - Links back to parent PR

## API Endpoints

- `GET /health` - Check service health
- `GET /health/db` - Check database connection
- `GET /test-github` - Test GitHub API connection (temporary)

## Configuration

The application uses environment variables for configuration:
- `GITHUB_TOKEN` - GitHub API token
- `DB_USER` - Database user (default: github_analysis)
- `DB_PASSWORD` - Database password (default: github_analysis)
- `DB_HOST` - Database host (default: localhost)
- `DB_PORT` - Database port (default: 5432)
- `DB_NAME` - Database name (default: github_analysis)

## Embedding Comparison Results

The project uses two approaches for finding similar pull requests:

### AI Summary Approach
Uses GPT-4 to generate a structured summary of the PR and then creates embeddings from this summary. Results show:
- Better at capturing semantic relationships between PRs
- Higher similarity scores for conceptually related changes
- Example findings:
  - Error handling PRs (#1, #2, #4) showed strong similarities (0.63-0.72)
  - Performance improvements (#5, #6) were correctly grouped
  - Feature additions (#3) were properly distinguished from error handling changes

### Raw Diff Approach
Creates embeddings directly from the code changes. Results show:
- Better at capturing syntactic similarities
- More sensitive to specific code patterns
- Example findings:
  - Error handling PRs showed moderate similarity (0.31-0.53)
  - External service changes (#4, #5) showed strong similarity (0.61)
  - API endpoint modifications (#2, #6) were recognized as related (0.57)

### Key Insights
- AI Summary approach is better at understanding the high-level purpose of changes
- Raw Diff approach is better at finding PRs with similar code patterns
- Combining both approaches could provide more comprehensive PR similarity analysis

## Running Tests
```bash
make test
```

## Development
For local development:
1. Start the database: `make up`
2. Run the API server: `make run`
3. API will be available at: http://localhost:8000
