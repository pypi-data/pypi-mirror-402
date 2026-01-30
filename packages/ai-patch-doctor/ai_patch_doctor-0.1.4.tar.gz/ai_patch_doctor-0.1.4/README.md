# AI Patch Doctor 🔍⚕️

**Fix AI API issues in under 60 seconds - diagnose streaming, retries, cost, and traceability problems**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)

AI Patch Doctor is a command-line tool that helps developers diagnose and fix common AI API issues quickly. It provides interactive diagnostics for OpenAI, Anthropic Claude, Google Gemini, and any OpenAI-compatible API.

## 🚀 Quick Start

```bash
# Using pipx (recommended)
pipx run ai-patch doctor

# Or with pip
pip install ai-patch
ai-patch doctor
```

## ✨ Key Features

- **4 Core Diagnostics**: Streaming, Retries, Cost, and Traceability checks
- **Multi-Provider Support**: OpenAI, Anthropic, Gemini, and OpenAI-compatible APIs
- **Interactive Mode**: Simple 2-question flow to get started
- **Auto-Detection**: Automatically detects API configuration from environment
- **Detailed Reports**: JSON and Markdown reports with specific fix recommendations

## 🔬 What It Checks

1. **Streaming Check** - SSE stalls, buffering issues, partial output problems
2. **Retries Check** - Rate limit storms, retry chaos, exponential backoff
3. **Cost Check** - Token spikes, unbounded requests, cost optimization
4. **Traceability Check** - Request IDs, correlation tracking, duplicate detection

## 💻 Usage

```bash
# Interactive mode (recommended)
ai-patch doctor

# Run specific check
ai-patch doctor --target=streaming

# Run all checks
ai-patch doctor --target=all
```

## 📖 Full Documentation

For complete documentation, examples, and advanced usage, visit:
- **GitHub Repository**: [github.com/michaelbrinkworth/ai-patch-doctor](https://github.com/michaelbrinkworth/ai-patch-doctor)
- **Issue Tracker**: [github.com/michaelbrinkworth/ai-patch-doctor/issues](https://github.com/michaelbrinkworth/ai-patch-doctor/issues)

## 📄 License

MIT License - see [LICENSE](https://github.com/michaelbrinkworth/ai-patch-doctor/blob/main/LICENSE) file for details.

---

**Run the doctor. Fix your AI API. ⚕️**
