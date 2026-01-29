# Django SwiftAPI

[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/)
[![Django Version](https://img.shields.io/badge/django-4.2%2B-green)](https://www.djangoproject.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**Django SwiftAPI** is a modern, async-first API framework for Django designed as a successor to Django REST Framework (DRF). It provides familiar DRF-like patterns while delivering significantly better performance through async-first design, lightweight schema-based validation, and built-in multi-tenancy support.

## ✨ Features

| Feature                 | Description                             |
| ----------------------- | --------------------------------------- |
| **Async-First Design**  | Native async/await with sync fallback   |
| **Lightweight Schemas** | Type-hint based validation              |
| **Zero-Config CRUD**    | Complete APIs from just a model         |
| **Multi-Tenancy**       | 5 tenant resolution strategies          |
| **DRF-Compatible**      | Familiar ViewSets, Routers, Permissions |
| **OpenAPI Docs**        | Auto-generated Swagger UI               |
| **High Performance**    | O(n) validation, minimal overhead       |
| **File Uploads**        | FileField, ImageField with validation   |
| **Caching**             | Response cache with ETag/Last-Modified  |
| **API Versioning**      | URL, header, and query param versioning |
| **Background Tasks**    | Async, Celery, Django-Q backends        |
| **Events/Signals**      | Domain events with async event bus      |
| **Bulk Operations**     | Bulk create/update/delete support       |
| **Content Types**       | JSON, CSV, XML, HTML renderers          |
| **Rate Limiting**       | IP, user, and scoped throttling         |

## 🚀 Quick Start

### Installation

```bash
pip install django-swiftapi
```

### Basic Usage

```python
# models.py
from django.db import models

class Article(models.Model):
    title = models.CharField(max_length=200)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

# views.py
from swiftapi import ViewSet, Router, Schema, Field
from swiftapi.permissions import IsAuthenticatedOrReadOnly

class ArticleSchema(Schema):
    id: int = Field(read_only=True)
    title: str = Field(min_length=1, max_length=200)
    content: str
    created_at: str = Field(read_only=True)

class ArticleViewSet(ViewSet):
    model = Article
    read_schema = ArticleSchema
    write_schema = ArticleSchema
    permission_classes = [IsAuthenticatedOrReadOnly]

# urls.py
router = Router()
router.register("articles", ArticleViewSet)

urlpatterns = [
    path("api/", include(router.urls)),
]
```

### Zero-Config CRUD

```python
from swiftapi import Router
router = Router()
router.crud("articles", Article, exclude=["internal_notes"])
```

## 📚 Module Reference

### Core Modules

| Module        | Purpose                                      |
| ------------- | -------------------------------------------- |
| `schemas.py`  | Type-hint based validation and serialization |
| `viewsets.py` | Async CRUD ViewSets with lifecycle hooks     |
| `routing.py`  | DRF-like URL router (Router, NestedRouter)   |
| `handlers.py` | Async request processing pipeline            |
| `crud.py`     | Zero-config CRUD generation                  |

### Auth & Security

| Module              | Purpose                                     |
| ------------------- | ------------------------------------------- |
| `authentication.py` | Session, Token, JWT, API Key authentication |
| `permissions.py`    | 10+ permission classes with async support   |
| `throttling.py`     | Rate limiting (IP, user, scoped)            |
| `middleware.py`     | CORS, logging, security headers             |

### Multi-Tenancy

| Module       | Purpose                                      |
| ------------ | -------------------------------------------- |
| `tenancy.py` | Header, JWT, subdomain, path, user resolvers |

### Data Handling

| Module          | Purpose                                      |
| --------------- | -------------------------------------------- |
| `pagination.py` | Limit/offset, page number, cursor pagination |
| `filters.py`    | Query, ordering, and search filters          |
| `uploads.py`    | File and image upload handling               |
| `bulk.py`       | Bulk create/update/delete operations         |

### Advanced Features

| Module          | Purpose                                    |
| --------------- | ------------------------------------------ |
| `versioning.py` | URL, header, query param API versioning    |
| `caching.py`    | Response caching with ETag/Last-Modified   |
| `events.py`     | Domain events and async event bus          |
| `tasks.py`      | Background tasks (async, Celery, Django-Q) |
| `lifecycle.py`  | Request lifecycle hooks                    |
| `content.py`    | JSON, CSV, XML, HTML content negotiation   |

### Documentation & Testing

| Module       | Purpose                             |
| ------------ | ----------------------------------- |
| `openapi.py` | OpenAPI 3.0 generation + Swagger UI |
| `testing.py` | AsyncAPIClient and test utilities   |

## ⚙️ Configuration

```python
# settings.py
SWIFTAPI = {
    # Pagination
    "PAGE_SIZE": 25,
    "MAX_PAGE_SIZE": 100,

    # Authentication
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "swiftapi.authentication.SessionAuthentication",
        "swiftapi.authentication.JWTAuthentication",
    ],

    # Permissions
    "DEFAULT_PERMISSION_CLASSES": [
        "swiftapi.permissions.IsAuthenticated",
    ],

    # Multi-tenancy
    "TENANT_RESOLVER": "swiftapi.tenancy.HeaderTenantResolver",
    "TENANT_MODEL": "myapp.Organization",

    # Throttling
    "DEFAULT_THROTTLE_RATES": {
        "anon": "100/day",
        "user": "1000/day",
    },

    # CORS
    "CORS_ALLOW_ALL_ORIGINS": True,

    # JWT
    "JWT_SECRET_KEY": "your-secret-key",
    "JWT_ALGORITHM": "HS256",

    # Background Tasks
    "TASK_BACKEND": "swiftapi.tasks.CeleryTaskBackend",
    "CELERY_APP": "myapp.celery.app",

    # Versioning
    "DEFAULT_VERSION": "v1",
    "ALLOWED_VERSIONS": ["v1", "v2"],
}
```

## 🔌 Middleware

Add SwiftAPI middleware to your Django project:

```python
MIDDLEWARE = [
    # ...
    "swiftapi.middleware.RequestLoggingMiddleware",
    "swiftapi.middleware.ExceptionMiddleware",
    "swiftapi.middleware.CORSMiddleware",
    "swiftapi.middleware.JSONBodyMiddleware",
    "swiftapi.tenancy.TenantMiddleware",
    # ...
]
```

## 🧪 Testing

```python
from swiftapi.testing import AsyncAPIClient, AsyncTestCase

class TestArticleAPI(AsyncTestCase):
    async def test_list_articles(self):
        response = await self.client.get("/api/articles/")
        self.assertEqual(response.status_code, 200)

    async def test_create_article(self):
        self.client.set_jwt("token")
        response = await self.client.post("/api/articles/", {
            "title": "Test",
            "content": "Content",
        })
        self.assertEqual(response.status_code, 201)
```

## 🤝 DRF Migration

| DRF                  | SwiftAPI             |
| -------------------- | -------------------- |
| `ModelSerializer`    | `Schema`             |
| `ModelViewSet`       | `ViewSet`            |
| `DefaultRouter`      | `Router`             |
| `permission_classes` | `permission_classes` |

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.
