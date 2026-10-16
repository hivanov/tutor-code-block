# Tutor Code Block Plugin & Open edX XBlock

A first-class Tutor plugin and Open edX XBlock component for embedding beautiful, interactive code snippets with syntax highlighting, copy-to-clipboard button, configurable line numbers, line emphasis/highlighting, and multiple themes without character escaping or HTML editing.

---

## Key Features

- **500+ Languages Supported**: Data-driven syntax highlighting powered by Pygments and pre-compiled language registries (Python, Go, Rust, TypeScript, Bash, YAML, JSON, SQL, Prometheus PromQL, Dockerfile, Terraform, GraphQL, Solidity, WebAssembly WAT, etc.).
- **Zero HTML Character Escaping**: Paste 100% raw unescaped source code directly into Studio—the engine safely handles HTML entities, tokens, and formatting automatically.
- **Copy to Clipboard Button**: Integrated header action with clipboard API (`navigator.clipboard`), fallback support, and animated feedback ("Copied!" with checkmark).
- **Line Numbering & Non-Bleed Gutter**: Display line numbers with customizable starting index (`line_number_start`). Gutter numbers use `user-select: none` so selecting code text never copies line numbers.
- **Line Emphasis & Highlighting**: Highlight key lines and ranges (e.g. `2, 4-7, 10`) with distinct theme-aware tinting and accent indicator bars.
- **Visual Themes**: Includes One Dark Pro, GitHub Dark, GitHub Light, Dracula, Monokai, Nord, Solarized Dark, and Solarized Light with zero external CDN dependencies.
- **Soft Wrap & Scroll Bounds**: Toggleable line wrapping and maximum container height with smooth scrolling.
- **OLX Course Format Support**: Seamless offline course export and import via standard `<code_block_xblock>` XML tags.

---

## Easy Deployment Guide

### Step 1: Install Plugin into Tutor Python Virtual Environment

On the machine where Tutor is running:

```bash
# Activate your Tutor virtualenv
source ~/.local/share/tutor/env/bin/activate  # or your tutor venv path

# Install tutor-code-block in editable mode or from Git/PyPI
pip install -e /path/to/plugins/tutor-code-block
# Or: pip install git+https://github.com/your-org/tutor-code-block.git
```

Verify that Tutor recognizes the plugin:

```bash
tutor plugins list
```

You should see:
```text
NAME         STATUS      VERSION
code_block   ⚪ disabled 0.1.0
```

---

### Step 2: Enable Plugin in Tutor

```bash
tutor plugins enable code_block
tutor config save
```

---

### Step 3: Rebuild Open edX Images & Deploy

The plugin automatically injects `tutor-code-block` into the LMS and CMS Docker image build pipeline.

For **Docker Compose (`tutor local`)**:

```bash
# Rebuild Open edX image with the new XBlock dependency
tutor images build openedx

# Restart LMS and CMS
tutor local start -d
```

For **Kubernetes (`tutor k8s`)**:

```bash
tutor images build openedx
tutor images push openedx
tutor k8s start
```

---

## Enabling in Studio Courses

1. Open your course in **Studio**.
2. Navigate to **Settings** > **Advanced Settings**.
3. In the **Advanced Module List** field, add `"code_block"`:
   ```json
   [
     "code_block"
   ]
   ```
4. Click **Save Changes**.
5. Inside any Course Unit, click **Add New Component** > **Advanced** > **Code Block**.
6. Click **Edit** to configure language, code, title, line numbers, and theme.

---

## OLX Course XML Schema

When compiling courses offline or packaging `.tar.gz` course archives:

```xml
<code_block_xblock
    url_name="block_sample_code"
    display_name="HTTP Server Example"
    title="main.go"
    language="go"
    theme="one-dark-pro"
    line_numbers="true"
    line_number_start="1"
    highlight_lines="6, 8-10"
    wrap_code="false"
    show_copy_button="true"
    max_height_px="400">
package main

import (
    "fmt"
    "net/http"
)

func main() {
    http.HandleFunc("/healthz", func(w http.ResponseWriter, r *http.Request) {
        fmt.Fprintln(w, "OK")
    })
    http.ListenAndServe(":8080", nil)
}
</code_block_xblock>
```

---

## Development & Testing

```bash
# Generate / refresh languages data registry
make build-data

# Run linter (Ruff)
make lint

# Run type checker (Mypy)
make typecheck

# Run full test suite (Pytest)
make test
```

---

## License

This software is licensed under the GPL-3.0 License.
