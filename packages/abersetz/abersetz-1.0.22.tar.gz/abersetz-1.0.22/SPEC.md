Here's the edited version of your technical specification, with all the facts and functionality preserved but the language tightened, cleaned up, and made more direct:

---

# Abersetz Technical Specification

## 1. Overview

`abersetz` is a Python package and command-line tool for translating file contents. It works by identifying files, splitting their content into chunks, translating those chunks, and reassembling them into translated files.

## 2. Core Functionality

### 2.1. File Handling

- **Input:** Accepts a path to either a single file or a directory.
- **File Discovery:** If given a directory, recursively finds files to translate. Controlled by the `--recurse` flag.
- **Output:** Two modes supported:
  - Save translated files in a specified output directory, preserving the source directory structure.
  - Overwrite original files with translated content using the `--write_over` flag.

### 2.2. Translation Pipeline

Translation follows these steps:

1. **Locate:** Identify files based on input path and recursion settings.
2. **Chunk:** Split each file’s content into smaller pieces suitable for the translation engine.
3. **Translate:** Send chunks to the selected translation engine.
4. **Merge:** Reassemble translated chunks into full file content.
5. **Save:** Write the result to the destination.

### 2.3. Content-Type Detection

- Automatically detects HTML content and processes it in a way that preserves markup during translation.

## 3. Translation Engines

Supports multiple translation engines.

### 3.1. Pre-integrated Engines

- Integrates with `translators` and `deep-translator`, allowing use of any of their supported services (e.g., `google`, `bing`, `deepl`).

### 3.2. Custom LLM-based Engines

#### 3.2.1. `hysf` Engine

- **Provider:** Siliconflow  
- **Model:** `tencent/Hunyuan-MT-7B`  
- **Implementation:** Uses the `openai` package to call the Siliconflow API endpoint: `https://api.siliconflow.com/v1/chat/completions`  
- **Authentication:** Pulls API key from configuration  
- **Resilience:** API calls include retry logic via `tenacity`

#### 3.2.2. `ullm` (Universal Large Language Model) Engine

- **Configurability:** Fully configurable per provider. Each profile includes:
  - API base URL  
  - Model name  
  - API key or environment variable reference  
  - Temperature  
  - Chunk size  
  - Maximum input token length  

- **voc Management:**
  - First chunk can include a "prolog" containing a JSON object of predefined vocabulary (`voc`)
  - Prompt instructs the LLM to return translation inside `<output>` tags
  - Optionally, the LLM may return updated vocabulary in `<voc>` tags
  - Tool parses returned `<voc>`, merges it with existing terms, and passes updated voc to subsequent chunks

- **voc Persistence:**
  - `--save-voc` flag saves merged vocabulary as a JSON file alongside the translated output

## 4. Configuration

- Stored in a user-specific directory using `platformdirs`
- API keys are stored securely, either directly or via environment variable names
- Supports engine-specific settings like chunk sizes

## 5. Command-Line Interface (CLI)

- Built using `python-fire`
- Main command: `translate`

### CLI Arguments

- `path`: Input file or directory
- `--from-lang`: Source language (default: `auto`)
- `--to-lang`: Target language (default: `en`)
- `--engine`: Translation engine to use
- `--recurse` / `--no-recurse`: Enable or disable recursive file discovery
- `--write_over`: Overwrite original files instead of saving to output directory
- `--output`: Directory to save translated files
- `--save-voc`: Save vocabulary file

## 6. Python API

- Provides programmatic access for integration into other Python projects

## 7. Dependencies

- `translators`  
- `deep-translator`  
- `openai`  
- `tenacity`  
- `platformdirs`  
- `python-fire`  
- `semantic-text-splitter` (or equivalent for chunking)

--- 

Let me know if you'd like this formatted for markdown or rendered as plain text.