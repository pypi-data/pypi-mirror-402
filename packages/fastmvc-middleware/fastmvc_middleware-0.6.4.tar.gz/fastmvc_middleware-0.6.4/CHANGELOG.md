# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.5.0] - 2026-01-18

### Added - Major Expansion (90+ Middlewares!)

#### Security (14 new)

- **ReferrerPolicyMiddleware**: Control Referrer-Policy header

- **PermissionsPolicyMiddleware**: Browser feature permissions

- **CSPReportMiddleware**: CSP violation report handling

- **ReplayPreventionMiddleware**: Prevent replay attacks with nonces

- **RequestSigningMiddleware**: HMAC request signature validation

- **HoneypotMiddleware**: Trap malicious requests with fake endpoints

- **SanitizationMiddleware**: Input sanitization and XSS prevention

#### Authentication (4 new)

- **BasicAuthMiddleware**: HTTP Basic Authentication

- **BearerAuthMiddleware**: Bearer token authentication

- **ScopeMiddleware**: OAuth scope validation

- **RouteAuthMiddleware**: Per-route authentication requirements

#### Rate Limiting & Protection (4 new)

- **BulkheadMiddleware**: Bulkhead pattern for isolation

- **RequestDedupMiddleware**: Deduplicate concurrent requests

- **RequestCoalescingMiddleware**: Coalesce identical requests

#### Performance (8 new)

- **ResponseCacheMiddleware**: In-memory response caching

- **ResponseSignatureMiddleware**: Sign responses for verification

- **BandwidthMiddleware**: Bandwidth throttling

- **NoCacheMiddleware**: Disable caching headers

- **ConditionalRequestMiddleware**: If-None-Match/If-Modified-Since

- **EarlyHintsMiddleware**: HTTP 103 Early Hints support

- **HATEOASMiddleware**: Hypermedia links in responses

#### Observability (6 new)

- **ResponseTimeMiddleware**: Response time SLA monitoring

- **ServerTimingMiddleware**: Server-Timing header support

- **RequestLoggerMiddleware**: Access logging in multiple formats

- **CostTrackingMiddleware**: Request cost tracking for billing

- **RequestSamplerMiddleware**: Request sampling for analytics

#### Operations (4 new)

- **WarmupMiddleware**: Container warmup handling

- **GracefulShutdownMiddleware**: Graceful shutdown with draining

- **ChaosMiddleware**: Chaos engineering fault injection

- **SlowResponseMiddleware**: Artificial delays for testing

#### Request Processing (8 new)

- **RequestValidatorMiddleware**: Request structure validation

- **JSONSchemaMiddleware**: JSON Schema validation

- **PayloadSizeMiddleware**: Request/response size limits

- **MethodOverrideMiddleware**: HTTP method override via header

- **RequestFingerprintMiddleware**: Request fingerprinting

- **RequestPriorityMiddleware**: Request prioritization

- **RequestIDPropagationMiddleware**: Distributed request ID chain

#### Routing (3 new)

- **PathRewriteMiddleware**: URL path rewriting

- **ProxyMiddleware**: Reverse proxy to other services

#### API Management (2 new)

- **APIVersionHeaderMiddleware**: API version headers

- **ContentNegotiationMiddleware**: Accept header content negotiation

#### Detection (3 new)

- **UserAgentMiddleware**: User-Agent parsing and analysis

- **ClientHintsMiddleware**: Client Hints support

- **AcceptLanguageMiddleware**: Accept-Language negotiation

#### Context (2 new)

- **ContextMiddleware**: Shared request context

- **RealIPMiddleware**: Real client IP extraction

- **XFFTrustMiddleware**: X-Forwarded-For trust handling

#### Error Handling (1 new)

- **ExceptionHandlerMiddleware**: Custom exception handlers

### Changed

- Updated version to 0.5.0

- Renamed package from `src` to `fastmiddleware`

- Expanded test suite to 316 tests

- Improved documentation with examples for all middlewares

## [0.4.0] - 2026-01-18

### Added

- **TimeoutMiddleware**: Request timeout enforcement

- **IPFilterMiddleware**: IP whitelist/blacklist

- **HTTPSRedirectMiddleware**: HTTPS enforcement

- **TrailingSlashMiddleware**: URL trailing slash normalization

- **RequestLimitMiddleware**: Request body size limits

- **CSRFMiddleware**: CSRF protection

- **SessionMiddleware**: Server-side sessions

- **CorrelationMiddleware**: Correlation ID tracking

- **VersioningMiddleware**: API versioning

- **BotDetectionMiddleware**: Bot detection and blocking

- **ProfilingMiddleware**: Request profiling

- **CircuitBreakerMiddleware**: Circuit breaker pattern

### Changed

- Updated test coverage

- Improved error messages

## [0.3.0] - 2026-01-17

### Added

- **QuotaMiddleware**: Usage quota enforcement

- **LoadSheddingMiddleware**: Load shedding during overload

- **FeatureFlagMiddleware**: Feature flag management

- **ABTestMiddleware**: A/B testing support

- **GeoIPMiddleware**: GeoIP data extraction

- **DeprecationMiddleware**: API deprecation warnings

- **LocaleMiddleware**: Locale detection

- **WebhookMiddleware**: Webhook signature validation

- **TenantMiddleware**: Multi-tenancy support

- **AuditMiddleware**: Audit logging

- **DataMaskingMiddleware**: Sensitive data masking

- **RedirectMiddleware**: URL redirects

- **HeaderTransformMiddleware**: Header manipulation

- **ETagMiddleware**: ETag generation

- **OriginMiddleware**: Origin validation

- **RetryAfterMiddleware**: Retry-After headers

- **ContentTypeMiddleware**: Content-Type validation

- **ResponseFormatMiddleware**: Response formatting

## [0.2.0] - 2026-01-17

### Added

- **CompressionMiddleware**: GZip compression for responses with configurable thresholds
- **TrustedHostMiddleware**: Host header validation to prevent host header attacks
- **ErrorHandlerMiddleware**: Consistent error response formatting with exception handling
- **HealthCheckMiddleware**: Built-in health, readiness, and liveness endpoints
- **IdempotencyMiddleware**: Idempotency key support for safe request retries
- **CacheMiddleware**: HTTP caching with ETag generation and conditional requests
- **MetricsMiddleware**: Prometheus-compatible metrics collection and endpoint
- **MaintenanceMiddleware**: Maintenance mode with IP/path/token bypass options

### Changed

- Updated version to 0.2.0
- Expanded test suite with 100+ tests

## [0.1.0] - 2026-01-17

### Added

- Initial release of FastMVC Middleware
- **CORSMiddleware**: Cross-origin resource sharing with sensible defaults
- **SecurityHeadersMiddleware**: Comprehensive security headers (CSP, HSTS, X-Frame-Options, etc.)
- **RateLimitMiddleware**: Sliding window rate limiting with configurable limits
- **AuthenticationMiddleware**: Pluggable authentication with JWT and API key backends
- **LoggingMiddleware**: Structured request/response logging
- **TimingMiddleware**: Request processing time tracking
- **RequestIDMiddleware**: Unique request identifier generation
- **RequestContextMiddleware**: Async-safe context variables for request tracking
- **FastMVCMiddleware**: Base class for creating custom middleware
- Comprehensive test suite
- Example applications
- Full documentation in README

### Features

- Python 3.10+ support
- Type hints throughout
- Fully async
- Zero required dependencies beyond Starlette
- Optional JWT support via PyJWT
- Configurable via dataclasses or keyword arguments
- Path and method exclusion support
- Standard rate limit headers (X-RateLimit-*)
- Standard security headers (OWASP recommended)
- Context variables for async-safe request tracking

[Unreleased]: https://github.com/shregar1/fastmvc-middleware/compare/v0.5.0...HEAD
[0.5.0]: https://github.com/shregar1/fastmvc-middleware/compare/v0.4.0...v0.5.0
[0.4.0]: https://github.com/shregar1/fastmvc-middleware/compare/v0.3.0...v0.4.0
[0.3.0]: https://github.com/shregar1/fastmvc-middleware/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/shregar1/fastmvc-middleware/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/shregar1/fastmvc-middleware/releases/tag/v0.1.0
