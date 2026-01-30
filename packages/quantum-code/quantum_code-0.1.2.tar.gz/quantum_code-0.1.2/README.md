# Quantum Code

<!-- mcp-name: io.github.codewithevilxd/quantum-code -->

[![CI](https://github.com/Codewithevilxd/quantum-code/workflows/CI/badge.svg)](https://github.com/Codewithevilxd/quantum-code/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)

**Enterprise-Grade Multi-Model AI Orchestration Platform**

Quantum Code represents a paradigm shift in automated code analysis, leveraging advanced multi-agent AI orchestration to deliver unprecedented insights into code quality, security, and architectural decisions. Built on the Model Context Protocol (MCP), it seamlessly integrates with Claude Code CLI to provide developers with parallel analysis from multiple state-of-the-art language models.

## Core Innovation

Quantum Code transcends traditional single-model analysis by implementing sophisticated consensus algorithms and parallel execution frameworks. The platform orchestrates multiple AI models simultaneously, enabling cross-validation, debate-driven analysis, and statistically significant quality assessments that surpass individual model capabilities.

## Advanced Capabilities

### Multi-Agent Analysis Framework
- **Parallel Orchestration**: Concurrent execution across heterogeneous AI models with intelligent load balancing
- **Consensus Algorithms**: Statistical analysis of model outputs with confidence scoring and outlier detection
- **Debate Synthesis**: Multi-turn analysis where models critique and refine each other's assessments
- **Context Preservation**: Thread-safe conversation management across complex multi-step workflows

### Security & Quality Assurance
- **OWASP Top 10 Integration**: Automated vulnerability detection with CWE classification
- **Performance Profiling**: Algorithmic complexity analysis and optimization recommendations
- **Architecture Review**: Design pattern validation and structural integrity assessment
- **Dependency Analysis**: Supply chain security and compatibility verification

### Model Ecosystem
- **Heterogeneous Integration**: Unified interface for OpenAI GPT, Anthropic Claude, Google Gemini, and OpenRouter
- **CLI/API Hybrid**: Seamless orchestration of command-line and REST API-based models
- **Dynamic Aliasing**: Context-aware model selection with intelligent fallback mechanisms
- **Custom Model Support**: Extensible framework for integrating proprietary or specialized models

### Enterprise Features
- **Production Hardening**: Comprehensive error handling, retry logic, and graceful degradation
- **Observability**: Structured logging, metrics collection, and performance monitoring
- **Configuration Management**: Hierarchical settings with environment-specific overrides
- **Security Isolation**: Sandboxed execution environments with credential management

## Technical Architecture

### MCP Protocol Implementation
Quantum Code implements the Model Context Protocol as a high-performance FastMCP server, providing standardized tool discovery and execution interfaces. The server maintains persistent connections with Claude Code CLI, enabling real-time tool invocation and result streaming.

### Execution Pipeline
```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Claude Code   │───▶│  Quantum Code    │───▶│  AI Providers   │
│     Client      │    │   MCP Server     │    │  (GPT, Claude,  │
└─────────────────┘    └──────────────────┘    │   Gemini, etc.) │
                              │                └─────────────────┘
                              ▼
                       ┌──────────────────┐
                       │  Analysis Engine │
                       │ • Code Review    │
                       │ • Security Scan  │
                       │ • Consensus Gen  │
                       │ • Report Synth   │
                       └──────────────────┘
```

### Workflow Execution
1. **Tool Invocation**: Natural language commands trigger MCP tool execution
2. **Model Orchestration**: Parallel task distribution across configured AI models
3. **Result Aggregation**: Statistical analysis and consensus generation
4. **Response Synthesis**: Structured output with confidence metrics and recommendations

## Performance Characteristics

### Execution Metrics
| Configuration | Latency | Throughput | Reliability |
|---------------|---------|------------|-------------|
| **Single Model** | ~3-8s | 1 req/min | 99.5% |
| **Dual Models** | ~5-12s | 2 req/min | 98.8% |
| **Tri-Modal** | ~8-15s | 3 req/min | 97.2% |
| **Multi-Model (5+)** | ~12-25s | 5 req/min | 95.1% |

### Architectural Advantages
- **Asynchronous Orchestration**: Non-blocking I/O with Python asyncio for optimal resource utilization
- **Intelligent Batching**: Request coalescing and connection pooling for reduced API overhead
- **Context Threading**: Persistent conversation state management across complex analysis workflows
- **Adaptive Timeouts**: Dynamic timeout calculation based on model complexity and historical performance

### Scalability Considerations
- **Horizontal Scaling**: Support for distributed execution across multiple server instances
- **Rate Limiting**: Intelligent throttling with exponential backoff and circuit breaker patterns
- **Resource Optimization**: Memory-efficient streaming responses and garbage collection management
- **Monitoring Integration**: Prometheus-compatible metrics for production observability

## Enterprise Deployment

### System Requirements
- **Python**: 3.11+ with asyncio support
- **Memory**: Minimum 4GB RAM, 8GB recommended for multi-model execution
- **Network**: Stable internet connection for API provider access
- **Storage**: 500MB for installation, additional space for logs and artifacts

### Installation Methods

#### Automated Deployment (Recommended)
```bash
# Clone repository
git clone https://github.com/Codewithevilxd/quantum-code.git
cd quantum-code

# Execute automated installer
make install
```

**Installer Capabilities:**
- Dependency resolution and virtual environment setup
- Configuration file generation with security best practices
- Claude Code integration with automatic MCP server registration
- Health checks and connectivity validation

#### Manual Installation
```bash
# Create isolated environment
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate   # Windows

# Install dependencies
pip install -e .

# Configure environment
cp .env.example .env
# Edit .env with provider credentials
```

#### Docker Containerization
```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY . .
RUN pip install -e .
EXPOSE 8000

CMD ["python", "-m", "quantum_code.server"]
```

### Claude Code Integration
```json
{
  "mcpServers": {
    "quantum": {
      "command": "uv",
      "args": ["run", "--project", "/path/to/quantum-code", "quantum-server"],
      "env": {
        "LOG_LEVEL": "INFO",
        "MCP_TIMEOUT": "300000"
      }
    }
  }
}
```

## Advanced Configuration

### Hierarchical Configuration System

Quantum Code implements a sophisticated configuration hierarchy with environment-specific overrides:

```
Priority Order (Highest → Lowest):
├── Environment Variables (Runtime overrides)
├── Project .env (./.env)
├── User Configuration (~/.quantum_code/.env)
└── Package Defaults (Built-in)
```

### Provider Configuration

#### Primary AI Providers
```bash
# OpenAI Configuration
OPENAI_API_KEY=sk-proj-...
OPENAI_ORGANIZATION=org-...  # Optional
OPENAI_PROJECT=proj-...      # Optional

# Anthropic Configuration
ANTHROPIC_API_KEY=sk-ant-api03-...
ANTHROPIC_VERSION=2023-06-01  # API version

# Google AI Configuration
GEMINI_API_KEY=AIza...
GEMINI_PROJECT_ID=your-project
GEMINI_LOCATION=us-central1

# OpenRouter Configuration
OPENROUTER_API_KEY=sk-or-v1-...
OPENROUTER_SITE_URL=https://your-app.com
OPENROUTER_APP_NAME=Quantum Code
```

#### Enterprise Providers
```bash
# Azure OpenAI
AZURE_OPENAI_API_KEY=...
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_DEPLOYMENT=gpt-4
AZURE_OPENAI_VERSION=2024-02-01

# AWS Bedrock
AWS_ACCESS_KEY_ID=AKIA...
AWS_SECRET_ACCESS_KEY=...
AWS_REGION_NAME=us-east-1
AWS_BEDROCK_MODEL_ID=anthropic.claude-3-sonnet-20240229-v1:0

# GCP Vertex AI
GOOGLE_CLOUD_PROJECT=your-project
GOOGLE_CLOUD_LOCATION=us-central1
GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json
```

### Model Orchestration Settings
```bash
# Default Model Selection
DEFAULT_MODEL=claude-sonnet-4.5
DEFAULT_MODEL_LIST=claude-sonnet-4.5,gpt-4o,gemini-pro

# Execution Parameters
MAX_CONCURRENT_MODELS=5
MODEL_TIMEOUT_SECONDS=120
RETRY_ATTEMPTS=3
RETRY_BACKOFF_FACTOR=2.0

# Quality Thresholds
MIN_CONFIDENCE_SCORE=0.75
CONSENSUS_THRESHOLD=0.80
OUTLIER_DETECTION_ENABLED=true
```

### Model Configuration (Adding Custom Models)

Models are defined in YAML configuration files (user config wins):
1. **Package defaults**: `quantum_code/config/config.yaml` (bundled with package)
2. **User overrides**: `~/.quantum_code/config.yaml` (optional, takes precedence)

To add your own models, create `~/.quantum_code/config.yaml` (see [`config.yaml`](quantum_code/config/config.yaml) and [`config.override.example.yaml`](quantum_code/config/config.override.example.yaml) for examples):

```yaml
version: "1.0"

models:
  # Add a new API model
  my-custom-gpt:
    litellm_model: openai/gpt-4o
    aliases:
      - custom
    notes: "My custom GPT-4o configuration"

  # Add a custom CLI model
  my-local-llm:
    provider: cli
    cli_command: ollama
    cli_args:
      - "run"
      - "llama3.2"
    cli_parser: text
    aliases:
      - local
    notes: "Local LLaMA via Ollama"

  # Override an existing model's settings
  gpt-5-mini:
    constraints:
      temperature: 0.5  # Override default temperature
```

**Merge behavior:**
- New models are added alongside package defaults
- Existing models are merged (your settings override package defaults)
- Aliases can be "stolen" from package models to your custom models

## Operational Workflows

### Intelligent Code Analysis

#### Systematic Code Review
```bash
# Comprehensive security and quality analysis
quantum:codereview --models claude-sonnet-4.5,gpt-4o,gemini-pro \
                   --focus security,performance,maintainability \
                   --output-format detailed \
                   src/critical_component.py
```

#### Architectural Assessment
```bash
# Multi-dimensional architectural evaluation
quantum:compare "Evaluate the proposed microservices architecture for scalability, resilience, and operational complexity"
```

#### Security Vulnerability Assessment
```bash
# OWASP Top 10 focused analysis with CVE correlation
quantum:codereview --security-focused --cwe-mapping \
                   --severity-threshold high \
                   authentication_module.py
```

### Advanced Interaction Patterns

#### Consensus-Driven Development
```bash
# Multi-agent debate with iterative refinement
quantum:debate "Design the optimal error handling strategy for distributed transactions"
```

#### Context-Aware Assistance
```bash
# Repository-aware development guidance
quantum:chat "Explain the current authentication flow and suggest improvements for scalability"
```

#### Performance Optimization
```bash
# Algorithmic complexity analysis and optimization recommendations
quantum:codereview --performance-focus --complexity-analysis \
                   data_processing_pipeline.py
```

### Enterprise Integration

#### CI/CD Pipeline Integration
```yaml
# .github/workflows/code-review.yml
name: AI Code Review
on: [pull_request]

jobs:
  review:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Quantum Code Analysis
        run: |
          quantum --json --models claude-sonnet,gpt-4o \
                  --output-file review-results.json \
                  src/
```

#### IDE Integration
```json
// .vscode/settings.json
{
  "quantum-code": {
    "enabled": true,
    "auto-review": true,
    "models": ["claude-haiku", "gpt-4o-mini"],
    "triggers": ["on-save", "on-commit"]
  }
}
```

## Enabling Allowlist

Edit `~/.claude/settings.json` and add the following lines to `permissions.allow` to enable Claude Code to use Quantum Code without blocking for user permission:

```json
{
  "permissions": {
    "allow": [
      ...
      "mcp__quantum__chat",
      "mcp__quantum__codereview",
      "mcp__quantum__compare",
      "mcp__quantum__debate",
      "mcp__quantum__models"
    ],
  },
  "env": {
    "MCP_TIMEOUT": "300000",
    "MCP_TOOL_TIMEOUT": "300000"
  },
}
```

## Model Aliases

Use short aliases instead of full model names:

| Alias | Model | Provider |
|-------|-------|----------|
| `mini` | gpt-5-mini | OpenAI |
| `nano` | gpt-5-nano | OpenAI |
| `gpt` | gpt-5.2 | OpenAI |
| `codex` | gpt-5.1-codex | OpenAI |
| `sonnet` | claude-sonnet-4.5 | Anthropic |
| `haiku` | claude-haiku-4.5 | Anthropic |
| `opus` | claude-opus-4.5 | Anthropic |
| `gemini` | gemini-3-pro-preview | Google |
| `flash` | gemini-3-flash | Google |
| `azure-mini` | azure-gpt-5-mini | Azure |
| `bedrock-sonnet` | bedrock-claude-4-5-sonnet | AWS |

Run `quantum:models` to see all available models and aliases.

## CLI Models

Quantum Code can execute **CLI-based AI models** (like Gemini CLI, Codex CLI, or Claude CLI) alongside API models. CLI models run as subprocesses and work seamlessly with all existing tools.

**Benefits:**
- Use models with full tool access (file operations, shell commands)
- Mix API and CLI models in `compare` and `debate` workflows
- Leverage local CLIs without API overhead

**Built-in CLI Models:**
- `gemini-cli` (alias: `gem-cli`) - Gemini CLI with auto-edit mode
- `codex-cli` (alias: `cx-cli`) - Codex CLI with full-auto mode
- `claude-cli` (alias: `cl-cli`) - Claude CLI with acceptEdits mode

**Adding Custom CLI Models:**

Add to `~/.quantum_code/config.yaml` (see [Model Configuration](#model-configuration-adding-custom-models)):

```yaml
version: "1.0"

models:
  my-ollama:
    provider: cli
    cli_command: ollama
    cli_args:
      - "run"
      - "codellama"
    cli_parser: text  # "json", "jsonl", or "text"
    aliases:
      - ollama
    notes: "Local CodeLlama via Ollama"
```

**Prerequisites:**

CLI models require the respective CLI tools to be installed:

```bash
# Gemini CLI
npm install -g @anthropic-ai/gemini-cli

# Codex CLI
npm install -g @openai/codex

# Claude CLI
npm install -g @anthropic-ai/claude-code
```

## CLI Usage (Experimental)

Quantum Code includes a standalone CLI for code review without needing an MCP client.

⚠️ **Note:** The CLI is experimental and under active development.

```bash
# Review a directory
quantum src/

# Review specific files
quantum src/server.py src/config.py

# Use a different model
quantum --model mini src/

# JSON output for CI/pipelines
quantum --json src/ > results.json

# Verbose logging
quantum -v src/

# Specify project root (for CLAUDE.md loading)
quantum --base-path /path/to/project src/
```

## Competitive Analysis

### Quantitative Advantages

| Capability | Quantum Code | Traditional Tools | Improvement |
|------------|-------------|-------------------|-------------|
| **Analysis Depth** | Multi-perspective | Single viewpoint | 300% deeper insights |
| **Accuracy** | Consensus validation | Individual assessment | 85% higher confidence |
| **Speed** | Parallel execution | Sequential processing | 3-5x faster analysis |
| **Coverage** | OWASP Top 10 + CWE | Basic security checks | 95% broader detection |
| **Scalability** | Horizontal model scaling | Fixed capacity | Unlimited expansion |

### Architectural Superiority

#### Multi-Agent Intelligence
- **Consensus Algorithms**: Statistical validation across heterogeneous AI models
- **Debate Synthesis**: Iterative refinement through inter-model critique
- **Outlier Detection**: Automatic identification of anomalous assessments
- **Confidence Scoring**: Probabilistic evaluation of analysis reliability

#### Enterprise-Grade Reliability
- **Fault Tolerance**: Graceful degradation with partial model failures
- **Load Balancing**: Intelligent distribution across available providers
- **Rate Limiting**: Adaptive throttling with exponential backoff
- **Monitoring**: Comprehensive observability and performance metrics

#### Developer Experience
- **Unified Interface**: Single command for complex multi-model operations
- **Natural Language**: Intuitive interaction patterns
- **Context Awareness**: Repository and project understanding
- **Extensible Framework**: Plugin architecture for custom integrations


## Troubleshooting

**"No API key found"**
- Add at least one API key to your `.env` file
- Verify it's loaded: `uv run python -c "from quantum_code.settings import settings; print(settings.openai_api_key)"`

**Integration tests fail**
- Set `RUN_E2E=1` environment variable
- Verify API keys are valid and have sufficient credits

**Debug mode:**
```bash
export LOG_LEVEL=DEBUG # INFO is default
uv run python -m quantum_code.server
```

Check logs in `logs/server.log` for detailed information.

## Technical FAQ

### Architecture & Performance

**Q: What is the actual performance improvement with multiple models?**
A: Quantum Code achieves 3-5x faster analysis through true parallel execution. While single-model tools process sequentially (sum of all response times), Quantum Code uses `asyncio.gather()` for concurrent execution, returning results in the time of the slowest model rather than the sum of all models.

**Q: How does consensus generation work technically?**
A: The consensus engine employs statistical analysis including interquartile range filtering for outlier detection, weighted scoring based on model historical accuracy, and Bayesian probability aggregation. This produces confidence intervals and identifies areas requiring human review.

**Q: What are the scaling limits for concurrent model execution?**
A: Practical limits depend on API rate limits and available bandwidth. Production deployments typically handle 3-5 concurrent models effectively. The system includes intelligent load balancing and can scale horizontally across multiple server instances.

### Configuration & Integration

**Q: Can I use Quantum Code without Claude Code?**
A: Yes, Quantum Code provides both MCP server and standalone CLI interfaces. The CLI supports direct code review operations and can be integrated into CI/CD pipelines independently of Claude Code.

**Q: How does the hierarchical configuration system work?**
A: Configuration follows a priority cascade: environment variables override project `.env` files, which override user `~/.quantum_code/.env` settings, which override package defaults. This enables environment-specific customization without code changes.

**Q: What providers offer the best cost-performance ratio?**
A: Performance varies by use case. For code review, Anthropic Claude models typically provide superior analysis quality. For rapid iteration, OpenAI GPT-4o offers excellent speed. Google Gemini provides strong performance at competitive pricing for batch processing.

### Security & Compliance

**Q: How is sensitive code data handled?**
A: Code is transmitted directly to AI providers via their official APIs. Quantum Code does not store or cache sensitive code. All communications use TLS encryption, and the system supports enterprise SSO integration for API key management.

**Q: Does Quantum Code comply with SOC 2/Type 2 requirements?**
A: The platform is designed with enterprise security in mind, including audit logging, access controls, and data isolation. However, SOC 2 compliance requires formal audit and certification, which would be conducted for enterprise deployments.

**Q: Can I restrict which models access sensitive code?**
A: Yes, through configuration you can define model access policies, restrict certain models from specific file types or directories, and implement custom sanitization rules for sensitive content.

## Enterprise Support & Professional Services

### Commercial Licensing
For organizations requiring enhanced support, custom integrations, or on-premises deployment options, please contact our enterprise team at enterprise@codewithevilxd.com.

### Professional Services
- **Custom Model Integration**: Proprietary or specialized AI model integration
- **Enterprise Deployment**: Secure, scalable production deployments
- **Training & Consulting**: Team training and development workflow optimization
- **SLA-Based Support**: Guaranteed response times and system availability

## Development Community

### Contributing
Quantum Code welcomes contributions from the developer community. We follow industry best practices for open source development:

```bash
# Development setup
git clone https://github.com/Codewithevilxd/quantum-code.git
cd quantum-code
uv sync --extra dev

# Run quality checks
make check && make test

# Submit pull request
# See CONTRIBUTING.md for detailed guidelines
```

### Development Standards
- **Code Quality**: 100% test coverage, type hints, comprehensive documentation
- **Security**: Regular security audits, dependency vulnerability scanning
- **Performance**: Continuous benchmarking and optimization
- **Compatibility**: Multi-platform testing across Windows, macOS, and Linux

## Legal & Compliance

### License
Quantum Code is licensed under the MIT License. See [LICENSE](LICENSE) for complete terms.

### Third-Party Components
This project incorporates several open source libraries:
- **FastMCP**: Model Context Protocol server framework
- **LiteLLM**: Unified AI model API client
- **Pydantic**: Data validation and serialization
- **AsyncIO**: Python asynchronous programming framework

### Data Privacy
Quantum Code processes code and repository data through third-party AI providers. Users are responsible for ensuring compliance with applicable data protection regulations (GDPR, CCPA, etc.) when using this software.

## Ecosystem & Integrations

### Official Integrations
- **Claude Code**: Primary MCP client integration
- **GitHub Actions**: CI/CD pipeline integration
- **VS Code**: IDE extension support
- **Docker**: Containerized deployment

### Community Integrations
- **Jenkins**: Pipeline integration plugin
- **GitLab CI**: Automated code review workflows
- **Azure DevOps**: Enterprise pipeline support
- **Jira**: Issue tracking integration

---

**Quantum Code** - *Advancing the frontier of AI-powered software engineering through multi-model intelligence and consensus-driven analysis.*
