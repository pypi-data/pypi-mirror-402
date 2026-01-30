# icon-gen-ai

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![PyPI version](https://img.shields.io/pypi/v/icon-gen-ai?color=blue&label=PyPI)](https://pypi.org/project/icon-gen-ai/)
[![Tests](https://github.com/yauheniya-ai/icon-gen-ai/actions/workflows/tests.yml/badge.svg)](https://github.com/yauheniya-ai/icon-gen-ai/actions/workflows/tests.yml)
[![Coverage](https://img.shields.io/endpoint?url=https://gist.githubusercontent.com/yauheniya-ai/0c3d87e9fd5394624952e6402af9b08e/raw/coverage.json)](https://github.com/yauheniya-ai/icon-gen-ai/actions/workflows/tests.yml)
[![GitHub last commit](https://img.shields.io/github/last-commit/yauheniya-ai/icon-gen)](https://github.com/yauheniya-ai/icon-gen/commits/main)
[![Downloads](https://pepy.tech/badge/icon-gen-ai)](https://pepy.tech/project/icon-gen-ai)

Generate pixel-perfect icons from Iconify, direct URLs, and local files—with animation support and exports to PNG, SVG, WebP, and ICO.

<div align="center">
  <img src="https://raw.githubusercontent.com/yauheniya-ai/icon-gen-ai/main/docs/icon_gen_ai-demo.webp" width="100%" alt="Playground Demo">
  <br><sub>
    <a href="https://yauheniya-ai.github.io/icon-gen-ai/" target="_blank" rel="noopener noreferrer">Read the Documentation</a> • <a href="https://yauheniya-ai.github.io/icon-gen-ai-playground/" target="_blank" rel="noopener noreferrer">Try the Interactive Playground</a>

  </sub>
</div>

## Features

<img src="https://raw.githubusercontent.com/yauheniya-ai/icon-gen-ai/main/output/feat_ai.svg" height="16px"> AI-assisted icon search and generation  
<img src="https://raw.githubusercontent.com/yauheniya-ai/icon-gen-ai/main/output/feat_python.svg" height="16px"> Simple and intuitive CLI and Python API  
<img src="https://raw.githubusercontent.com/yauheniya-ai/icon-gen-ai/main/output/feat_iconify.svg" height="16px"> Access 275,000+ icons from Iconify  
<img src="https://raw.githubusercontent.com/yauheniya-ai/icon-gen-ai/main/output/feat_image.svg" height="16px"> Unlimited icons from direct URLs or local files  
<img src="https://raw.githubusercontent.com/yauheniya-ai/icon-gen-ai/main/output/feat_customize.svg" height="16px"> Customize colors, sizes, and backgrounds and adjust border radius  
<img src="https://raw.githubusercontent.com/yauheniya-ai/icon-gen-ai/main/output/feat_gradient.svg" height="16px"> Gradient color option for icons and backgrounds  
<img src="https://raw.githubusercontent.com/yauheniya-ai/icon-gen-ai/main/output/feat_save.svg" height="16px"> Export to SVG, PNG, WEBP, or ICO format  

## Installation

```bash
pip install icon-gen-ai
```

**(Optional) AI features**: 
```bash
pip install icon-gen-ai[ai]
```

After installing AI features, configure at least one API key:
- **OpenAI**: Set `OPENAI_API_KEY` environment variable
- **Anthropic**: Set `ANTHROPIC_API_KEY` environment variable  
- **Hugging Face**: Set `HF_TOKEN` environment variable

Check provider status:
```bash
icon-gen-ai providers
```

## Quick Start

### Generate Single Icons

```python
from icon_gen_ai import IconGenerator

generator = IconGenerator(output_dir="output")

# From URL
generator.generate_icon(
    direct_url='https://upload.wikimedia.org/wikipedia/commons/b/b0/Claude_AI_symbol.svg',
    output_name='claude_white_mediumslateblue_bg',
    color='white',
    bg_color='mediumslateblue',
    border_radius=0,
    size=256
)

# From Iconify
generator.generate_icon(
    icon_name='simple-icons:googlegemini',
    output_name='gemini_white_deeppink_bg',
    color='white',
    bg_color='deeppink',
    border_radius=128,  # Circle (half of size)
    size=256
)

# From Iconify 
generator.generate_icon(
    icon_name='simple-icons:mistralai',
    output_name='mistral_white_gradient_bg',
    color='white',
    bg_color=('mediumslateblue', 'deeppink'),  # Gradient
    direction="vertical",
    border_radius=48,
    size=256
)

# From Iconify 
generator.generate_icon(
    icon_name='simple-icons:openai',
    output_name='openai_gradient_transparent_bg',
    color=('mediumslateblue', 'deeppink'),  # Gradient icon
    direction="diagonal",
    bg_color=None,
    size=256
)
```

<div align="center">
  <img src="https://raw.githubusercontent.com/yauheniya-ai/icon-gen-ai/main/output/claude_white_mediumslateblue_bg.svg" width="40" alt="Claude">
  <img src="data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7" width="10" height="1" alt="">
  <img src="https://raw.githubusercontent.com/yauheniya-ai/icon-gen-ai/main/output/gemini_white_deeppink_bg.svg" width="40" alt="Gemini">
  <img src="data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7" width="10" height="1" alt="">
  <img src="https://raw.githubusercontent.com/yauheniya-ai/icon-gen-ai/main/output/mistral_white_gradient_bg.svg" width="40" alt="Mistral">
  <img src="data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7" width="10" height="1" alt="">
  <img src="https://raw.githubusercontent.com/yauheniya-ai/icon-gen-ai/main/output/openai_gradient_transparent_bg.svg" width=40" alt="OpenAI">
</div>

### Generate Multiple Icons (Batch)

```python
from icon_gen_ai import IconGenerator

generator = IconGenerator(output_dir="output")

# Generate multiple icons at once
ai_icons = {
    'llama_deepskyblue': 'simple-icons:meta',
    'deepseek_deepskyblue': {
        'local_file': 'input/deepseek-icon.png'
    },
    'nemotron_deepskyblue': {
        'url': 'https://companieslogo.com/img/orig/NVDA-df4c2377.svg'
    },
    'grok_deepskyblue': {
        'url': 'https://unpkg.com/@lobehub/icons-static-svg@latest/icons/grok.svg'
    }
}

generator.generate_batch(ai_icons, color='deepskyblue', size=256, outline_color='deepskyblue', outline_width=8, border_radius=48)
```

<div align="center">
  <img src="https://raw.githubusercontent.com/yauheniya-ai/icon-gen-ai/main/output/llama_deepskyblue.svg" width="40" alt="Llama">
  <img src="data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7" width="10" height="1" alt="">
  <img src="https://raw.githubusercontent.com/yauheniya-ai/icon-gen-ai/main/output/deepseek_deepskyblue.svg" width="40" alt="DeepSeek">
  <img src="data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7" width="10" height="1" alt="">
  <img src="https://raw.githubusercontent.com/yauheniya-ai/icon-gen-ai/main/output/nemotron_deepskyblue.svg" width="40" alt="Nemotron">
  <img src="data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7" width="10" height="1" alt="">
  <img src="https://raw.githubusercontent.com/yauheniya-ai/icon-gen-ai/main/output/grok_deepskyblue.svg" width="40" alt="Grok">
</div>

### Create Custom Animations

You can add four types of animations to the SVG icons: spin, pulse, flip horizontally, and flip vertically.

```python
from icon_gen_ai import IconGenerator

generator = IconGenerator(output_dir="output")

icons_with_custom_ani = {
    f'disk': {'icon':'qlementine-icons:disk-16',"animation":"spin:4s"},
    f'cicle': {'icon':'clarity:dot-circle-line',"animation":"pulse:1s"},
    f'coffee': {'icon':'gg:coffee',"animation":"flip-h:1s"},
    f'card': {'icon':'famicons:card-outline',"animation":"flip-v:1s"},
}

generated = generator.generate_batch(
    icons_with_custom_ani, 
    color='white', 
    size=256,  
    bg_color=('deeppink','mediumslateblue'), 
    border_radius=48)
```


<div align="center">
  <img src="https://raw.githubusercontent.com/yauheniya-ai/icon-gen-ai/main/output/ani_custom_disk.svg" width="40" alt="Spinning Disk">
  <img src="data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7" width="10" height="1" alt="">
  <img src="https://raw.githubusercontent.com/yauheniya-ai/icon-gen-ai/main/output/ani_custom_circle.svg" width="40" alt="Pulsating Circle">
  <img src="data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7" width="10" height="1" alt="">
  <img src="https://raw.githubusercontent.com/yauheniya-ai/icon-gen-ai/main/output/ani_custom_coffee.svg" width="40" alt="Flipping Coffee">
  <img src="data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7" width="10" height="1" alt="">
  <img src="https://raw.githubusercontent.com/yauheniya-ai/icon-gen-ai/main/output/ani_custom_card.svg" width="40" alt="Flipping Card">
</div>

### Support for Embedded Animations

When you apply a solid color to an animated SVG icon, the animations are automatically preserved:


```python
from icon_gen_ai import IconGenerator

generator = IconGenerator(output_dir="output")

color = 'mediumslateblue' 

animated_icons = {
    f'ani_embedded_blocks': 'svg-spinners:blocks-wave',
    f'ani_embedded_upload': 'line-md:upload-outline-loop',
    f'ani_embedded_location': 'line-md:my-location-loop',
    f'ani_embedded_bars': 'svg-spinners:bars-scale-middle'
}

generator.generate_batch(animated_icons, color=color, size=256, outline_color='springgreen', bg_color='snow', outline_width=8, border_radius=48)
```

<div align="center">
  <img src="https://raw.githubusercontent.com/yauheniya-ai/icon-gen-ai/main/output/ani_embedded_blocks.svg" width="40" alt="bars scale">
  <img src="data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7" width="10" height="1" alt="">
  <img src="https://raw.githubusercontent.com/yauheniya-ai/icon-gen-ai/main/output/ani_embedded_upload.svg" width="40" alt="my location loop">
  <img src="data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7" width="10" height="1" alt="">
  <img src="https://raw.githubusercontent.com/yauheniya-ai/icon-gen-ai/main/output/ani_embedded_location.svg" width="40" alt="speedometer loop">
  <img src="data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7" width="10" height="1" alt="">
  <img src="https://raw.githubusercontent.com/yauheniya-ai/icon-gen-ai/main/output/ani_embedded_bars.svg" width="40" alt="upload outline loop">
</div>

**What preserves animations:**
- Solid colors
- No color specified (original colors)
- Backgrounds and outlines

**What removes animations:**
- Gradient colors on the icon itself: `color=('deeppink', 'mediumslateblue')`

**Note:** Background gradients don't affect icon animations - only icon color gradients do.

## CLI Usage

Below is the full output of <code>icon-gen-ai --help</code>:

```text
Usage: icon-gen-ai [OPTIONS] COMMAND [ARGS]...

  icon-gen-ai — generate icons from Iconify, URLs, or local files.

Options:
  --version  Show the version and exit.
  --help     Show this message and exit.

Commands:
  generate   Generate icons from Iconify or local files.
  providers  Show AI provider status.
  search     Search for icons using natural language queries.
```
Read the <a href="https://yauheniya-ai.github.io/icon-gen-ai/" target="_blank" rel="noopener noreferrer">documentation</a> for more detailed instructions.


## Icon Sources

**Three ways to get icons:**

### 1. Iconify (275,000+ icons)
Browse at <a href="https://icon-sets.iconify.design/" target="_blank" rel="noopener noreferrer">Iconify</a>

```python
# Format: collection:icon-name
'simple-icons:openai'           # Simple Icons by Simple Icons Collaborators (License: CC0 1.0)  
'mdi:github'                    # Material Design Icons by Pictogrammers (License: Apache 2.0)  
'devicon:fastapi'               # Devicon by konpa (License: MIT)  
'gis:drone'                     # Font-GIS by Jean-Marc Viglino (License: CC BY 4.0)  
```

**AI-powered search** (requires `pip install icon-gen-ai[ai]`):
```bash
icon-gen-ai search "payment icons for checkout"
```

### 2. Direct URL
Any public image URL:
```python
direct_url='https://upload.wikimedia.org/wikipedia/commons/b/b0/Claude_AI_symbol.svg'
direct_url='https://companieslogo.com/img/orig/NVDA-df4c2377.svg'
```

### 3. Local File
Locally saved images:
```python
local_file='input/pypi-icon.svg'
local_file='input/github-mark.png'
local_file='input/html_css_js-icon.jpeg'
local_file='input/react-icon.webp'
```

## Examples

Check out the `examples/` directory for more use cases:

**Basic Generation:**
- `generate_ai_icons_singular.py` - Generate icons one-by-one with custom backgrounds & gradients
- `generate_ai_icons_batch.py` - Generate multiple AI model icons at once (batch mode)

**AI-Powered Search** (requires `pip install icon-gen-ai[ai]`):
- `ai_simple_usage.py` - Search and generate icons using natural language
- `ai_icon_search.py` - Advanced search with custom styles and project context

## Development

```bash
# Clone the repository
git clone https://github.com/yauheniya-ai/icon-gen-ai.git
cd icon-gen-ai

# Install all dependencies (including dev tools)
uv sync --extra ai --dev

# Run tests
uv run pytest --cov=src --cov-report=term-missing
```

## License

MIT License – see <a href="https://github.com/yauheniya-ai/icon-gen-ai/blob/main/LICENSE" target="_blank" rel="noopener noreferrer">LICENSE</a> file for details.

## Author

Yauheniya

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
