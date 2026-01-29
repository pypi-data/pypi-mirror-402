"""
SwiftAPI Browsable API.

Developer-friendly HTML interface for API exploration - similar to DRF's browsable API.
"""

from __future__ import annotations

import json
from typing import Any

from django.http import HttpRequest, HttpResponse

# Inline template for browsable API (no external files needed)
BROWSABLE_API_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ title }} - SwiftAPI</title>
    <style>
        :root {
            --primary: #2c3e50;
            --accent: #3498db;
            --success: #27ae60;
            --warning: #f39c12;
            --danger: #e74c3c;
            --bg: #ecf0f1;
            --card-bg: #ffffff;
            --text: #2c3e50;
            --text-muted: #7f8c8d;
            --border: #bdc3c7;
        }

        * { box-sizing: border-box; margin: 0; padding: 0; }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            background: var(--bg);
            color: var(--text);
            line-height: 1.6;
        }

        /* Header */
        .header {
            background: var(--primary);
            color: white;
            padding: 1rem 2rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .header h1 {
            font-size: 1.25rem;
            font-weight: 600;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }

        .header h1::before {
            content: "⚡";
        }

        .header-nav {
            display: flex;
            gap: 1rem;
        }

        .header-nav a {
            color: white;
            text-decoration: none;
            opacity: 0.8;
            transition: opacity 0.2s;
        }

        .header-nav a:hover { opacity: 1; }

        /* Container */
        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 2rem;
        }

        /* Breadcrumb */
        .breadcrumb {
            display: flex;
            gap: 0.5rem;
            margin-bottom: 1.5rem;
            font-size: 0.875rem;
        }

        .breadcrumb a {
            color: var(--accent);
            text-decoration: none;
        }

        .breadcrumb a:hover { text-decoration: underline; }

        .breadcrumb span { color: var(--text-muted); }

        /* Card */
        .card {
            background: var(--card-bg);
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
            overflow: hidden;
        }

        .card-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 1rem 1.5rem;
            border-bottom: 1px solid var(--border);
        }

        .card-header h2 {
            font-size: 1.5rem;
            font-weight: 600;
        }

        .card-body { padding: 1.5rem; }

        /* Buttons */
        .btn-group {
            display: flex;
            gap: 0.5rem;
        }

        .btn {
            padding: 0.5rem 1rem;
            border: none;
            border-radius: 4px;
            font-size: 0.875rem;
            font-weight: 500;
            cursor: pointer;
            transition: all 0.2s;
        }

        .btn-primary {
            background: var(--accent);
            color: white;
        }

        .btn-primary:hover { background: #2980b9; }

        .btn-secondary {
            background: var(--text-muted);
            color: white;
        }

        .btn-success {
            background: var(--success);
            color: white;
        }

        .btn-warning {
            background: var(--warning);
            color: white;
        }

        .btn-danger {
            background: var(--danger);
            color: white;
        }

        /* Method indicator */
        .method-label {
            display: inline-block;
            padding: 0.25rem 0.75rem;
            border-radius: 4px;
            font-size: 0.75rem;
            font-weight: 700;
            text-transform: uppercase;
            margin-right: 0.5rem;
        }

        .method-GET { background: var(--success); color: white; }
        .method-POST { background: var(--accent); color: white; }
        .method-PUT { background: var(--warning); color: white; }
        .method-PATCH { background: #9b59b6; color: white; }
        .method-DELETE { background: var(--danger); color: white; }
        .method-OPTIONS { background: var(--text-muted); color: white; }

        /* Request info */
        .request-info {
            background: #f7f9fa;
            padding: 1rem 1.5rem;
            border-bottom: 1px solid var(--border);
            font-family: 'SF Mono', 'Monaco', 'Consolas', monospace;
            font-size: 0.875rem;
        }

        .request-url {
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }

        /* Response headers */
        .response-headers {
            background: #f7f9fa;
            padding: 1rem 1.5rem;
            border-bottom: 1px solid var(--border);
            font-family: 'SF Mono', 'Monaco', 'Consolas', monospace;
            font-size: 0.8125rem;
        }

        .response-headers .status {
            font-weight: 700;
            margin-bottom: 0.5rem;
        }

        .response-headers .status.success { color: var(--success); }
        .response-headers .status.error { color: var(--danger); }

        .response-headers .header-line {
            color: var(--text-muted);
        }

        .response-headers .header-name {
            color: var(--primary);
            font-weight: 600;
        }

        .response-headers .header-value {
            color: var(--accent);
        }

        /* JSON response */
        .response-body {
            padding: 1.5rem;
            font-family: 'SF Mono', 'Monaco', 'Consolas', monospace;
            font-size: 0.8125rem;
            overflow-x: auto;
            background: #fafbfc;
        }

        .response-body pre {
            margin: 0;
            white-space: pre-wrap;
            word-break: break-word;
        }

        /* JSON syntax highlighting */
        .json-key { color: #e74c3c; }
        .json-string { color: #27ae60; }
        .json-number { color: #3498db; }
        .json-boolean { color: #9b59b6; }
        .json-null { color: #7f8c8d; }

        /* Form */
        .api-form {
            margin-top: 1.5rem;
            padding-top: 1.5rem;
            border-top: 1px solid var(--border);
        }

        .api-form h3 {
            font-size: 1rem;
            margin-bottom: 1rem;
        }

        .api-form textarea {
            width: 100%;
            min-height: 150px;
            padding: 0.75rem;
            border: 1px solid var(--border);
            border-radius: 4px;
            font-family: 'SF Mono', 'Monaco', 'Consolas', monospace;
            font-size: 0.875rem;
            resize: vertical;
        }

        .api-form .form-actions {
            margin-top: 1rem;
            display: flex;
            gap: 0.5rem;
        }

        /* Tabs */
        .tabs {
            display: flex;
            border-bottom: 1px solid var(--border);
            margin-bottom: 1rem;
        }

        .tab {
            padding: 0.75rem 1.5rem;
            cursor: pointer;
            border-bottom: 2px solid transparent;
            color: var(--text-muted);
            font-weight: 500;
        }

        .tab.active {
            color: var(--accent);
            border-bottom-color: var(--accent);
        }

        /* Description */
        .description {
            color: var(--text-muted);
            margin-bottom: 1rem;
        }

        /* Footer */
        .footer {
            text-align: center;
            padding: 2rem;
            color: var(--text-muted);
            font-size: 0.875rem;
        }

        .footer a { color: var(--accent); text-decoration: none; }
    </style>
</head>
<body>
    <header class="header">
        <h1>SwiftAPI</h1>
        <nav class="header-nav">
            <a href="{{ api_root }}">API Root</a>
            {% if user.is_authenticated %}
            <a href="#">{{ user.username }}</a>
            {% else %}
            <a href="#">Log in</a>
            {% endif %}
        </nav>
    </header>

    <main class="container">
        <nav class="breadcrumb">
            <a href="{{ api_root }}">Api Overview</a>
            <span>/</span>
            <span>{{ view_name }}</span>
        </nav>

        <div class="card">
            <div class="card-header">
                <h2>{{ view_name }}</h2>
                <div class="btn-group">
                    {% for method in allowed_methods %}
                    <button class="btn btn-{% if method == 'GET' %}primary{% elif method == 'POST' %}success{% elif method == 'DELETE' %}danger{% else %}secondary{% endif %}"
                            onclick="window.location.href='?format=json'"
                            {% if method == request.method %}disabled{% endif %}>
                        {{ method }}
                    </button>
                    {% endfor %}
                </div>
            </div>

            <div class="request-info">
                <div class="request-url">
                    <span class="method-label method-{{ request.method }}">{{ request.method }}</span>
                    <code>{{ request.path }}</code>
                </div>
            </div>

            {% if description %}
            <div class="card-body">
                <p class="description">{{ description }}</p>
            </div>
            {% endif %}

            <div class="response-headers">
                <div class="status {% if status_code < 400 %}success{% else %}error{% endif %}">
                    HTTP {{ status_code }} {{ status_text }}
                </div>
                <div class="header-line">
                    <span class="header-name">Allow:</span>
                    <span class="header-value">{{ allowed_methods|join:", " }}</span>
                </div>
                <div class="header-line">
                    <span class="header-name">Content-Type:</span>
                    <span class="header-value">application/json</span>
                </div>
                <div class="header-line">
                    <span class="header-name">Vary:</span>
                    <span class="header-value">Accept</span>
                </div>
            </div>

            <div class="response-body">
                <pre>{{ response_json }}</pre>
            </div>

            {% if show_form and 'POST' in allowed_methods %}
            <div class="card-body api-form">
                <h3>POST Request</h3>
                <form method="POST">
                    {% csrf_token %}
                    <textarea name="data" placeholder='{"key": "value"}'></textarea>
                    <div class="form-actions">
                        <button type="submit" class="btn btn-success">POST</button>
                    </div>
                </form>
            </div>
            {% endif %}

            {% if show_form and 'PUT' in allowed_methods %}
            <div class="card-body api-form">
                <h3>PUT Request</h3>
                <form method="POST">
                    {% csrf_token %}
                    <input type="hidden" name="_method" value="PUT">
                    <textarea name="data" placeholder='{"key": "value"}'>{{ response_json }}</textarea>
                    <div class="form-actions">
                        <button type="submit" class="btn btn-warning">PUT</button>
                    </div>
                </form>
            </div>
            {% endif %}
        </div>
    </main>

    <footer class="footer">
        <p>Powered by <a href="#">SwiftAPI</a> v{{ version }}</p>
    </footer>

    <script>
        // JSON syntax highlighting
        document.addEventListener('DOMContentLoaded', function() {
            const pre = document.querySelector('.response-body pre');
            if (pre) {
                const json = pre.textContent;
                try {
                    const highlighted = syntaxHighlight(JSON.parse(json));
                    pre.innerHTML = highlighted;
                } catch (e) {
                    // Not valid JSON, leave as is
                }
            }
        });

        function syntaxHighlight(obj, indent = 0) {
            const spaces = '  '.repeat(indent);

            if (obj === null) {
                return '<span class="json-null">null</span>';
            }

            if (typeof obj === 'boolean') {
                return '<span class="json-boolean">' + obj + '</span>';
            }

            if (typeof obj === 'number') {
                return '<span class="json-number">' + obj + '</span>';
            }

            if (typeof obj === 'string') {
                return '<span class="json-string">"' + escapeHtml(obj) + '"</span>';
            }

            if (Array.isArray(obj)) {
                if (obj.length === 0) return '[]';
                const items = obj.map(item => spaces + '  ' + syntaxHighlight(item, indent + 1));
                return '[\\n' + items.join(',\\n') + '\\n' + spaces + ']';
            }

            if (typeof obj === 'object') {
                const keys = Object.keys(obj);
                if (keys.length === 0) return '{}';
                const items = keys.map(key =>
                    spaces + '  <span class="json-key">"' + escapeHtml(key) + '"</span>: ' +
                    syntaxHighlight(obj[key], indent + 1)
                );
                return '{\\n' + items.join(',\\n') + '\\n' + spaces + '}';
            }

            return String(obj);
        }

        function escapeHtml(str) {
            return str.replace(/&/g, '&amp;')
                      .replace(/</g, '&lt;')
                      .replace(/>/g, '&gt;')
                      .replace(/"/g, '&quot;');
        }
    </script>
</body>
</html>
"""


def get_status_text(status_code: int) -> str:
    """Get HTTP status text from code."""
    status_texts = {
        200: "OK",
        201: "Created",
        204: "No Content",
        301: "Moved Permanently",
        302: "Found",
        304: "Not Modified",
        400: "Bad Request",
        401: "Unauthorized",
        403: "Forbidden",
        404: "Not Found",
        405: "Method Not Allowed",
        406: "Not Acceptable",
        409: "Conflict",
        422: "Unprocessable Entity",
        429: "Too Many Requests",
        500: "Internal Server Error",
        502: "Bad Gateway",
        503: "Service Unavailable",
    }
    return status_texts.get(status_code, "Unknown")


def format_json(data: Any) -> str:
    """Format data as pretty JSON."""
    return json.dumps(data, indent=2, ensure_ascii=False, default=str)


class BrowsableAPIRenderer:
    """
    Renders responses as browsable HTML interface.

    Usage:
        SWIFTAPI = {
            "DEFAULT_RENDERER_CLASSES": [
                "swiftapi.browsable.BrowsableAPIRenderer",
                "swiftapi.content.JSONRenderer",
            ],
        }
    """

    media_type = "text/html"
    format = "html"
    charset = "utf-8"
    template = BROWSABLE_API_TEMPLATE

    def render(
        self,
        data: Any,
        request: HttpRequest,
        view: Any = None,
        status_code: int = 200,
    ) -> str:
        """Render data as browsable HTML."""
        from django.template import Context, Template

        # Build context
        context = self._get_context(data, request, view, status_code)

        # Render template
        template = Template(self.template)
        return template.render(Context(context))

    def get_response(
        self,
        data: Any,
        request: HttpRequest,
        view: Any = None,
        status: int = 200,
        headers: dict | None = None,
    ) -> HttpResponse:
        """Create HTTP response with rendered HTML."""
        content = self.render(data, request, view, status)

        response = HttpResponse(
            content,
            content_type=f"{self.media_type}; charset={self.charset}",
            status=status,
        )

        if headers:
            for key, value in headers.items():
                response[key] = value

        return response

    def _get_context(
        self,
        data: Any,
        request: HttpRequest,
        view: Any,
        status_code: int,
    ) -> dict[str, Any]:
        """Build template context."""
        from swiftapi import __version__

        # Get view info
        view_name = self._get_view_name(view)
        description = self._get_view_description(view)
        allowed_methods = self._get_allowed_methods(view)

        return {
            "request": request,
            "user": getattr(request, "user", None),
            "view_name": view_name,
            "title": view_name,
            "description": description,
            "allowed_methods": allowed_methods,
            "status_code": status_code,
            "status_text": get_status_text(status_code),
            "response_json": format_json(data),
            "api_root": "/api/",
            "version": __version__,
            "show_form": True,
        }

    def _get_view_name(self, view: Any) -> str:
        """Get human-readable view name."""
        if view is None:
            return "API"

        if hasattr(view, "get_view_name"):
            return view.get_view_name()

        name = view.__class__.__name__
        # Convert CamelCase to Title Case
        import re
        name = re.sub(r"([a-z])([A-Z])", r"\1 \2", name)
        return name.replace("ViewSet", "").strip() or "API"

    def _get_view_description(self, view: Any) -> str:
        """Get view description from docstring."""
        if view is None:
            return ""

        if hasattr(view, "get_view_description"):
            return view.get_view_description()

        return view.__class__.__doc__ or ""

    def _get_allowed_methods(self, view: Any) -> list[str]:
        """Get list of allowed HTTP methods."""
        if view is None:
            return ["GET"]

        methods = []
        method_map = {
            "list": "GET",
            "retrieve": "GET",
            "create": "POST",
            "update": "PUT",
            "partial_update": "PATCH",
            "destroy": "DELETE",
        }

        for action, method in method_map.items():
            if hasattr(view, action) and method not in methods:
                methods.append(method)

        if "OPTIONS" not in methods:
            methods.append("OPTIONS")

        return methods


class BrowsableAPIMixin:
    """
    Mixin for ViewSets to support browsable API.

    Usage:
        class UserViewSet(BrowsableAPIMixin, ViewSet):
            model = User
            ...
    """

    browsable_name: str | None = None
    browsable_description: str | None = None

    def get_view_name(self) -> str:
        """Get human-readable view name."""
        if self.browsable_name:
            return self.browsable_name

        name = self.__class__.__name__
        import re
        name = re.sub(r"([a-z])([A-Z])", r"\1 \2", name)
        return name.replace("ViewSet", "").replace("View", "").strip()

    def get_view_description(self) -> str:
        """Get view description."""
        if self.browsable_description:
            return self.browsable_description
        return self.__class__.__doc__ or ""


def get_browsable_api_view():
    """
    Create a view that renders the API root as browsable HTML.

    Usage:
        urlpatterns = [
            path("api/", get_browsable_api_view(router)),
        ]
    """
    def browsable_root_view(request: HttpRequest) -> HttpResponse:
        renderer = BrowsableAPIRenderer()

        data = {
            "message": "Welcome to SwiftAPI",
            "endpoints": {
                "users": "/api/users/",
                "docs": "/api/docs/",
            }
        }

        return renderer.get_response(data, request)

    return browsable_root_view
