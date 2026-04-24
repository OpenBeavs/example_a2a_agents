# example_a2a_agents

A collection of A2A (Agent-to-Agent) protocol agents built with [Google ADK](https://google.github.io/adk-docs/) and deployable to **Google Cloud Run**. These agents are compatible with the [GENESIS-AI-Hub / OpenBeavs](https://github.com/OpenBeavs/GENESIS-AI-Hub) platform.

---

## What Is A2A?

The A2A protocol is a JSON-RPC 2.0 standard for inter-agent communication. Every agent:

1. Exposes a **discovery card** at `/.well-known/agent.json` describing its capabilities.
2. Accepts **JSON-RPC 2.0 messages** at a `/a2a/<agent_name>/` endpoint.
3. Can be registered with any A2A-compatible hub (like GENESIS-AI-Hub) for discovery and use.

---

## Agents

### New Agents (this repo)

| Agent | Description | Tools | External API |
|-------|-------------|-------|--------------|
| [financial_auditor_agent](#1-financial-auditor-agent) | Financial ratio analysis, anomaly detection, audit reports | 3 tools | None |
| [weather_agent](#2-weather-agent) | Current weather & multi-day forecasts worldwide | 3 tools | Open-Meteo (free) |
| [code_review_agent](#3-code-review-agent) | Code smell detection, security scanning, complexity metrics | 3 tools | None |
| [trivia_agent](#4-trivia-agent) | Multi-category trivia quiz with answer evaluation | 3 tools | Open Trivia DB (free) |
| [unit_converter_agent](#5-unit-converter-agent) | Length, temp, weight, volume, speed, data conversions | 6 tools | None |

### Migrated Agents (from OpenBeavs/GENESIS-AI-Hub)

| Agent | Description |
|-------|-------------|
| `Cyrano-de-Bergerac/` | Multi-agent SequentialAgent: tone analysis → eloquent response |
| `oregon-state-expert/` | Oregon State University expert using Google Search |
| `oregon-state-scraper/` | OSU website scraper and knowledge agent |
| `weather-expert-agent/` | Original weather expert agent |
| `chatgpt-agent/` | ChatGPT API wrapper agent |
| `claude-agent/` | Claude API wrapper agent |
| `gemini-agent/` | Gemini API wrapper agent |

---

## Agent Details

### 1. Financial Auditor Agent

**Directory:** `financial_auditor_agent/`  
**Cloud Run service:** `financial-auditor-agent`

Performs financial statement analysis with zero external API calls (beyond Gemini). Useful for auditing quarterly reports, detecting irregular transactions, and generating risk-rated audit summaries.

#### Tools

| Tool | Description |
|------|-------------|
| `calculate_financial_ratios` | Computes gross margin, net margin, current ratio, D/E, ROA, ROE, operating ratio |
| `detect_anomalies` | Z-score based outlier detection on lists of transaction amounts |
| `generate_audit_report` | Produces a structured audit summary with LOW/MEDIUM/HIGH risk rating |

#### Example queries
```
Calculate financial ratios: revenue $5M, COGS $2M, OpEx $1M, net income $800K,
assets $4M, liabilities $1.5M, current assets $1.2M, current liabilities $600K, equity $2.5M

Check these transactions for anomalies: [1200, 1150, 1300, 1180, 45000, 1250, 1100]

Generate an audit report for Acme Corp Q3 2024
```

#### Agent Card

```json
{
  "name": "financial_auditor_agent",
  "description": "A financial auditing agent that calculates key financial ratios, detects transaction anomalies using Z-score analysis, and generates structured audit reports with risk ratings.",
  "version": "1.0.0",
  "url": "https://financial-auditor-agent-PROJECT_NUMBER.us-west1.run.app/a2a/financial_auditor_agent",
  "defaultInputModes": ["text"],
  "defaultOutputModes": ["text"],
  "capabilities": { "streaming": false, "pushNotifications": false },
  "skills": [
    {
      "id": "financial-ratio-analysis",
      "name": "Financial Ratio Analysis",
      "description": "Calculate gross margin, net margin, current ratio, debt-to-equity, ROA, ROE, and operating ratio from raw financial statement figures.",
      "tags": ["finance", "ratios", "accounting", "analysis"]
    },
    {
      "id": "anomaly-detection",
      "name": "Transaction Anomaly Detection",
      "description": "Detect statistically anomalous transactions in a dataset using Z-score analysis with configurable thresholds.",
      "tags": ["fraud-detection", "anomaly", "statistics", "audit"]
    },
    {
      "id": "audit-report-generation",
      "name": "Audit Report Generation",
      "description": "Generate a structured audit summary report with a risk score and recommendation based on findings.",
      "tags": ["audit", "report", "compliance", "risk"]
    }
  ]
}
```

---

### 2. Weather Agent

**Directory:** `weather_agent/`  
**Cloud Run service:** `weather-agent`

Provides real-time current conditions and 1–16 day forecasts for any city in the world using the [Open-Meteo API](https://open-meteo.com/) (free, no API key required).

#### Tools

| Tool | Description |
|------|-------------|
| `geocode_city` | Resolves a city name to latitude/longitude using Open-Meteo Geocoding |
| `get_current_weather` | Returns temperature, humidity, wind, precipitation, and sky conditions |
| `get_forecast` | Returns daily high/low, precipitation, and wind for 1–16 days |

#### Example queries
```
What is the weather in Portland, Oregon right now?
Give me a 5-day forecast for Seattle
Will it snow in Denver this week?
```

#### Agent Card

```json
{
  "name": "weather_agent",
  "description": "A weather agent that provides real-time current conditions and multi-day forecasts for any city worldwide using the Open-Meteo free API.",
  "version": "1.0.0",
  "url": "https://weather-agent-PROJECT_NUMBER.us-west1.run.app/a2a/weather_agent",
  "defaultInputModes": ["text"],
  "defaultOutputModes": ["text"],
  "capabilities": { "streaming": false, "pushNotifications": false },
  "skills": [
    {
      "id": "current-weather",
      "name": "Current Weather Lookup",
      "description": "Get real-time temperature, humidity, wind speed, precipitation, and sky conditions for any city.",
      "tags": ["weather", "current", "temperature", "forecast"]
    },
    {
      "id": "weather-forecast",
      "name": "Multi-Day Weather Forecast",
      "description": "Get a daily forecast (highs, lows, precipitation, conditions) for 1–16 days ahead.",
      "tags": ["forecast", "weather", "daily", "planning"]
    }
  ]
}
```

---

### 3. Code Review Agent

**Directory:** `code_review_agent/`  
**Cloud Run service:** `code-review-agent`

Reviews Python code snippets using Python's built-in `ast` module and regex patterns — no external APIs needed. Detects code smells, security vulnerabilities, and computes cyclomatic complexity.

#### Tools

| Tool | Description |
|------|-------------|
| `detect_code_smells` | Finds long functions, magic numbers, too many params, missing docstrings, TODO markers |
| `check_security_patterns` | Scans for hardcoded creds, SQL injection, shell injection, eval/exec, pickle, SSL bypass |
| `calculate_complexity_metrics` | Cyclomatic complexity, function/class count, line count, maintainability rating |

#### Example queries
```
Review this Python function for code smells
Check this snippet for SQL injection risks
What is the cyclomatic complexity of my code?
Does this code have any hardcoded secrets?
```

#### Agent Card

```json
{
  "name": "code_review_agent",
  "description": "A code review agent that detects code smells, identifies security vulnerabilities, and calculates cyclomatic complexity metrics for Python and other languages.",
  "version": "1.0.0",
  "url": "https://code-review-agent-PROJECT_NUMBER.us-west1.run.app/a2a/code_review_agent",
  "defaultInputModes": ["text"],
  "defaultOutputModes": ["text"],
  "capabilities": { "streaming": false, "pushNotifications": false },
  "skills": [
    {
      "id": "code-smell-detection",
      "name": "Code Smell Detection",
      "description": "Identify structural code quality issues such as long functions, magic numbers, too many parameters, missing docstrings, and TODO markers.",
      "tags": ["code-quality", "refactoring", "clean-code", "review"]
    },
    {
      "id": "security-analysis",
      "name": "Security Pattern Analysis",
      "description": "Scan code for hardcoded credentials, SQL injection, shell injection, eval/exec usage, insecure deserialization, and SSL verification bypass.",
      "tags": ["security", "owasp", "vulnerability", "review"]
    },
    {
      "id": "complexity-metrics",
      "name": "Complexity Metrics",
      "description": "Compute cyclomatic complexity, function count, class count, and line count for Python code.",
      "tags": ["complexity", "metrics", "maintainability", "python"]
    }
  ]
}
```

---

### 4. Trivia Agent

**Directory:** `trivia_agent/`  
**Cloud Run service:** `trivia-agent`

An interactive trivia host that pulls questions from the [Open Trivia Database](https://opentdb.com/) (free, no API key) across 24 categories and 3 difficulty levels.

#### Tools

| Tool | Description |
|------|-------------|
| `list_trivia_categories` | Returns all 24 available question categories with their IDs |
| `fetch_trivia_question` | Fetches a question with shuffled multiple-choice or true/false options |
| `evaluate_answer` | Case-insensitive answer check with feedback |

#### Example queries
```
Ask me a trivia question
What categories are available?
Give me a hard science question
Quiz me on history — easy difficulty
```

#### Agent Card

```json
{
  "name": "trivia_agent",
  "description": "A trivia host agent that fetches questions from Open Trivia DB across dozens of categories and difficulties, presents choices, and evaluates user answers.",
  "version": "1.0.0",
  "url": "https://trivia-agent-PROJECT_NUMBER.us-west1.run.app/a2a/trivia_agent",
  "defaultInputModes": ["text"],
  "defaultOutputModes": ["text"],
  "capabilities": { "streaming": false, "pushNotifications": false },
  "skills": [
    {
      "id": "trivia-quiz",
      "name": "Trivia Quiz",
      "description": "Ask trivia questions from 24 categories at easy, medium, or hard difficulty.",
      "tags": ["trivia", "quiz", "games", "education"]
    },
    {
      "id": "answer-evaluation",
      "name": "Answer Evaluation",
      "description": "Evaluate whether a user's answer to a trivia question is correct.",
      "tags": ["trivia", "quiz", "evaluation", "feedback"]
    }
  ]
}
```

---

### 5. Unit Converter Agent

**Directory:** `unit_converter_agent/`  
**Cloud Run service:** `unit-converter-agent`

Converts between dozens of units across 6 measurement categories — all pure Python with no external API calls.

#### Tools

| Tool | Supported Units |
|------|----------------|
| `convert_length` | mm, cm, m, km, in, ft, yd, mi, nmi |
| `convert_temperature` | Celsius, Fahrenheit, Kelvin |
| `convert_weight` | mg, g, kg, tonne, oz, lb, st, ton |
| `convert_volume` | ml, L, m³, tsp, tbsp, fl oz, cup, pt, qt, gal |
| `convert_speed` | m/s, km/h, mph, knots, ft/s |
| `convert_data_storage` | bytes, KB, MB, GB, TB, PB |

#### Example queries
```
Convert 5 miles to kilometers
What is 100°F in Celsius?
How many MB in 2.5 GB?
Convert 60 mph to km/h
How many liters in 2 gallons?
```

#### Agent Card

```json
{
  "name": "unit_converter_agent",
  "description": "A unit conversion agent supporting length, temperature, weight, volume, speed, and data storage — all computed locally with no external APIs.",
  "version": "1.0.0",
  "url": "https://unit-converter-agent-PROJECT_NUMBER.us-west1.run.app/a2a/unit_converter_agent",
  "defaultInputModes": ["text"],
  "defaultOutputModes": ["text"],
  "capabilities": { "streaming": false, "pushNotifications": false },
  "skills": [
    { "id": "length-conversion", "name": "Length Conversion", "tags": ["conversion", "length", "distance"] },
    { "id": "temperature-conversion", "name": "Temperature Conversion", "tags": ["temperature", "celsius", "fahrenheit"] },
    { "id": "weight-conversion", "name": "Weight Conversion", "tags": ["weight", "mass", "conversion"] },
    { "id": "volume-conversion", "name": "Volume Conversion", "tags": ["volume", "liquid", "cooking"] },
    { "id": "speed-conversion", "name": "Speed Conversion", "tags": ["speed", "velocity", "physics"] },
    { "id": "data-storage-conversion", "name": "Data Storage Conversion", "tags": ["data", "bytes", "computing"] }
  ]
}
```

---

## Prerequisites

- Python 3.11+
- [Google ADK](https://google.github.io/adk-docs/): `pip install google-adk[a2a]`
- A **Google AI Studio API key** (`GOOGLE_API_KEY`) for Gemini
- [Google Cloud SDK](https://cloud.google.com/sdk/docs/install) (`gcloud`) — for deployment only
- A GCP project with Cloud Run and Cloud Build APIs enabled

---

## Local Development

### 1. Clone and set up environment

```bash
git clone https://github.com/gitJamoo/example_a2a_agents.git
cd example_a2a_agents

# Create a virtual environment
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate

# Install dependencies for a specific agent
pip install -r financial_auditor_agent/requirements.txt
```

### 2. Configure environment variables

```bash
cp .env.example .env
# Edit .env and set GOOGLE_API_KEY
```

### 3. Run an agent locally (ADK dev UI)

```bash
# From the repo root:
adk web                            # Interactive web UI at http://localhost:8000
# or
adk api_server --a2a .             # Serve A2A endpoints for all agents in this dir

# Test the agent card:
curl http://localhost:8000/a2a/financial_auditor_agent/.well-known/agent-card.json
```

### 4. Run tests

```bash
# Install pytest if needed
pip install pytest

# Run all tests
pytest financial_auditor_agent/tests/ -v
pytest weather_agent/tests/ -v
pytest code_review_agent/tests/ -v
pytest trivia_agent/tests/ -v
pytest unit_converter_agent/tests/ -v

# Run all at once
pytest */tests/ -v
```

---

## Deploying to GCP Cloud Run

Each agent is independently deployable. The shared `deploy_agent.py` script handles the full deployment including public IAM binding required for A2A card discovery.

### Prerequisites

```bash
# Authenticate
gcloud auth login
gcloud auth configure-docker

# Set default project and region
gcloud config set project YOUR_GCP_PROJECT_ID
gcloud config set compute/region us-west1

# Enable required APIs (one-time)
gcloud services enable run.googleapis.com cloudbuild.googleapis.com
```

### Deploy a single agent

```bash
# Deploy the financial auditor agent
python deploy_agent.py financial_auditor_agent

# Deploy with explicit project / region
python deploy_agent.py weather_agent --project osu-genesis-hub --region us-west1

# Deploy with more memory (for agents that load large models)
python deploy_agent.py code_review_agent --memory 2Gi
```

### Deploy all 5 new agents

```bash
for agent in financial_auditor_agent weather_agent code_review_agent trivia_agent unit_converter_agent; do
  python deploy_agent.py $agent --project osu-genesis-hub --region us-west1
done
```

### What `deploy_agent.py` does

1. Detects your GCP project and region from `gcloud config` (or CLI flags).
2. Converts `agent_name_underscored` → `agent-name-dashed` for the Cloud Run service name.
3. Runs `gcloud run deploy --source=<agent_dir>` — Cloud Build triggers automatically.
4. Re-applies `allUsers` IAM binding so the agent card endpoint is publicly accessible (required for A2A discovery).
5. Prints the service URL, agent card URL, and RPC endpoint.

### After deployment: update agent.json URLs

After deploying, replace `PROJECT_NUMBER` in each `agent.json` with your actual GCP project number:

```bash
# Find your project number
gcloud projects describe YOUR_PROJECT_ID --format="value(projectNumber)"

# Example deployed URLs (project number: 716080272371, region: us-west1):
# https://financial-auditor-agent-716080272371.us-west1.run.app/a2a/financial_auditor_agent
# https://weather-agent-716080272371.us-west1.run.app/a2a/weather_agent
# https://code-review-agent-716080272371.us-west1.run.app/a2a/code_review_agent
# https://trivia-agent-716080272371.us-west1.run.app/a2a/trivia_agent
# https://unit-converter-agent-716080272371.us-west1.run.app/a2a/unit_converter_agent
```

### Verify deployment

```bash
# Check agent card is live (replace with your actual URL)
curl https://financial-auditor-agent-716080272371.us-west1.run.app/a2a/financial_auditor_agent/.well-known/agent-card.json

# Send a test message
curl -X POST https://financial-auditor-agent-716080272371.us-west1.run.app/a2a/financial_auditor_agent/ \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "message/send",
    "params": {
      "message": {
        "messageId": "test-001",
        "role": "user",
        "parts": [{"text": "What is the current ratio if assets are $300K and liabilities are $150K?", "type": "text"}]
      }
    },
    "id": 1
  }'
```

---

## Registering with GENESIS-AI-Hub

Once deployed, register each agent with the hub:

```bash
# Using the OpenBeavs hub API (replace with your hub URL and auth token)
curl -X POST https://your-hub.run.app/api/agents/register-by-url \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://financial-auditor-agent-716080272371.us-west1.run.app/a2a/financial_auditor_agent/.well-known/agent-card.json"}'
```

Or use the GENESIS-AI-Hub web UI: **Workspace → Agents → Add Agent → Enter URL**.

---

## Repository Structure

```
example_a2a_agents/
├── README.md
├── deploy_agent.py                    # Shared GCP Cloud Run deployment script
├── .env.example                       # Root env vars template
├── .gitignore
│
├── financial_auditor_agent/           # NEW: Financial ratio analysis + audit reports
│   ├── agent.py
│   ├── agent.json
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── .env.example
│   └── tests/
│       └── test_agent.py              # 18 tests
│
├── weather_agent/                     # NEW: Open-Meteo weather + forecasts
│   ├── agent.py
│   ├── agent.json
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── .env.example
│   └── tests/
│       └── test_agent.py              # 12 tests
│
├── code_review_agent/                 # NEW: AST-based code review + security scan
│   ├── agent.py
│   ├── agent.json
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── .env.example
│   └── tests/
│       └── test_agent.py              # 24 tests
│
├── trivia_agent/                      # NEW: Open Trivia DB quiz host
│   ├── agent.py
│   ├── agent.json
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── .env.example
│   └── tests/
│       └── test_agent.py              # 15 tests
│
├── unit_converter_agent/              # NEW: Multi-category unit conversion
│   ├── agent.py
│   ├── agent.json
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── .env.example
│   └── tests/
│       └── test_agent.py              # 24 tests
│
├── Cyrano-de-Bergerac/                # MIGRATED from OpenBeavs/GENESIS-AI-Hub
├── oregon-state-expert/               # MIGRATED from OpenBeavs/GENESIS-AI-Hub
├── oregon-state-scraper/              # MIGRATED from OpenBeavs/GENESIS-AI-Hub
├── weather-expert-agent/              # MIGRATED from OpenBeavs/GENESIS-AI-Hub
├── chatgpt-agent/                     # MIGRATED from OpenBeavs/GENESIS-AI-Hub
├── claude-agent/                      # MIGRATED from OpenBeavs/GENESIS-AI-Hub
└── gemini-agent/                      # MIGRATED from OpenBeavs/GENESIS-AI-Hub
```

---

## How Each Agent Is Structured (ADK Pattern)

All new agents follow the `adk api_server` pattern used by [OSU-RAG-Pipeline](https://github.com/OpenBeavs/OSU-RAG-Pipeline):

```
agent_name/
├── agent.py          # Defines root_agent = Agent(name="agent_name", tools=[...])
├── agent.json        # Static A2A discovery card
├── Dockerfile        # Copies to /app/agents/agent_name/ and runs adk api_server --a2a
├── requirements.txt  # google-adk[a2a], python-dotenv, + any agent-specific deps
└── tests/
    └── test_agent.py # Pytest tests for all tool functions (no Gemini calls needed)
```

The ADK server automatically serves:
- `GET /a2a/<agent_name>/.well-known/agent-card.json` — discovery card
- `POST /a2a/<agent_name>/` — JSON-RPC 2.0 message endpoint

---

## Contributing

New agents should follow the patterns above. See [GENESIS-AI-Hub AGENTS.md](https://github.com/OpenBeavs/GENESIS-AI-Hub/blob/main/AGENTS.md) for full A2A protocol documentation and code conventions.
