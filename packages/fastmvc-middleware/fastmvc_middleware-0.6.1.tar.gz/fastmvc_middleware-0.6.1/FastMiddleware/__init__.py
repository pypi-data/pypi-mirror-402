"""
FastMVC Middleware - Production-ready middlewares for FastAPI applications.

A comprehensive collection of 90+ battle-tested, configurable middleware components
for building robust FastAPI/Starlette applications.
"""

from FastMiddleware.ab_testing import (
    ABTestConfig,
    ABTestMiddleware,
    Experiment,
    get_variant,
)
from FastMiddleware.accept_language import (
    AcceptLanguageConfig,
    AcceptLanguageMiddleware,
    get_language,
)
from FastMiddleware.api_version_header import APIVersionHeaderConfig, APIVersionHeaderMiddleware
from FastMiddleware.audit import AuditConfig, AuditEvent, AuditMiddleware

# ============================================================================
# Authentication & Authorization
# ============================================================================
from FastMiddleware.authentication import (
    APIKeyAuthBackend,
    AuthBackend,
    AuthConfig,
    AuthenticationMiddleware,
    JWTAuthBackend,
)
from FastMiddleware.bandwidth import BandwidthConfig, BandwidthMiddleware
from FastMiddleware.base import FastMVCMiddleware
from FastMiddleware.basic_auth import BasicAuthConfig, BasicAuthMiddleware
from FastMiddleware.bearer_auth import BearerAuthConfig, BearerAuthMiddleware

# ============================================================================
# Detection & Analytics
# ============================================================================
from FastMiddleware.bot_detection import BotAction, BotConfig, BotDetectionMiddleware
from FastMiddleware.bulkhead import BulkheadConfig, BulkheadMiddleware
from FastMiddleware.cache import CacheConfig, CacheMiddleware
from FastMiddleware.chaos import ChaosConfig, ChaosMiddleware
from FastMiddleware.circuit_breaker import (
    CircuitBreakerConfig,
    CircuitBreakerMiddleware,
    CircuitState,
)
from FastMiddleware.client_hints import (
    ClientHintsConfig,
    ClientHintsMiddleware,
    get_client_hints,
)

# ============================================================================
# Response Handling
# ============================================================================
from FastMiddleware.compression import CompressionConfig, CompressionMiddleware
from FastMiddleware.conditional_request import (
    ConditionalRequestConfig,
    ConditionalRequestMiddleware,
)
from FastMiddleware.content_negotiation import (
    ContentNegotiationConfig,
    ContentNegotiationMiddleware,
    get_negotiated_type,
)
from FastMiddleware.content_type import ContentTypeConfig, ContentTypeMiddleware
from FastMiddleware.context import (
    ContextConfig,
    ContextMiddleware,
    get_context,
    get_context_value,
    set_context_value,
)
from FastMiddleware.correlation import (
    CorrelationConfig,
    CorrelationMiddleware,
    get_correlation_id,
)

# ============================================================================
# Core Middlewares
# ============================================================================
from FastMiddleware.cors import CORSMiddleware
from FastMiddleware.cost_tracking import (
    CostTrackingConfig,
    CostTrackingMiddleware,
    add_cost,
    get_request_cost,
)
from FastMiddleware.csp_report import CSPReportConfig, CSPReportMiddleware
from FastMiddleware.csrf import CSRFConfig, CSRFMiddleware
from FastMiddleware.data_masking import DataMaskingConfig, DataMaskingMiddleware, MaskingRule
from FastMiddleware.deprecation import DeprecationConfig, DeprecationInfo, DeprecationMiddleware
from FastMiddleware.early_hints import EarlyHint, EarlyHintsConfig, EarlyHintsMiddleware

# ============================================================================
# Error Handling
# ============================================================================
from FastMiddleware.error_handler import ErrorConfig, ErrorHandlerMiddleware
from FastMiddleware.etag import ETagConfig, ETagMiddleware
from FastMiddleware.exception_handler import ExceptionHandlerConfig, ExceptionHandlerMiddleware

# ============================================================================
# Feature Management & Testing
# ============================================================================
from FastMiddleware.feature_flag import (
    FeatureFlagConfig,
    FeatureFlagMiddleware,
    get_feature_flags,
    is_feature_enabled,
)
from FastMiddleware.geoip import GeoIPConfig, GeoIPMiddleware, get_geo_data
from FastMiddleware.graceful_shutdown import GracefulShutdownConfig, GracefulShutdownMiddleware
from FastMiddleware.hateoas import HATEOASConfig, HATEOASMiddleware, Link
from FastMiddleware.header_transform import HeaderTransformConfig, HeaderTransformMiddleware

# ============================================================================
# Health & Monitoring
# ============================================================================
from FastMiddleware.health import HealthCheckMiddleware, HealthConfig
from FastMiddleware.honeypot import HoneypotConfig, HoneypotMiddleware
from FastMiddleware.https_redirect import HTTPSRedirectConfig, HTTPSRedirectMiddleware

# ============================================================================
# Idempotency
# ============================================================================
from FastMiddleware.idempotency import (
    IdempotencyConfig,
    IdempotencyMiddleware,
    IdempotencyStore,
    InMemoryIdempotencyStore,
)
from FastMiddleware.ip_filter import IPFilterConfig, IPFilterMiddleware
from FastMiddleware.json_schema import JSONSchemaConfig, JSONSchemaMiddleware
from FastMiddleware.load_shedding import LoadSheddingConfig, LoadSheddingMiddleware

# ============================================================================
# Localization & Content Negotiation
# ============================================================================
from FastMiddleware.locale import LocaleConfig, LocaleMiddleware, get_locale
from FastMiddleware.logging import LoggingMiddleware

# ============================================================================
# Maintenance & Lifecycle
# ============================================================================
from FastMiddleware.maintenance import MaintenanceConfig, MaintenanceMiddleware
from FastMiddleware.method_override import MethodOverrideConfig, MethodOverrideMiddleware
from FastMiddleware.metrics import MetricsCollector, MetricsConfig, MetricsMiddleware
from FastMiddleware.no_cache import NoCacheConfig, NoCacheMiddleware
from FastMiddleware.origin import OriginConfig, OriginMiddleware
from FastMiddleware.path_rewrite import PathRewriteConfig, PathRewriteMiddleware, RewriteRule
from FastMiddleware.payload_size import PayloadSizeConfig, PayloadSizeMiddleware
from FastMiddleware.permissions_policy import PermissionsPolicyConfig, PermissionsPolicyMiddleware
from FastMiddleware.profiling import ProfilingConfig, ProfilingMiddleware
from FastMiddleware.proxy import ProxyConfig, ProxyMiddleware, ProxyRoute
from FastMiddleware.quota import QuotaConfig, QuotaMiddleware

# ============================================================================
# Rate Limiting & Protection
# ============================================================================
from FastMiddleware.rate_limit import (
    InMemoryRateLimitStore,
    RateLimitConfig,
    RateLimitMiddleware,
    RateLimitStore,
)

# ============================================================================
# IP & Proxy Handling
# ============================================================================
from FastMiddleware.real_ip import RealIPConfig, RealIPMiddleware, get_real_ip

# ============================================================================
# URL & Routing
# ============================================================================
from FastMiddleware.redirect import RedirectConfig, RedirectMiddleware, RedirectRule
from FastMiddleware.referrer_policy import ReferrerPolicyConfig, ReferrerPolicyMiddleware
from FastMiddleware.replay_prevention import ReplayPreventionConfig, ReplayPreventionMiddleware
from FastMiddleware.request_coalescing import CoalescingConfig, RequestCoalescingMiddleware
from FastMiddleware.request_context import (
    RequestContextMiddleware,
    get_request_context,
    get_request_id,
)
from FastMiddleware.request_dedup import RequestDedupConfig, RequestDedupMiddleware
from FastMiddleware.request_fingerprint import (
    FingerprintConfig,
    RequestFingerprintMiddleware,
    get_fingerprint,
)
from FastMiddleware.request_id import RequestIDMiddleware
from FastMiddleware.request_id_propagation import (
    RequestIDPropagationConfig,
    RequestIDPropagationMiddleware,
    get_request_ids,
    get_trace_header,
)
from FastMiddleware.request_limit import RequestLimitConfig, RequestLimitMiddleware
from FastMiddleware.request_logger import RequestLoggerConfig, RequestLoggerMiddleware
from FastMiddleware.request_priority import Priority, PriorityConfig, RequestPriorityMiddleware
from FastMiddleware.request_sampler import (
    RequestSamplerConfig,
    RequestSamplerMiddleware,
    is_sampled,
)
from FastMiddleware.request_signing import RequestSigningConfig, RequestSigningMiddleware
from FastMiddleware.request_validator import (
    RequestValidatorConfig,
    RequestValidatorMiddleware,
    ValidationRule,
)
from FastMiddleware.response_cache import ResponseCacheConfig, ResponseCacheMiddleware
from FastMiddleware.response_format import ResponseFormatConfig, ResponseFormatMiddleware
from FastMiddleware.response_signature import ResponseSignatureConfig, ResponseSignatureMiddleware
from FastMiddleware.response_time import ResponseTimeConfig, ResponseTimeMiddleware, ResponseTimeSLA
from FastMiddleware.retry_after import RetryAfterConfig, RetryAfterMiddleware
from FastMiddleware.route_auth import RouteAuth, RouteAuthConfig, RouteAuthMiddleware
from FastMiddleware.sanitization import SanitizationConfig, SanitizationMiddleware
from FastMiddleware.scope import ScopeConfig, ScopeMiddleware

# ============================================================================
# Security Middlewares
# ============================================================================
from FastMiddleware.security import SecurityHeadersConfig, SecurityHeadersMiddleware
from FastMiddleware.server_timing import (
    ServerTimingConfig,
    ServerTimingMiddleware,
    add_timing,
    timing,
)

# ============================================================================
# Session & Context
# ============================================================================
from FastMiddleware.session import (
    InMemorySessionStore,
    Session,
    SessionConfig,
    SessionMiddleware,
    SessionStore,
)
from FastMiddleware.slow_response import SlowResponseConfig, SlowResponseMiddleware
from FastMiddleware.tenant import (
    TenantConfig,
    TenantMiddleware,
    get_tenant,
    get_tenant_id,
)

# ============================================================================
# Request Processing
# ============================================================================
from FastMiddleware.timeout import TimeoutConfig, TimeoutMiddleware
from FastMiddleware.timing import TimingMiddleware
from FastMiddleware.trailing_slash import SlashAction, TrailingSlashConfig, TrailingSlashMiddleware
from FastMiddleware.trusted_host import TrustedHostMiddleware
from FastMiddleware.user_agent import (
    UserAgentConfig,
    UserAgentInfo,
    UserAgentMiddleware,
    get_user_agent,
)

# ============================================================================
# API Management
# ============================================================================
from FastMiddleware.versioning import (
    VersioningConfig,
    VersioningMiddleware,
    VersionLocation,
    get_api_version,
)
from FastMiddleware.warmup import WarmupConfig, WarmupMiddleware
from FastMiddleware.webhook import WebhookConfig, WebhookMiddleware
from FastMiddleware.xff_trust import XFFTrustConfig, XFFTrustMiddleware


__version__ = "0.5.0"
__author__ = "Shiv"
__email__ = "shiv@hyyre.dev"
__license__ = "MIT"
__url__ = "https://github.com/hyyre/fastmvc-middleware"

__all__ = [
    # Base
    "FastMVCMiddleware",
    # Core
    "CORSMiddleware",
    "LoggingMiddleware",
    "TimingMiddleware",
    "RequestIDMiddleware",
    # Security
    "SecurityHeadersMiddleware",
    "SecurityHeadersConfig",
    "TrustedHostMiddleware",
    "CSRFMiddleware",
    "CSRFConfig",
    "HTTPSRedirectMiddleware",
    "HTTPSRedirectConfig",
    "IPFilterMiddleware",
    "IPFilterConfig",
    "OriginMiddleware",
    "OriginConfig",
    "WebhookMiddleware",
    "WebhookConfig",
    "ReferrerPolicyMiddleware",
    "ReferrerPolicyConfig",
    "PermissionsPolicyMiddleware",
    "PermissionsPolicyConfig",
    "CSPReportMiddleware",
    "CSPReportConfig",
    "ReplayPreventionMiddleware",
    "ReplayPreventionConfig",
    "RequestSigningMiddleware",
    "RequestSigningConfig",
    "HoneypotMiddleware",
    "HoneypotConfig",
    "SanitizationMiddleware",
    "SanitizationConfig",
    # Rate Limiting & Protection
    "RateLimitMiddleware",
    "RateLimitConfig",
    "RateLimitStore",
    "InMemoryRateLimitStore",
    "QuotaMiddleware",
    "QuotaConfig",
    "LoadSheddingMiddleware",
    "LoadSheddingConfig",
    "BulkheadMiddleware",
    "BulkheadConfig",
    "RequestDedupMiddleware",
    "RequestDedupConfig",
    "RequestCoalescingMiddleware",
    "CoalescingConfig",
    # Authentication
    "AuthenticationMiddleware",
    "AuthConfig",
    "AuthBackend",
    "JWTAuthBackend",
    "APIKeyAuthBackend",
    "BasicAuthMiddleware",
    "BasicAuthConfig",
    "BearerAuthMiddleware",
    "BearerAuthConfig",
    "ScopeMiddleware",
    "ScopeConfig",
    "RouteAuthMiddleware",
    "RouteAuthConfig",
    "RouteAuth",
    # Session & Context
    "SessionMiddleware",
    "SessionConfig",
    "SessionStore",
    "InMemorySessionStore",
    "Session",
    "RequestContextMiddleware",
    "get_request_id",
    "get_request_context",
    "CorrelationMiddleware",
    "CorrelationConfig",
    "get_correlation_id",
    "TenantMiddleware",
    "TenantConfig",
    "get_tenant",
    "get_tenant_id",
    "ContextMiddleware",
    "ContextConfig",
    "get_context",
    "get_context_value",
    "set_context_value",
    "RequestIDPropagationMiddleware",
    "RequestIDPropagationConfig",
    "get_request_ids",
    "get_trace_header",
    # Response Handling
    "CompressionMiddleware",
    "CompressionConfig",
    "ResponseFormatMiddleware",
    "ResponseFormatConfig",
    "CacheMiddleware",
    "CacheConfig",
    "ETagMiddleware",
    "ETagConfig",
    "DataMaskingMiddleware",
    "DataMaskingConfig",
    "MaskingRule",
    "ResponseCacheMiddleware",
    "ResponseCacheConfig",
    "ResponseSignatureMiddleware",
    "ResponseSignatureConfig",
    "HATEOASMiddleware",
    "HATEOASConfig",
    "Link",
    "BandwidthMiddleware",
    "BandwidthConfig",
    "NoCacheMiddleware",
    "NoCacheConfig",
    "ConditionalRequestMiddleware",
    "ConditionalRequestConfig",
    "EarlyHintsMiddleware",
    "EarlyHintsConfig",
    "EarlyHint",
    # Error Handling
    "ErrorHandlerMiddleware",
    "ErrorConfig",
    "CircuitBreakerMiddleware",
    "CircuitBreakerConfig",
    "CircuitState",
    "ExceptionHandlerMiddleware",
    "ExceptionHandlerConfig",
    # Health & Monitoring
    "HealthCheckMiddleware",
    "HealthConfig",
    "MetricsMiddleware",
    "MetricsConfig",
    "MetricsCollector",
    "ProfilingMiddleware",
    "ProfilingConfig",
    "AuditMiddleware",
    "AuditConfig",
    "AuditEvent",
    "ResponseTimeMiddleware",
    "ResponseTimeConfig",
    "ResponseTimeSLA",
    "ServerTimingMiddleware",
    "ServerTimingConfig",
    "timing",
    "add_timing",
    "RequestLoggerMiddleware",
    "RequestLoggerConfig",
    "CostTrackingMiddleware",
    "CostTrackingConfig",
    "get_request_cost",
    "add_cost",
    "RequestSamplerMiddleware",
    "RequestSamplerConfig",
    "is_sampled",
    # Idempotency
    "IdempotencyMiddleware",
    "IdempotencyConfig",
    "IdempotencyStore",
    "InMemoryIdempotencyStore",
    # Maintenance & Lifecycle
    "MaintenanceMiddleware",
    "MaintenanceConfig",
    "WarmupMiddleware",
    "WarmupConfig",
    "GracefulShutdownMiddleware",
    "GracefulShutdownConfig",
    "ChaosMiddleware",
    "ChaosConfig",
    "SlowResponseMiddleware",
    "SlowResponseConfig",
    # Request Processing
    "TimeoutMiddleware",
    "TimeoutConfig",
    "RequestLimitMiddleware",
    "RequestLimitConfig",
    "TrailingSlashMiddleware",
    "TrailingSlashConfig",
    "SlashAction",
    "ContentTypeMiddleware",
    "ContentTypeConfig",
    "HeaderTransformMiddleware",
    "HeaderTransformConfig",
    "RequestValidatorMiddleware",
    "RequestValidatorConfig",
    "ValidationRule",
    "JSONSchemaMiddleware",
    "JSONSchemaConfig",
    "PayloadSizeMiddleware",
    "PayloadSizeConfig",
    "MethodOverrideMiddleware",
    "MethodOverrideConfig",
    "RequestFingerprintMiddleware",
    "FingerprintConfig",
    "get_fingerprint",
    "RequestPriorityMiddleware",
    "PriorityConfig",
    "Priority",
    # URL & Routing
    "RedirectMiddleware",
    "RedirectConfig",
    "RedirectRule",
    "PathRewriteMiddleware",
    "PathRewriteConfig",
    "RewriteRule",
    "ProxyMiddleware",
    "ProxyConfig",
    "ProxyRoute",
    # API Management
    "VersioningMiddleware",
    "VersioningConfig",
    "VersionLocation",
    "get_api_version",
    "DeprecationMiddleware",
    "DeprecationConfig",
    "DeprecationInfo",
    "RetryAfterMiddleware",
    "RetryAfterConfig",
    "APIVersionHeaderMiddleware",
    "APIVersionHeaderConfig",
    # Detection & Analytics
    "BotDetectionMiddleware",
    "BotConfig",
    "BotAction",
    "GeoIPMiddleware",
    "GeoIPConfig",
    "get_geo_data",
    "UserAgentMiddleware",
    "UserAgentConfig",
    "UserAgentInfo",
    "get_user_agent",
    # Feature Management & Testing
    "FeatureFlagMiddleware",
    "FeatureFlagConfig",
    "get_feature_flags",
    "is_feature_enabled",
    "ABTestMiddleware",
    "ABTestConfig",
    "Experiment",
    "get_variant",
    # Localization & Content Negotiation
    "LocaleMiddleware",
    "LocaleConfig",
    "get_locale",
    "AcceptLanguageMiddleware",
    "AcceptLanguageConfig",
    "get_language",
    "ContentNegotiationMiddleware",
    "ContentNegotiationConfig",
    "get_negotiated_type",
    "ClientHintsMiddleware",
    "ClientHintsConfig",
    "get_client_hints",
    # IP & Proxy Handling
    "RealIPMiddleware",
    "RealIPConfig",
    "get_real_ip",
    "XFFTrustMiddleware",
    "XFFTrustConfig",
]
