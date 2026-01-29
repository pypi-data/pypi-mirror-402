#!/bin/bash
# this_file: examples/config_setup.sh

# Setup and configure abersetz with various engines

set -e

echo "=== Abersetz Configuration Setup ==="
echo ""

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to setup environment variable
setup_env_var() {
    local var_name=$1
    local var_description=$2

    if [ -z "${!var_name:-}" ]; then
        echo "⚠ $var_name not set"
        echo "  Description: $var_description"
        echo "  To set: export $var_name='your_api_key_here'"
        return 1
    else
        echo "✓ $var_name is configured"
        return 0
    fi
}

# Check abersetz installation
echo "Checking installation..."
if command_exists abersetz; then
    echo "✓ abersetz is installed"
    abersetz version
else
    echo "✗ abersetz not found. Install with: pip install abersetz"
    exit 1
fi

echo ""

# Show config location
echo "Configuration location:"
abersetz config path
echo ""

# Check API keys for various engines
echo "Checking API keys for LLM engines:"
echo ""

setup_env_var "OPENAI_API_KEY" "OpenAI API for GPT models"
setup_env_var "ANTHROPIC_API_KEY" "Anthropic API for Claude models"
setup_env_var "SILICONFLOW_API_KEY" "SiliconFlow API for Hunyuan translation"
setup_env_var "DEEPSEEK_API_KEY" "DeepSeek API for Chinese models"
setup_env_var "GROQ_API_KEY" "Groq API for fast inference"
setup_env_var "GOOGLE_API_KEY" "Google API for Gemini models"

echo ""

# Test available engines
echo "Testing available engines:"
echo ""

# Test free engines (no API key required)
echo "1. Testing free engines..."
for engine in "tr/google" "tr/bing" "dt/google"; do
    echo -n "  $engine: "
    if echo "Hello" | abtr es - --engine "$engine" --dry-run >/dev/null 2>&1; then
        echo "✓"
    else
        echo "✗"
    fi
done

echo ""

# Create sample configuration
CONFIG_FILE="$HOME/.config/abersetz/config.toml"
if [ ! -f "$CONFIG_FILE" ]; then
    echo "Creating default configuration..."
    mkdir -p "$(dirname "$CONFIG_FILE")"
    cat > "$CONFIG_FILE" <<'EOF'
[defaults]
engine = "tr/google"
from_lang = "auto"
to_lang = "en"
chunk_size = 1200
html_chunk_size = 1800

[credentials.openai]
env = "OPENAI_API_KEY"

[credentials.anthropic]
env = "ANTHROPIC_API_KEY"

[credentials.siliconflow]
env = "SILICONFLOW_API_KEY"

[credentials.deepseek]
env = "DEEPSEEK_API_KEY"

[credentials.groq]
env = "GROQ_API_KEY"

[credentials.google]
env = "GOOGLE_API_KEY"

[engines.hysf]
chunk_size = 2400

[engines.hysf.credential]
name = "siliconflow"

[engines.hysf.options]
model = "tencent/Hunyuan-MT-7B"
base_url = "https://api.siliconflow.com/v1"
temperature = 0.3

[engines.ullm]
chunk_size = 2400

[engines.ullm.options.profiles.default]
base_url = "https://api.siliconflow.com/v1"
model = "tencent/Hunyuan-MT-7B"
credential = { name = "siliconflow" }
temperature = 0.3
max_input_tokens = 32000

[engines.ullm.options.profiles.gpt4]
base_url = "https://api.openai.com/v1"
model = "gpt-4-turbo-preview"
credential = { name = "openai" }
temperature = 0.3
max_input_tokens = 128000

[engines.ullm.options.profiles.claude]
base_url = "https://api.anthropic.com/v1"
model = "claude-3-opus-20240229"
credential = { name = "anthropic" }
temperature = 0.3
max_input_tokens = 200000

[engines.ullm.options.profiles.deepseek]
base_url = "https://api.deepseek.com/v1"
model = "deepseek-chat"
credential = { name = "deepseek" }
temperature = 0.3
max_input_tokens = 32000
EOF
    echo "✓ Configuration created at $CONFIG_FILE"
else
    echo "Configuration already exists at $CONFIG_FILE"
fi

echo ""

# Show current configuration
echo "Current configuration:"
abersetz config show | head -20
echo "..."

echo ""
echo "=== Setup Complete ==="
echo ""
echo "Quick test commands:"
echo "  abersetz tr es test.txt                    # Use default engine"
echo "  abtr fr test.txt --engine tr/bing # Use Bing"
echo "  abtr de test.txt --engine hy             # Use SiliconFlow LLM"
echo "  abtr ja test.txt --engine ullm/gpt4        # Use GPT-4"
