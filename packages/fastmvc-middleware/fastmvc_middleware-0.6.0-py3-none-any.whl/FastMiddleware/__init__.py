"""
FastMVC Middleware - Production-ready middlewares for FastAPI applications.

A comprehensive collection of 90+ battle-tested, configurable middleware components
for building robust FastAPI/Starlette applications.
"""

from FastMiddleware.base import FastMVCMiddleware

# ============================================================================
# Core Middlewares
# ============================================================================
from FastMiddleware.cors import CORSMiddleware
from FastMiddleware.logging import LoggingMiddleware
from FastMiddleware.timing import TimingMiddleware
from FastMiddleware.request_id import RequestIDMiddleware

# ============================================================================
# Security Middlewares
# ============================================================================
from FastMiddleware.security import SecurityHeadersMiddleware, SecurityHeadersConfig
from FastMiddleware.trusted_host import TrustedHostMiddleware
from FastMiddleware.csrf import CSRFMiddleware, CSRFConfig
from FastMiddleware.https_redirect import HTTPSRedirectMiddleware, HTTPSRedirectConfig
from FastMiddleware.ip_filter import IPFilterMiddleware, IPFilterConfig
from FastMiddleware.origin import OriginMiddleware, OriginConfig
from FastMiddleware.webhook import WebhookMiddleware, WebhookConfig
from FastMiddleware.referrer_policy import ReferrerPolicyMiddleware, ReferrerPolicyConfig
from FastMiddleware.permissions_policy import PermissionsPolicyMiddleware, PermissionsPolicyConfig
from FastMiddleware.csp_report import CSPReportMiddleware, CSPReportConfig
from FastMiddleware.replay_prevention import ReplayPreventionMiddleware, ReplayPreventionConfig
from FastMiddleware.request_signing import RequestSigningMiddleware, RequestSigningConfig
from FastMiddleware.honeypot import HoneypotMiddleware, HoneypotConfig
from FastMiddleware.sanitization import SanitizationMiddleware, SanitizationConfig

# ============================================================================
# Rate Limiting & Protection
# ============================================================================
from FastMiddleware.rate_limit import (
    RateLimitMiddleware,
    RateLimitConfig,
    RateLimitStore,
    InMemoryRateLimitStore,
)
from FastMiddleware.quota import QuotaMiddleware, QuotaConfig
from FastMiddleware.load_shedding import LoadSheddingMiddleware, LoadSheddingConfig
from FastMiddleware.bulkhead import BulkheadMiddleware, BulkheadConfig
from FastMiddleware.request_dedup import RequestDedupMiddleware, RequestDedupConfig
from FastMiddleware.request_coalescing import RequestCoalescingMiddleware, CoalescingConfig

# ============================================================================
# Authentication & Authorization
# ============================================================================
from FastMiddleware.authentication import (
    AuthenticationMiddleware,
    AuthConfig,
    AuthBackend,
    JWTAuthBackend,
    APIKeyAuthBackend,
)
from FastMiddleware.basic_auth import BasicAuthMiddleware, BasicAuthConfig
from FastMiddleware.bearer_auth import BearerAuthMiddleware, BearerAuthConfig
from FastMiddleware.scope import ScopeMiddleware, ScopeConfig
from FastMiddleware.route_auth import RouteAuthMiddleware, RouteAuthConfig, RouteAuth

# ============================================================================
# Session & Context
# ============================================================================
from FastMiddleware.session import (
    SessionMiddleware,
    SessionConfig,
    SessionStore,
    InMemorySessionStore,
    Session,
)
from FastMiddleware.request_context import (
    RequestContextMiddleware,
    get_request_id,
    get_request_context,
)
from FastMiddleware.correlation import (
    CorrelationMiddleware,
    CorrelationConfig,
    get_correlation_id,
)
from FastMiddleware.tenant import (
    TenantMiddleware,
    TenantConfig,
    get_tenant,
    get_tenant_id,
)
from FastMiddleware.context import (
    ContextMiddleware,
    ContextConfig,
    get_context,
    get_context_value,
    set_context_value,
)
from FastMiddleware.request_id_propagation import (
    RequestIDPropagationMiddleware,
    RequestIDPropagationConfig,
    get_request_ids,
    get_trace_header,
)

# ============================================================================
# Response Handling
# ============================================================================
from FastMiddleware.compression import CompressionMiddleware, CompressionConfig
from FastMiddleware.response_format import ResponseFormatMiddleware, ResponseFormatConfig
from FastMiddleware.cache import CacheMiddleware, CacheConfig
from FastMiddleware.etag import ETagMiddleware, ETagConfig
from FastMiddleware.data_masking import DataMaskingMiddleware, DataMaskingConfig, MaskingRule
from FastMiddleware.response_cache import ResponseCacheMiddleware, ResponseCacheConfig
from FastMiddleware.response_signature import ResponseSignatureMiddleware, ResponseSignatureConfig
from FastMiddleware.hateoas import HATEOASMiddleware, HATEOASConfig, Link
from FastMiddleware.bandwidth import BandwidthMiddleware, BandwidthConfig
from FastMiddleware.no_cache import NoCacheMiddleware, NoCacheConfig
from FastMiddleware.conditional_request import ConditionalRequestMiddleware, ConditionalRequestConfig
from FastMiddleware.early_hints import EarlyHintsMiddleware, EarlyHintsConfig, EarlyHint

# ============================================================================
# Error Handling
# ============================================================================
from FastMiddleware.error_handler import ErrorHandlerMiddleware, ErrorConfig
from FastMiddleware.circuit_breaker import CircuitBreakerMiddleware, CircuitBreakerConfig, CircuitState
from FastMiddleware.exception_handler import ExceptionHandlerMiddleware, ExceptionHandlerConfig

# ============================================================================
# Health & Monitoring
# ============================================================================
from FastMiddleware.health import HealthCheckMiddleware, HealthConfig
from FastMiddleware.metrics import MetricsMiddleware, MetricsConfig, MetricsCollector
from FastMiddleware.profiling import ProfilingMiddleware, ProfilingConfig
from FastMiddleware.audit import AuditMiddleware, AuditConfig, AuditEvent
from FastMiddleware.response_time import ResponseTimeMiddleware, ResponseTimeConfig, ResponseTimeSLA
from FastMiddleware.server_timing import (
    ServerTimingMiddleware,
    ServerTimingConfig,
    timing,
    add_timing,
)
from FastMiddleware.request_logger import RequestLoggerMiddleware, RequestLoggerConfig
from FastMiddleware.cost_tracking import (
    CostTrackingMiddleware,
    CostTrackingConfig,
    get_request_cost,
    add_cost,
)
from FastMiddleware.request_sampler import (
    RequestSamplerMiddleware,
    RequestSamplerConfig,
    is_sampled,
)

# ============================================================================
# Idempotency
# ============================================================================
from FastMiddleware.idempotency import (
    IdempotencyMiddleware,
    IdempotencyConfig,
    IdempotencyStore,
    InMemoryIdempotencyStore,
)

# ============================================================================
# Maintenance & Lifecycle
# ============================================================================
from FastMiddleware.maintenance import MaintenanceMiddleware, MaintenanceConfig
from FastMiddleware.warmup import WarmupMiddleware, WarmupConfig
from FastMiddleware.graceful_shutdown import GracefulShutdownMiddleware, GracefulShutdownConfig
from FastMiddleware.chaos import ChaosMiddleware, ChaosConfig
from FastMiddleware.slow_response import SlowResponseMiddleware, SlowResponseConfig

# ============================================================================
# Request Processing
# ============================================================================
from FastMiddleware.timeout import TimeoutMiddleware, TimeoutConfig
from FastMiddleware.request_limit import RequestLimitMiddleware, RequestLimitConfig
from FastMiddleware.trailing_slash import TrailingSlashMiddleware, TrailingSlashConfig, SlashAction
from FastMiddleware.content_type import ContentTypeMiddleware, ContentTypeConfig
from FastMiddleware.header_transform import HeaderTransformMiddleware, HeaderTransformConfig
from FastMiddleware.request_validator import RequestValidatorMiddleware, RequestValidatorConfig, ValidationRule
from FastMiddleware.json_schema import JSONSchemaMiddleware, JSONSchemaConfig
from FastMiddleware.payload_size import PayloadSizeMiddleware, PayloadSizeConfig
from FastMiddleware.method_override import MethodOverrideMiddleware, MethodOverrideConfig
from FastMiddleware.request_fingerprint import (
    RequestFingerprintMiddleware,
    FingerprintConfig,
    get_fingerprint,
)
from FastMiddleware.request_priority import RequestPriorityMiddleware, PriorityConfig, Priority

# ============================================================================
# URL & Routing
# ============================================================================
from FastMiddleware.redirect import RedirectMiddleware, RedirectConfig, RedirectRule
from FastMiddleware.path_rewrite import PathRewriteMiddleware, PathRewriteConfig, RewriteRule
from FastMiddleware.proxy import ProxyMiddleware, ProxyConfig, ProxyRoute

# ============================================================================
# API Management
# ============================================================================
from FastMiddleware.versioning import (
    VersioningMiddleware,
    VersioningConfig,
    VersionLocation,
    get_api_version,
)
from FastMiddleware.deprecation import DeprecationMiddleware, DeprecationConfig, DeprecationInfo
from FastMiddleware.retry_after import RetryAfterMiddleware, RetryAfterConfig
from FastMiddleware.api_version_header import APIVersionHeaderMiddleware, APIVersionHeaderConfig

# ============================================================================
# Detection & Analytics
# ============================================================================
from FastMiddleware.bot_detection import BotDetectionMiddleware, BotConfig, BotAction
from FastMiddleware.geoip import GeoIPMiddleware, GeoIPConfig, get_geo_data
from FastMiddleware.user_agent import (
    UserAgentMiddleware,
    UserAgentConfig,
    UserAgentInfo,
    get_user_agent,
)

# ============================================================================
# Feature Management & Testing
# ============================================================================
from FastMiddleware.feature_flag import (
    FeatureFlagMiddleware,
    FeatureFlagConfig,
    get_feature_flags,
    is_feature_enabled,
)
from FastMiddleware.ab_testing import (
    ABTestMiddleware,
    ABTestConfig,
    Experiment,
    get_variant,
)

# ============================================================================
# Localization & Content Negotiation
# ============================================================================
from FastMiddleware.locale import LocaleMiddleware, LocaleConfig, get_locale
from FastMiddleware.accept_language import (
    AcceptLanguageMiddleware,
    AcceptLanguageConfig,
    get_language,
)
from FastMiddleware.content_negotiation import (
    ContentNegotiationMiddleware,
    ContentNegotiationConfig,
    get_negotiated_type,
)
from FastMiddleware.client_hints import (
    ClientHintsMiddleware,
    ClientHintsConfig,
    get_client_hints,
)

# ============================================================================
# IP & Proxy Handling
# ============================================================================
from FastMiddleware.real_ip import RealIPMiddleware, RealIPConfig, get_real_ip
from FastMiddleware.xff_trust import XFFTrustMiddleware, XFFTrustConfig

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
