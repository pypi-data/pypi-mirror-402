"""Vite configuration generator for vanilla HTML/CSS projects."""

from pathlib import Path


def generate_vite_config(
    backend_url: str,
    port: int,
    root: Path,
    open_browser: bool = True,
) -> str:
    """
    Generate a minimal Vite config with cosmux-inject plugin.

    Args:
        backend_url: The Cosmux backend URL (e.g., http://localhost:3333)
        port: The Vite dev server port
        root: The project root directory
        open_browser: Whether to auto-open the browser

    Returns:
        A string containing the Vite configuration as JavaScript
    """
    # Normalize the root path for JavaScript (forward slashes)
    root_str = str(root.resolve()).replace("\\", "/")

    # Note: We use CommonJS module.exports to avoid requiring vite to be installed
    # in the user's project. The defineConfig helper is optional.
    return f'''/** @type {{import('vite').UserConfig}} */
module.exports = {{
  root: '{root_str}',
  server: {{
    port: {port},
    open: {str(open_browser).lower()},
    strictPort: true,
  }},
  plugins: [
    {{
      name: 'cosmux-inject',
      transformIndexHtml(html) {{
        // Inject Cosmux widget before </body>
        const injection = `
<script>window.__COSMUX_CONFIG__ = {{ serverUrl: '{backend_url}' }};</script>
<script src="{backend_url}/static/cosmux-widget.iife.js"></script>
<link rel="stylesheet" href="{backend_url}/static/cosmux-widget.css">
`;
        return html.replace('</body>', injection + '</body>');
      }},
    }},
  ],
  // Disable caching for development
  optimizeDeps: {{
    force: true,
  }},
}};
'''


def get_temp_config_path(workspace: Path) -> Path:
    """
    Get the path for the temporary Vite config file.

    The config is stored in the .cosmux directory to keep the user's
    project root clean.

    Args:
        workspace: The workspace directory

    Returns:
        Path to the temporary Vite config file
    """
    cosmux_dir = workspace / ".cosmux"
    cosmux_dir.mkdir(exist_ok=True)
    # Use .cjs extension to ensure CommonJS module loading
    return cosmux_dir / "vite.config.cjs"
