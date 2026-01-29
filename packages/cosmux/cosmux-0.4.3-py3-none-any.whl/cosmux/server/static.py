"""Static file serving and widget demo page"""

from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import HTMLResponse, FileResponse

router = APIRouter()

STATIC_DIR = Path(__file__).parent.parent / "static"


@router.get("/widget")
async def widget_demo() -> HTMLResponse:
    """Serve the widget demo page"""
    return HTMLResponse("""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Cosmux Widget Demo</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
            min-height: 100vh;
            color: #e4e4e7;
            padding: 2rem;
        }
        .container {
            max-width: 800px;
            margin: 0 auto;
        }
        h1 {
            font-size: 2.5rem;
            margin-bottom: 1rem;
            background: linear-gradient(90deg, #a855f7, #ec4899);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }
        .subtitle {
            color: #a1a1aa;
            font-size: 1.125rem;
            margin-bottom: 2rem;
        }
        .card {
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 1rem;
            padding: 1.5rem;
            margin-bottom: 1.5rem;
            backdrop-filter: blur(10px);
        }
        .card h2 {
            font-size: 1.25rem;
            margin-bottom: 0.75rem;
            color: #fafafa;
        }
        .card p {
            color: #a1a1aa;
            line-height: 1.6;
        }
        .code {
            font-family: 'SF Mono', Monaco, Consolas, monospace;
            background: rgba(0, 0, 0, 0.3);
            padding: 0.25rem 0.5rem;
            border-radius: 0.25rem;
            font-size: 0.875rem;
            color: #a855f7;
        }
        .hint {
            margin-top: 2rem;
            padding: 1rem;
            background: rgba(168, 85, 247, 0.1);
            border: 1px solid rgba(168, 85, 247, 0.3);
            border-radius: 0.5rem;
            color: #d8b4fe;
        }
        .loading {
            display: flex;
            align-items: center;
            gap: 0.5rem;
            color: #a1a1aa;
        }
        .spinner {
            width: 1rem;
            height: 1rem;
            border: 2px solid rgba(168, 85, 247, 0.3);
            border-top-color: #a855f7;
            border-radius: 50%;
            animation: spin 1s linear infinite;
        }
        @keyframes spin {
            to { transform: rotate(360deg); }
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Cosmux</h1>
        <p class="subtitle">AI Coding Agent Widget for Web Development</p>

        <div class="card">
            <h2>Welcome to Cosmux</h2>
            <p>
                The Cosmux widget should appear in the bottom-right corner of this page.
                Click the floating button to open the chat interface and start interacting
                with the AI coding agent.
            </p>
        </div>

        <div class="card">
            <h2>Getting Started</h2>
            <p>
                1. Click the purple button in the corner<br>
                2. Type your message or coding question<br>
                3. Watch as the agent reads, writes, and edits your code
            </p>
        </div>

        <div class="card">
            <h2>Integration</h2>
            <p>
                Add Cosmux to any web app by including:<br><br>
                <span class="code">&lt;script src="http://localhost:3333/static/inject.js"&gt;&lt;/script&gt;</span>
            </p>
        </div>

        <div class="hint" id="loading-hint">
            <div class="loading">
                <div class="spinner"></div>
                <span>Loading Cosmux widget...</span>
            </div>
        </div>
    </div>

    <!-- Load Cosmux Widget -->
    <link rel="stylesheet" href="/static/cosmux-widget.css">
    <script>
        window.__COSMUX_CONFIG__ = {
            serverUrl: window.location.origin
        };
    </script>
    <script src="/static/cosmux-widget.iife.js"
        onload="document.getElementById('loading-hint').innerHTML = '<span style=color:#22c55e>Widget loaded! Click the purple button in the bottom-right corner.</span>'"
        onerror="document.getElementById('loading-hint').innerHTML = '<span style=color:#ef4444>Widget not built. Run: cd frontend && npm run build:widget</span>'">
    </script>
</body>
</html>
    """)


@router.get("/static/cosmux-widget.iife.js")
async def widget_js() -> FileResponse:
    """Return the widget JS with no-cache headers"""
    js_path = STATIC_DIR / "cosmux-widget.iife.js"
    if not js_path.exists():
        return HTMLResponse(
            content="// Widget not built yet",
            media_type="application/javascript",
            status_code=404,
        )
    return FileResponse(
        js_path,
        media_type="application/javascript",
        headers={
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0",
        },
    )


@router.get("/static/cosmux-widget.css")
async def widget_css() -> FileResponse:
    """Return the widget CSS with no-cache headers"""
    css_path = STATIC_DIR / "cosmux-widget.css"
    if not css_path.exists():
        return HTMLResponse(
            content="/* Widget not built yet */",
            media_type="text/css",
            status_code=404,
        )
    return FileResponse(
        css_path,
        media_type="text/css",
        headers={
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0",
        },
    )


@router.get("/cosmux")
async def standalone_chat():
    """Serve the standalone Cosmux chat page"""
    standalone_html = STATIC_DIR / "standalone.html"

    if not standalone_html.exists():
        return HTMLResponse(
            content="""
<!DOCTYPE html>
<html>
<head><title>Cosmux</title></head>
<body style="background:#18181b;color:#fff;font-family:system-ui;display:flex;align-items:center;justify-content:center;height:100vh;margin:0">
  <div style="text-align:center">
    <h1>Cosmux</h1>
    <p>Standalone chat not built yet.</p>
    <code style="background:#27272a;padding:8px 16px;border-radius:8px;display:block;margin-top:16px">
      cd frontend && npm run build:standalone
    </code>
  </div>
</body>
</html>
            """,
            status_code=404,
        )

    return FileResponse(
        standalone_html,
        media_type="text/html",
        headers={
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0",
        },
    )


@router.get("/inject.js")
async def injection_script() -> FileResponse:
    """Return the widget injection script"""
    inject_path = STATIC_DIR / "inject.js"

    if not inject_path.exists():
        # Return a placeholder if not built yet
        return HTMLResponse(
            content="""
// Cosmux Widget Loader - Placeholder
// Run 'cd frontend && npm run build:widget' to build the widget
console.log('[Cosmux] Widget not built yet');
            """,
            media_type="application/javascript",
        )

    return FileResponse(
        inject_path,
        media_type="application/javascript",
        headers={
            "Cache-Control": "no-cache",
            "Access-Control-Allow-Origin": "*",
        },
    )
