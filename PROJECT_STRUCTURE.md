# 📁 Causal Memory Core - Project Structure

This document provides a comprehensive overview of the project organization and file structure for the Causal Memory Core repository.

## 🏗️ Repository Layout

```
Causal-Memory-Core/
├── 📄 README.md                          # Main project documentation
├── 📄 LICENSE                            # MIT License
├── 📄 CHANGELOG.md                       # Version history and changes
├── 📄 CONTRIBUTING.md                    # Contribution guidelines
├── 📄 PROJECT_STRUCTURE.md               # This file
├── 📄 .gitignore                         # Git ignore patterns
├── 📄 .env.template                      # Environment variables template
├── 📄 requirements.txt                   # Python dependencies
├── 📄 requirements-dev.txt               # Development dependencies
├── 📄 setup.py                           # Package setup configuration
├── 📄 pyproject.toml                     # Modern Python project config
├── 📄 Dockerfile                         # Container deployment
├── 📄 docker-compose.yml                 # Multi-container setup
│
├── 📂 .github/                           # GitHub-specific files
│   ├── 📂 workflows/                     # CI/CD automation
│   │   ├── ci.yml                        # Main CI/CD pipeline
│   │   ├── security.yml                  # Security scanning
│   │   └── release.yml                   # Release automation
│   ├── 📂 ISSUE_TEMPLATE/                # Issue templates
│   │   ├── bug_report.md                 # Bug report template
│   │   ├── feature_request.md            # Feature request template
│   │   └── question.md                   # Question template
│   ├── 📂 PULL_REQUEST_TEMPLATE/         # PR templates
│   │   └── pull_request_template.md      # Standard PR template
│   ├── CODEOWNERS                        # Code ownership rules
│   ├── copilot-instructions.md           # AI assistant guidelines
│   └── dependabot.yml                    # Dependency updates
│
├── 📂 src/                               # Main source code
│   ├── 🐍 __init__.py                    # Package initialization
│   ├── 🐍 memory_core.py                 # Core memory system interface
│   ├── 🐍 causal_engine.py               # Causal relationship analysis
│   ├── 🐍 semantic_search.py             # Semantic search functionality
│   ├── 🐍 mcp_server.py                  # MCP protocol server
│   ├── 🐍 config.py                      # Configuration management
│   ├── 🐍 cli.py                         # Command-line interface
│   ├── 🐍 api_server.py                  # REST API server
│   ├── 🐍 example_usage.py               # Usage examples
│   │
│   ├── 📂 models/                        # Data models and schemas
│   │   ├── 🐍 __init__.py                
│   │   ├── 🐍 event.py                   # Event data models
│   │   ├── 🐍 relationship.py            # Causal relationship models
│   │   ├── 🐍 query.py                   # Query and response models
│   │   └── 🐍 config_models.py           # Configuration models
│   │
│   ├── 📂 utils/                         # Utility modules
│   │   ├── 🐍 __init__.py                
│   │   ├── 🐍 database.py                # Database operations
│   │   ├── 🐍 embeddings.py              # Embedding generation
│   │   ├── 🐍 validation.py              # Input validation
│   │   ├── 🐍 logging.py                 # Logging utilities
│   │   ├── 🐍 profiler.py                # Performance profiling
│   │   └── 🐍 security.py                # Security utilities
│   │
│   ├── 📂 integrations/                  # External integrations
│   │   ├── 🐍 __init__.py                
│   │   ├── 🐍 openai_client.py           # OpenAI API integration
│   │   ├── 🐍 mcp_client.py              # MCP client utilities
│   │   └── 🐍 webhook_handlers.py        # Webhook integrations
│   │
│   └── 📂 web/                           # Web interface (optional)
│       ├── 🐍 __init__.py                
│       ├── 🐍 app.py                     # Web application
│       ├── 📂 templates/                 # HTML templates
│       ├── 📂 static/                    # Static assets
│       └── 📂 api/                       # API routes
│
├── 📂 tests/                             # Test suite
│   ├── 🐍 __init__.py                    
│   ├── 🐍 conftest.py                    # Pytest configuration
│   ├── 🐍 test_memory_core.py            # Core functionality tests
│   ├── 🐍 test_causal_engine.py          # Causal analysis tests
│   ├── 🐍 test_semantic_search.py        # Search functionality tests
│   ├── 🐍 test_config.py                 # Configuration tests
│   ├── 🐍 test_cli.py                    # CLI interface tests
│   │
│   ├── 📂 integration/                   # Integration tests
│   │   ├── 🐍 __init__.py                
│   │   ├── 🐍 test_database_ops.py       # Database integration
│   │   ├── 🐍 test_openai_integration.py # OpenAI API integration
│   │   └── 🐍 test_mcp_integration.py    # MCP protocol tests
│   │
│   ├── 📂 e2e/                           # End-to-end tests
│   │   ├── 🐍 __init__.py                
│   │   ├── 🐍 test_complete_workflow.py  # Full workflow tests
│   │   ├── 🐍 test_api_endpoints.py      # REST API tests
│   │   └── 🐍 test_mcp_server.py         # MCP server tests
│   │
│   ├── 📂 performance/                   # Performance tests
│   │   ├── 🐍 __init__.py                
│   │   ├── 🐍 test_load_testing.py       # Load testing
│   │   ├── 🐍 test_benchmarks.py         # Performance benchmarks
│   │   └── 🐍 test_memory_usage.py       # Memory usage tests
│   │
│   └── 📂 fixtures/                      # Test data and fixtures
│       ├── 📄 sample_events.json         # Sample event data
│       ├── 📄 test_database.db           # Test database
│       └── 📂 mock_responses/             # Mock API responses
│
├── 📂 docs/                              # Documentation
│   ├── 📄 index.md                       # Documentation home
│   ├── 📄 architecture.md                # System architecture
│   ├── 📄 api.md                         # API documentation
│   ├── 📄 configuration.md               # Configuration guide
│   ├── 📄 testing.md                     # Testing guide
│   ├── 📄 deployment.md                  # Deployment guide
│   ├── 📄 mcp-integration.md             # MCP integration guide
│   ├── 📄 troubleshooting.md             # Common issues and solutions
│   │
│   ├── 📂 examples/                      # Code examples
│   │   ├── 📄 basic_usage.md             # Basic usage examples
│   │   ├── 📄 advanced_queries.md        # Advanced query examples
│   │   ├── 📄 integration_patterns.md    # Integration patterns
│   │   └── 📄 custom_configurations.md   # Custom config examples
│   │
│   ├── 📂 diagrams/                      # Architecture diagrams
│   │   ├── 🖼️ system_overview.png        # System overview
│   │   ├── 🖼️ data_flow.png              # Data flow diagram
│   │   └── 🖼️ component_diagram.png      # Component relationships
│   │
│   └── 📂 api-specs/                     # API specifications
│       ├── 📄 openapi.yaml               # OpenAPI specification
│       └── 📄 mcp-schema.json            # MCP tool schemas
│
├── 📂 scripts/                           # Utility scripts
│   ├── 🐍 setup_dev_env.py               # Development environment setup
│   ├── 🐍 run_comprehensive_tests.py     # Test runner
│   ├── 🐍 generate_docs.py               # Documentation generator
│   ├── 🐍 migrate_database.py            # Database migration
│   ├── 🐍 benchmark_performance.py       # Performance benchmarking
│   └── 🐍 export_data.py                 # Data export utilities
│
├── 📂 config/                            # Configuration files
│   ├── 📄 default.yaml                   # Default configuration
│   ├── 📄 development.yaml               # Development settings
│   ├── 📄 production.yaml                # Production settings
│   ├── 📄 testing.yaml                   # Test environment settings
│   └── 📄 logging.yaml                   # Logging configuration
│
├── 📂 data/                              # Data files (not in version control)
│   ├── 📄 memory.db                      # Main database file
│   ├── 📂 backups/                       # Database backups
│   ├── 📂 exports/                       # Data exports
│   └── 📂 cache/                         # Temporary cache files
│
├── 📂 docker/                            # Docker configuration
│   ├── 📄 Dockerfile.dev                 # Development container
│   ├── 📄 Dockerfile.prod                # Production container
│   ├── 📄 docker-compose.dev.yml         # Development compose
│   └── 📄 docker-compose.prod.yml        # Production compose
│
└── 📂 tools/                             # Development tools
    ├── 🐍 code_formatter.py              # Code formatting
    ├── 🐍 dependency_checker.py          # Dependency analysis
    ├── 🐍 security_scanner.py            # Security scanning
    └── 🐍 release_helper.py              # Release automation
```

## 📋 File Categories

### 🔧 Core Application Files

| File | Purpose | Key Features |
|------|---------|--------------|
| `src/memory_core.py` | Main system interface | Event storage, context retrieval |
| `src/causal_engine.py` | Causal analysis | Relationship detection, confidence scoring |
| `src/semantic_search.py` | Search functionality | Vector search, similarity matching |
| `src/mcp_server.py` | MCP protocol server | Tool integration, async handling |

### 🎯 Configuration & Setup

| File | Purpose | Key Features |
|------|---------|--------------|
| `config.py` | System configuration | Environment management, defaults |
| `.env.template` | Environment template | Required variables, examples |
| `requirements.txt` | Dependencies | Production packages |
| `requirements-dev.txt` | Dev dependencies | Testing, linting, development tools |

---

This structure provides a comprehensive, scalable foundation for the Causal Memory Core project while maintaining clear organization and professional development practices.