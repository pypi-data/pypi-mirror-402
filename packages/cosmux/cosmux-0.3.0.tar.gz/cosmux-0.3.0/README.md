<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="docs/images/logo-dark.png">
    <source media="(prefers-color-scheme: light)" srcset="docs/images/logo-light.png">
    <img src="docs/images/logo-light.png" alt="Cosmux" height="80">
  </picture>
</p>

<p align="center">
  <strong>AI coding assistant that lives in your dev environment</strong><br>
  Powered by Claude. Reads, writes, and edits your code while you work.
</p>

<p align="center">
  <img src="docs/images/cosmux-workflow.gif" alt="Cosmux Workflow" width="100%">
</p>

<p align="center">
  <a href="#quick-start">Quick Start</a> •
  <a href="#features">Features</a> •
  <a href="#vite-integration">Vite</a> •
  <a href="#nextjs-integration">Next.js</a> •
  <a href="#configuration">Configuration</a>
</p>

---

## Choose Your Integration

| Your Project | Recommended |
|--------------|-------------|
| Plain HTML/CSS | [`cosmux dev`](#html-css-projects) — zero config! |
| Vite/React/Vue | [Vite Plugin](#vite-integration) |
| Next.js | [Next.js Wrapper](#nextjs-integration) |
| Other frameworks | [Manual Script](#manual-integration) |
| Standalone Chat | `http://localhost:3333/cosmux` |

---

## HTML/CSS Projects

The simplest way to use Cosmux. **No configuration needed.**

### 1. Install

```bash
pip install cosmux
```

### 2. Set your API key

```bash
export ANTHROPIC_API_KEY=sk-ant-api03-...
```

### 3. Start development

```bash
cd your-website/
cosmux dev
```

Open **http://localhost:5174** — your website with the AI assistant injected.

**What you get:**
- CSS changes update **instantly** (no page reload)
- HTML changes **auto-reload** the page
- Widget **auto-injected** into your HTML
- Backend + Vite dev server managed for you

---

## Quick Start (Standalone)

Just want the chat interface? No widget injection needed.

### 1. Install

```bash
pip install cosmux
```

### 2. Set your API key

```bash
# .env or environment
ANTHROPIC_API_KEY=sk-ant-api03-...
```

### 3. Start the server

```bash
cosmux serve
```

### 4. Open the chat

Visit **http://localhost:3333/cosmux** — the AI assistant is ready!

---

## Features

| | Feature | Description |
|---|---------|-------------|
| 💬 | **Chat Interface** | Natural conversation with streaming responses |
| 🧠 | **Extended Thinking** | Watch the AI reason through complex problems |
| 📁 | **File Operations** | Read, Write, Edit files in your project |
| 💻 | **Terminal Access** | Run shell commands via Bash tool |
| 🔍 | **Code Search** | Glob and Grep tools for finding code |
| 💾 | **Session Persistence** | Chat history saved locally |
| 📖 | **Context-Aware** | Reads `CLAUDE.md` for project understanding |

---

## Vite Integration

Inject the widget automatically into your Vite app.

### 1. Install both packages

```bash
pip install cosmux
npm install -D cosmux
```

### 2. Add the plugin

```typescript
// vite.config.ts
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { cosmux } from 'cosmux/vite'

export default defineConfig({
  plugins: [
    react(),
    cosmux()  // Starts server + injects widget
  ]
})
```

### 3. Run your dev server

```bash
npm run dev
```

The widget appears automatically! The plugin:
- Starts `cosmux serve` when Vite starts
- Injects the widget into your HTML
- Stops the server when Vite closes

### Plugin Options

```typescript
cosmux({
  port: 3333,           // Server port (default: 3333)
  autoStart: true,      // Auto-start server (default: true)
  injectWidget: true,   // Inject widget script (default: true)
  workspace: './',      // Workspace path (default: cwd)
})
```

---

## Next.js Integration

### Option 1: Config Wrapper

```javascript
// next.config.mjs
import { withCosmux } from 'cosmux/next'

export default withCosmux({
  // your existing Next.js config
})
```

### Option 2: Widget Component (App Router)

Create a client component:

```tsx
// components/CosmuxWidget.tsx
'use client'

import { useEffect } from 'react'

export function CosmuxWidget({ port = 3333 }: { port?: number }) {
  useEffect(() => {
    if (process.env.NODE_ENV !== 'development') return

    ;(window as any).__COSMUX_CONFIG__ = { serverUrl: `http://localhost:${port}` }

    const script = document.createElement('script')
    script.src = `http://localhost:${port}/static/cosmux-widget.iife.js`
    script.async = true
    document.body.appendChild(script)

    return () => { script.remove() }
  }, [port])

  return null
}
```

Add to your layout:

```tsx
// app/layout.tsx
import { CosmuxWidget } from '@/components/CosmuxWidget'

export default function RootLayout({ children }) {
  return (
    <html>
      <body>
        {children}
        <CosmuxWidget />
      </body>
    </html>
  )
}
```

---

## Manual Integration

For any web project, add the script tags:

```html
<script>
  window.__COSMUX_CONFIG__ = { serverUrl: 'http://localhost:3333' };
</script>
<script src="http://localhost:3333/static/cosmux-widget.iife.js"></script>
<link rel="stylesheet" href="http://localhost:3333/static/cosmux-widget.css">
```

Then start the server:

```bash
cosmux serve
```

---

## CLI Commands

```bash
# Development (HTML/CSS projects)
cosmux dev                          # Start dev environment with HMR
cosmux dev --port 8080              # Custom dev server port
cosmux dev -w ./my-site             # Specify workspace

# Server only (for other integrations)
cosmux serve                        # Start the backend server
cosmux serve --port 4000            # Custom port
cosmux serve --workspace ./project  # Specific workspace

# Setup & Auth
cosmux init                         # Create CLAUDE.md template
cosmux login                        # Login with Claude Max (OAuth)
cosmux logout                       # Remove stored credentials
cosmux status                       # Show auth status
cosmux version                      # Show version
```

---

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `ANTHROPIC_API_KEY` | Your Anthropic API key | Required |
| `COSMUX_PORT` | Server port | `3333` |
| `COSMUX_MODEL` | Claude model | `claude-opus-4-5-20251101` |

### Project Context

Create a `CLAUDE.md` file in your project root to give the AI context:

```markdown
# My Project

## Tech Stack
- React 18 + TypeScript
- Tailwind CSS

## Code Style
- Use functional components
- Prefer named exports
```

---

## How It Works

1. **Install** — `pip install cosmux` adds the CLI and server
2. **Start** — `cosmux serve` runs the agent server
3. **Connect** — Open `/cosmux` or inject the widget
4. **Code** — AI reads and modifies files in your workspace

All file operations happen locally. Your code is only sent to Claude's API for processing.

---

## Troubleshooting

<details>
<summary><strong>Widget doesn't appear?</strong></summary>

- Check that the server is running (look for "Cosmux Server Starting" in terminal)
- Verify your API key is set in `.env`
- Try opening `http://localhost:3333/cosmux` directly
</details>

<details>
<summary><strong>Server won't start?</strong></summary>

- Check if port 3333 is in use: `lsof -i :3333`
- Try a different port: `cosmux serve --port 4000`
</details>

<details>
<summary><strong>"cosmux: command not found"?</strong></summary>

- Make sure Python bin directory is in your PATH
- Try: `python -m cosmux serve`
</details>

---

## Requirements

- **Python 3.11+** — for the server
- **Node.js 18+** — only for Vite/Next.js integration (optional)
- **Anthropic API key** — [console.anthropic.com](https://console.anthropic.com)

---

## License

MIT — see [LICENSE](LICENSE)

---

<p align="center">
  <a href="./CONTRIBUTING.md">Contributing</a> •
  <a href="https://github.com/techdivision-rnd/cosmux/issues">Issues</a>
</p>
