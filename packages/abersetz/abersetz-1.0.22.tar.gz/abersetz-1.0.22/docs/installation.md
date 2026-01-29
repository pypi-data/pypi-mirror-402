---
layout: default
title: Installation
nav_order: 2
---

# Installation
{: .no_toc }

## Table of contents
{: .no_toc .text-delta }

1. TOC
{:toc}

---

## Requirements

- Python 3.10 or higher  
- pip or uv package manager  

## Installing with pip

The simplest way to install abersetz:

```bash
pip install abersetz
```

## Installing with uv

If you prefer the modern uv package manager:

```bash
uv pip install abersetz
```

## Installing from source

To install the latest development version:

```bash
git clone https://github.com/twardoch/abersetz.git
cd abersetz
pip install -e .
```

## Verifying installation

After installation, verify abersetz is working:

```bash
# Check version
abersetz version

# Show help
abersetz --help

# Test with dry run
echo "Hello world" > test.txt
abersetz tr es test.txt --dry-run
```

## Dependencies

Abersetz automatically installs these dependencies:

### Core dependencies
- **translators** (>=5.9): Multiple free translation APIs  
- **deep-translator** (>=1.11): Alternative translation providers  
- **openai** (>=1.51): LLM-based translation engines  
- **tenacity** (>=8.4): Retry logic for API calls  

### Utility dependencies
- **fire** (>=0.5): CLI interface generation  
- **rich** (>=13.9): Terminal formatting  
- **loguru** (>=0.7): Structured logging  
- **platformdirs** (>=4.3): Cross-platform config paths  
- **semantic-text-splitter** (>=0.7): Intelligent text chunking  

## Optional: Setting up API keys

For LLM-based translation engines, you’ll need API keys:

```bash
# OpenAI GPT models
export OPENAI_API_KEY="sk-..."

# Anthropic Claude models
export ANTHROPIC_API_KEY="sk-ant-..."

# SiliconFlow (Hunyuan translator)
export SILICONFLOW_API_KEY="sk-..."

# Google Gemini
export GOOGLE_API_KEY="..."

# Add to your shell profile to persist
echo 'export OPENAI_API_KEY="sk-..."' >> ~/.bashrc
```

## Shell completion (optional)

Enable tab completion for bash:

```bash
# Generate completion script
python -c "import fire; fire.Fire()" -- --completion > ~/.abersetz-completion.bash

# Add to bashrc
echo "source ~/.abersetz-completion.bash" >> ~/.bashrc

# Reload shell
source ~/.bashrc
```

## Docker installation (alternative)

Run abersetz in a container:

```dockerfile
FROM python:3.12-slim

RUN pip install abersetz

WORKDIR /data

ENTRYPOINT ["abersetz"]
```

Build and use:

```bash
docker build -t abersetz .
docker run -v $(pwd):/data abersetz tr es /data/file.txt
```

## Troubleshooting

### Command not found

If `abersetz` isn't found after installation:

1. Check where pip installed it:
   ```bash
   pip show -f abersetz | grep Location
   ```

2. Make sure the scripts directory is in your PATH:
   ```bash
   export PATH="$HOME/.local/bin:$PATH"
   ```

### Permission denied

On Linux or macOS, you might need to make the script executable:

```bash
chmod +x ~/.local/bin/abersetz
chmod +x ~/.local/bin/abtr
```

### SSL certificate errors

If you hit SSL errors during API calls:

```bash
# Update certificates
pip install --upgrade certifi

# Or disable SSL verification (not recommended)
export CURL_CA_BUNDLE=""
```

## Next steps

- [Configure abersetz](configuration/)  
- [Learn CLI commands](cli/)  
- [Explore