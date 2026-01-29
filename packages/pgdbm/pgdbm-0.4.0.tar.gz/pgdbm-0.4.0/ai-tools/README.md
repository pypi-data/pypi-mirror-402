# AI Tools Plugin Marketplace  for Claude Code

**Python tools for AI development by [Juan Reyero](https://github.com/juanre)**

Production-ready packages for databases, LLM integration, and document search. Each package includes multiple Claude Code skills providing guidance on best practices and patterns.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Quick Start

```bash
# Add marketplace
/plugin marketplace add juanre/ai-tools

# Install all skills for a package
/plugin install pgdbm@juanre-ai-tools
/plugin install llmemory@juanre-ai-tools
/plugin install llmring@juanre-ai-tools

# Or install individual skills
/plugin install pgdbm-shared-pool@juanre-ai-tools
/plugin install llmemory-hybrid-search@juanre-ai-tools
/plugin install llmring-streaming@juanre-ai-tools
```

## What Are These Skills?

Claude Code skills are **expert guidance systems** that teach Claude how to work with your packages. When you ask Claude for help with databases, LLMs, or document search, these skills automatically activate and provide:

- ✅ Production-ready code examples
- ✅ Best practices and patterns
- ✅ Common pitfalls to avoid
- ✅ Architecture guidance
- ✅ Testing strategies

**No manual needed** - just ask Claude naturally and the right skills load automatically!

## Available Packages

### 🗄️ pgdbm - PostgreSQL Database Management

Production-ready async PostgreSQL with migrations, connection pooling, and schema isolation.

**[Package on GitHub](https://github.com/juanre/pgdbm) | [PyPI](https://pypi.org/project/pgdbm/)**

**Skills included:**
- `pgdbm` - Complete skill set (all 9 skills)
- `pgdbm-choosing-pattern` - Decision guide for which pattern to use
- `pgdbm-shared-pool` - Production pattern with connection pooling ⭐
- `pgdbm-dual-mode` - Create portable database libraries
- `pgdbm-standalone` - Standalone service pattern
- `pgdbm-testing` - Test your database code
- `pgdbm-usage` - Basic operations and queries
- `pgdbm-core-api` - Complete API reference
- `pgdbm-migrations-api` - Migrations API reference
- `pgdbm-common-mistakes` - Common pitfalls and how to avoid them

**When to use:** Building FastAPI apps, microservices, multi-tenant SaaS, or any production application needing PostgreSQL.

**Key features:**
- Async operations with asyncpg
- Automatic migrations with version control
- Connection pooling for production
- Schema isolation for multi-module apps
- Built-in testing utilities

```bash
# Install all pgdbm skills
/plugin install pgdbm@juanre-ai-tools

# Or just what you need
/plugin install pgdbm-shared-pool@juanre-ai-tools
```

### 🔍 llmemory - Document Memory with Vector Search

High-performance document memory system with hybrid search, multi-query expansion, and reranking.

**[Package on GitHub](https://github.com/juanre/llmemory) | [PyPI](https://pypi.org/project/llmemory/)**

**Skills included:**
- `llmemory` - Complete skill set (all 5 skills)
- `llmemory-basic-usage` - Installation and basic operations
- `llmemory-hybrid-search` - Combining vector + BM25 search ⭐
- `llmemory-multi-query` - Query expansion for better results
- `llmemory-multi-tenant` - Owner-based isolation for SaaS
- `llmemory-rag` - Building complete RAG systems

**When to use:** Building RAG applications, semantic search, document management, or chatbots with knowledge bases.

**Key features:**
- Hybrid search (vector + BM25 with RRF)
- Query expansion (heuristic + LLM semantic variants)
- Multiple rerankers (OpenAI, CrossEncoder, Lexical)
- Query routing (answerable detection, prevents hallucinations)
- Contextual retrieval (Anthropic's approach)
- Hierarchical chunking with true parent context
- Multi-tenant with owner-based isolation
- pgvector with HNSW indexes
- Multi-language support (14+ languages)
- SOTA RAG compliance (95/100)

```bash
# Install all llmemory skills
/plugin install llmemory@juanre-ai-tools

# Or specific skills
/plugin install llmemory-hybrid-search@juanre-ai-tools
/plugin install llmemory-rag@juanre-ai-tools
```

### 🤖 llmring - Unified LLM Interface

Single interface for OpenAI, Anthropic, Google Gemini, and Ollama with streaming, tools, and structured output.

**[Package on GitHub](https://github.com/juanre/llmring) | [PyPI](https://pypi.org/project/llmring/)**

**Skills included:**
- `llmring` - Complete skill set (all 6 skills)
- `llmring-chat` - Basic chat completions ⭐
- `llmring-streaming` - Streaming responses
- `llmring-tools` - Function calling and tool use
- `llmring-structured` - JSON schema and typed responses
- `llmring-lockfile` - Aliases, profiles, and configuration
- `llmring-providers` - Multi-provider switching and fallbacks

**When to use:** Building LLM applications, multi-provider setups, AI agents, or any application integrating with LLMs.

**Key features:**
- Unified API across all providers
- Semantic aliases (fast, balanced, deep)
- Automatic fallback models
- Streaming support everywhere
- Tool calling with consistent interface
- Cost tracking and receipts
- Profile support (dev/staging/prod)

```bash
# Install all llmring skills
/plugin install llmring@juanre-ai-tools

# Or specific skills
/plugin install llmring-streaming@juanre-ai-tools
/plugin install llmring-tools@juanre-ai-tools
```

## How Skills Work

### Example: Building a FastAPI App

**You ask:**
> "Help me build a FastAPI app with PostgreSQL connection pooling"

**What happens:**
1. Claude sees "FastAPI", "PostgreSQL", "connection pooling"
2. Automatically loads `pgdbm-shared-pool` skill
3. Provides expert guidance with production patterns
4. Shows you the exact code you need

**Result:** Production-ready code following best practices, no manual lookup needed!

### Example: Building a RAG System

**You ask:**
> "Build a RAG system with hybrid search for customer support docs"

**What happens:**
1. Claude sees "RAG", "hybrid search"
2. Loads `llmemory-hybrid-search` and `llmemory-rag` skills
3. Guides you through document ingestion, search setup, and retrieval
4. Shows you how to combine vector + keyword search

**Result:** Complete RAG implementation with best practices built-in!

## Installation Guide

### Step 1: Install Python Packages

```bash
# Install the packages you need
uv add pgdbm
uv add llmemory
uv add llmring

# Or with pip
pip install pgdbm llmemory llmring
```

### Step 2: Install Claude Code Skills

```bash
# In Claude Code terminal
/plugin marketplace add juanre/ai-tools

# Install complete skill sets
/plugin install pgdbm@juanre-ai-tools
/plugin install llmemory@juanre-ai-tools
/plugin install llmring@juanre-ai-tools
```

### Step 3: Start Building!

Just ask Claude naturally:

```
"Create a FastAPI app with PostgreSQL"
"Build a RAG system with document search"
"Add streaming responses from OpenAI"
"Help me test my database code"
```

Claude will automatically use the relevant skills to provide expert guidance!

## Complete Skill List

### pgdbm (9 skills)
| Skill | Description | Install |
|-------|-------------|---------|
| `pgdbm` | All pgdbm skills | `/plugin install pgdbm@juanre-ai-tools` |
| `pgdbm-choosing-pattern` | Choose the right pattern | `/plugin install pgdbm-choosing-pattern@juanre-ai-tools` |
| `pgdbm-shared-pool` | Production connection pooling | `/plugin install pgdbm-shared-pool@juanre-ai-tools` |
| `pgdbm-dual-mode` | Portable database libraries | `/plugin install pgdbm-dual-mode@juanre-ai-tools` |
| `pgdbm-standalone` | Standalone service pattern | `/plugin install pgdbm-standalone@juanre-ai-tools` |
| `pgdbm-testing` | Database testing patterns | `/plugin install pgdbm-testing@juanre-ai-tools` |
| `pgdbm-usage` | Basic operations | `/plugin install pgdbm-usage@juanre-ai-tools` |
| `pgdbm-core-api` | Complete API reference | `/plugin install pgdbm-core-api@juanre-ai-tools` |
| `pgdbm-migrations-api` | Migrations API reference | `/plugin install pgdbm-migrations-api@juanre-ai-tools` |
| `pgdbm-common-mistakes` | Common pitfalls to avoid | `/plugin install pgdbm-common-mistakes@juanre-ai-tools` |

### llmemory (5 skills)
| Skill | Description | Install |
|-------|-------------|---------|
| `llmemory` | All llmemory skills | `/plugin install llmemory@juanre-ai-tools` |
| `llmemory-basic-usage` | Getting started | `/plugin install llmemory-basic-usage@juanre-ai-tools` |
| `llmemory-hybrid-search` | Vector + BM25 search | `/plugin install llmemory-hybrid-search@juanre-ai-tools` |
| `llmemory-multi-query` | Query expansion | `/plugin install llmemory-multi-query@juanre-ai-tools` |
| `llmemory-multi-tenant` | SaaS patterns | `/plugin install llmemory-multi-tenant@juanre-ai-tools` |
| `llmemory-rag` | Complete RAG systems | `/plugin install llmemory-rag@juanre-ai-tools` |

### llmring (6 skills)
| Skill | Description | Install |
|-------|-------------|---------|
| `llmring` | All llmring skills | `/plugin install llmring@juanre-ai-tools` |
| `llmring-chat` | Basic completions | `/plugin install llmring-chat@juanre-ai-tools` |
| `llmring-streaming` | Streaming responses | `/plugin install llmring-streaming@juanre-ai-tools` |
| `llmring-tools` | Function calling | `/plugin install llmring-tools@juanre-ai-tools` |
| `llmring-structured` | JSON schemas | `/plugin install llmring-structured@juanre-ai-tools` |
| `llmring-lockfile` | Configuration | `/plugin install llmring-lockfile@juanre-ai-tools` |
| `llmring-providers` | Multi-provider setup | `/plugin install llmring-providers@juanre-ai-tools` |

## Use Cases

### Build a SaaS Application

```bash
# Install all needed skills
/plugin install pgdbm@juanre-ai-tools
/plugin install llmemory@juanre-ai-tools
/plugin install llmring@juanre-ai-tools
```

**Then ask Claude:**
- "Create a FastAPI app with multi-tenant PostgreSQL"
- "Add document search with vector embeddings per customer"
- "Integrate OpenAI for chat with streaming responses"

Skills automatically guide you through best practices for each component!

### Build a RAG Chatbot

```bash
/plugin install llmemory@juanre-ai-tools
/plugin install llmring@juanre-ai-tools
```

**Then ask Claude:**
- "Set up hybrid search for product documentation"
- "Add multi-query expansion for better retrieval"
- "Integrate with Claude API for responses"

### Optimize Database Performance

```bash
/plugin install pgdbm@juanre-ai-tools
```

**Then ask Claude:**
- "Review my database setup for connection pooling"
- "Help me add migrations to my project"
- "Show me how to test database transactions"

## Why Use These Skills?

### Without Skills
❌ Generic database advice
❌ You have to explain the package API
❌ May suggest outdated patterns
❌ No awareness of package-specific features

### With Skills
✅ Specific to pgdbm/llmemory/llmring APIs
✅ Production-tested patterns
✅ Common pitfalls documented
✅ Best practices built-in
✅ Automatically activated when relevant

## Package Links

- **pgdbm** - [GitHub](https://github.com/juanre/pgdbm) | [PyPI](https://pypi.org/project/pgdbm/) | [Docs](https://github.com/juanre/pgdbm#readme)
- **llmemory** - [GitHub](https://github.com/juanre/llmemory) | [PyPI](https://pypi.org/project/llmemory/) | [Docs](https://github.com/juanre/llmemory#readme)
- **llmring** - [GitHub](https://github.com/juanre/llmring) | [PyPI](https://pypi.org/project/llmring/) | [Docs](https://github.com/juanre/llmring#readme)

## Requirements

- **Claude Code** installed and running
- **Python 3.9+** for the packages
- **PostgreSQL 14+** (for pgdbm and llmemory)

## Support & Community

- 💬 **Issues & Questions**: [Open an issue](https://github.com/juanre/ai-tools/issues)
- 🐛 **Bug Reports**: Report bugs in the specific package repository
- 💡 **Feature Requests**: Suggest improvements in package repos
- 📧 **Contact**: [[email protected]](mailto:[email protected])

## Contributing

Skills are maintained in each package repository:
- pgdbm skills: [pgdbm/.claude/skills/](https://github.com/juanre/pgdbm/tree/main/.claude/skills)
- llmemory skills: [llmemory/.claude/skills/](https://github.com/juanre/llmemory/tree/main/.claude/skills)
- llmring skills: [llmring/.claude/skills/](https://github.com/juanre/llmring/tree/main/.claude/skills)

To contribute:
1. Fork the package repository
2. Improve or add skills in `.claude/skills/`
3. Test with Claude Code
4. Submit a pull request

## License

All packages and skills are released under the MIT License.

## About the Author

**Juan Reyero** is a software engineer with 30+ years of experience in engineering leadership and technical innovation. CTO at Quantica and previously senior technical roles at Hewlett-Packard and Xaar, Juan has extensive experience building production systems and developer tools.

- GitHub: [@juanre](https://github.com/juanre)
- Website: [juanreyero.com](https://juanreyero.com)
- Email: [email protected]

## Acknowledgments

Thanks to:
- **Anthropic** for creating Claude Code and the skills system
- **The Claude Code community** for feedback and contributions
- **Early adopters** who helped refine these skills

---

**Made with ❤️ for the AI development community**

*Last updated: January 2026*
