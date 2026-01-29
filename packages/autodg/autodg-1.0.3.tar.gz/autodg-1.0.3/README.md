# AutoDG (Automated Documentation Generator) 💎

[![PyPI version](https://badge.fury.io/py/autodg.svg)](https://pypi.org/project/autodg/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python Support](https://img.shields.io/badge/python-3.11%20%7C%203.12-blue.svg)](https://pypi.org/project/autodg/)

**AutoDG** is a premium, AI-driven documentation generator for Python API projects. It performs deep static and dynamic code analysis to transform complex backends into clear, actionable, and visually rich documentation.

---

## 🚀 Core Capabilities

### 1. Multi-Dimensional Documentation
- **API Request Documentation**: Detailed technical specs for every endpoint, including headers, parameters, and handler logic.
- **File-wise Intelligence**: Comprehensive AI-generated overviews of every Python module in your project.
- **Visual Call Graphs**: Mermaid.js diagrams showing cross-functional dependencies.
- **Database Mapping**: Visualizes database operations and relationships per endpoint.

### 2. AI Auditing & Insights
- **Security Audit**: Identifies SQL injection, XSS, and authentication vulnerabilities.
- **Efficiency Analysis**: Detects N+1 query patterns and performance bottlenecks.
- **Code Suggestions**: Provides line-by-line quality and refactoring recommendations.

### 3. Business & Operational Suites
- **Feature Map & User Stories**: Translates code into human-readable business features and requirements.
- **DevOps Playbooks**: Auto-generates Scaling Guides and Deployment (Docker/CI-CD) documentation.
- **Automated Changelog**: Generates a technical summary of project state and architectural evolution.

### 4. Enterprise-Grade UX
- **Live Flight Plan**: Transparent dashboard summary before analysis begins.
- **Dynamic Progress**: Real-time progress bars with ETAs for long-running AI tasks.
- **Robust Logging**: Detailed execution audit trails in `aidocs_generation.log`.
- **Framework Support**: Native compatibility with **FastAPI**, **Flask**, **Django**, and **DRF**.

---

## ⚙️ Installation

```bash
pip install autodg
```

### Enable AI Cloud Providers
To use cloud LLMs, install the corresponding extras:

```bash
pip install autodg[openai]   # OpenAI (GPT-4)
pip install autodg[claude]   # Anthropic (Claude 3.5)
pip install autodg[gemini]   # Google (Gemini 1.5)
pip install autodg[all]      # All-in-one installation
```

---

## 🛠 Usage Guide

### Simple Static Analysis
Generates technical docs without AI costs:
```bash
autodg --paths /path/to/project --output ./docs
```

### Full AI Suite (Recommended)
Generates the complete documentation package using a local Ollama instance:
```bash
autodg --paths /path/to/project \
       --output ./docs \
       --ollama true \
       --gen-features \
       --gen-devops \
       --gen-changelog
```

### Advanced CLI Options

| Flag | Values | Description |
|------|--------|-------------|
| `--paths` | `path` | **Required**. Path to your source code root. |
| `--output` | `path` | Output directory (default: `output`). |
| `--doc-type`| `request`, `file`, `both` | Choose between API docs, File overviews, or both. |
| `--ollama` | `true`, `false` | Enable AI-powered auditing and explanations. |
| `--gen-features`| `flag` | Generate Feature Map & User Stories. |
| `--gen-devops` | `flag` | Generate Scaling & Deployment Guides. |
| `--gen-changelog`| `flag` | Generate AI-driven project changelog. |

---

## 📝 Configuration (`config.yaml`)

To use cloud providers or customize your local LLM, create a `config.yaml` in your project root:

```yaml
llm:
  provider: ollama  # Options: ollama, openai, claude, gemini
  
  ollama:
    host: http://localhost:11434
    model: llama3.1
    
  openai:
    api_key: "your-key-here"
    model: "gpt-4-turbo"
```

---

## 📂 Artifact Hierarchy

Your `output/` directory will contain:

- **`request_docs/`**: Technical specs for every API route.
- **`file_docs/`**: AI overviews for every codebase file.
- **`features_and_stories.md`**: Business requirements mapping.
- **`scaling_guide.md`**: infrastructure scaling strategies.
- **`deployment_guide.md`**: CI/CD and containerization plans.
- **`changelog.md`**: Architectural state summary.
- **`aidocs_generation.log`**: Detailed audit trail of the generation process.

---

## 📄 License
MIT License - see [LICENSE](LICENSE) for details.

## ✍️ Author
Dhinagaran S ([atsupp02@gmail.com](mailto:atsupp02@gmail.com))
