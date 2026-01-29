"""FastAPI application for DataCheck dashboard.

Provides REST API endpoints for monitoring data quality.

API Versioning:
    - All API endpoints are versioned under /api/v1/
    - Health and root endpoints remain unversioned
    - Future versions can be added as /api/v2/, etc.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Query, Depends, Request, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timedelta
import os

from datacheck import __version__
from datacheck.api.database import Database
from datacheck.api.auth import verify_api_key
from datacheck.api.logging_config import setup_logging, get_logger
from datacheck.api.middleware import (
    RequestLoggingMiddleware,
    SecurityHeadersMiddleware,
    global_exception_handler,
)
from datacheck.api.models import (
    ValidationSummary,
    ValidationDetail,
    ValidationResult,
    RuleResult,
    TrendData,
    TopIssue,
    Alert,
    AlertCreate,
    ValidationCreate,
    RuleResultCreate,
    MetricCreate,
    HealthResponse,
    APIInfo,
    ValidationStatus,
)

# Import rate limiting (optional dependency)
try:
    from slowapi import Limiter, _rate_limit_exceeded_handler
    from slowapi.util import get_remote_address
    from slowapi.errors import RateLimitExceeded
    RATE_LIMITING_AVAILABLE = True
except ImportError:
    RATE_LIMITING_AVAILABLE = False
    Limiter = None
    RateLimitExceeded = None

# Setup structured logging
log_level = os.getenv("LOG_LEVEL", "INFO")
log_format = os.getenv("LOG_FORMAT", "text")  # "text" or "json"
setup_logging(level=log_level, json_format=(log_format == "json"))

# Get logger for this module
logger = get_logger("api.app")


def create_app(db_path: str = None) -> FastAPI:
    """Create FastAPI application.

    Args:
        db_path: Path to database file

    Returns:
        FastAPI application instance
    """
    # Database instance
    db_file = db_path or os.environ.get("DATACHECK_DB", "datacheck.db")
    db = Database(db_file)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        """Application lifespan handler."""
        # Startup
        db.initialize()
        yield
        # Shutdown
        db.close()

    app = FastAPI(
        title="DataCheck API",
        description="REST API for DataCheck data quality monitoring dashboard",
        version=__version__,
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    # Configure rate limiting if available
    if RATE_LIMITING_AVAILABLE:
        # Get rate limit configuration from environment
        rate_limit_enabled = os.getenv("DATACHECK_RATE_LIMIT_ENABLED", "true").lower() == "true"

        if rate_limit_enabled:
            limiter = Limiter(key_func=get_remote_address)
            app.state.limiter = limiter
            app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
            logger.info("Rate limiting enabled")
        else:
            limiter = None
            logger.warning("Rate limiting disabled via configuration")
    else:
        limiter = None
        logger.warning("Rate limiting not available - install slowapi: pip install datacheck-cli[api]")

    # Add global exception handler
    app.add_exception_handler(Exception, global_exception_handler)

    # Add middleware (order matters - last added is executed first)
    # 1. Security headers (outermost)
    app.add_middleware(SecurityHeadersMiddleware)

    # 2. Request logging
    app.add_middleware(RequestLoggingMiddleware)

    # 3. CORS configuration (innermost, before request processing)
    allowed_origins_env = os.getenv("DATACHECK_ALLOWED_ORIGINS", "http://localhost:3000")
    allowed_origins = [origin.strip() for origin in allowed_origins_env.split(",") if origin.strip()]

    # Security check: don't allow wildcard with credentials
    if "*" in allowed_origins and len(allowed_origins) > 1:
        logger.warning("CORS misconfiguration: wildcard '*' cannot be combined with specific origins")
        allowed_origins = ["*"]

    # Log CORS configuration (security notice)
    if "*" in allowed_origins:
        logger.warning(
            "CORS configured with wildcard origin '*'. "
            "This is insecure for production. Set DATACHECK_ALLOWED_ORIGINS environment variable."
        )
    else:
        logger.info(f"CORS configured for origins: {', '.join(allowed_origins)}")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["Content-Type", "X-API-Key", "Authorization", "X-Request-ID"],
    )

    def get_db():
        """Dependency to get database instance."""
        return db

    # Root endpoint
    @app.get("/", response_model=APIInfo)
    async def root():
        """API root endpoint."""
        return APIInfo(
            name="DataCheck API",
            version=__version__,
            status="running",
            endpoints=[
                "/health",
                "/api/v1/validations",
                "/api/v1/validations/{id}",
                "/api/v1/validations/summary",
                "/api/v1/validations/trends",
                "/api/v1/validations/top-issues",
                "/api/v1/alerts",
                "/api/v1/metrics",
            ],
        )

    # Helper to apply rate limits
    def apply_rate_limit(limit_string: str):
        """Decorator to apply rate limits conditionally."""
        def decorator(func):
            if limiter:
                return limiter.limit(limit_string)(func)
            return func
        return decorator

    # Create v1 API router
    v1_router = APIRouter(prefix="/api/v1", tags=["v1"])

    # Health check
    @app.get("/health", response_model=HealthResponse)
    @apply_rate_limit("1000/minute")
    async def health_check(request: Request, database: Database = Depends(get_db)):
        """Health check endpoint.

        Rate limit: 1000 requests/minute (monitoring use case).
        """
        try:
            # Test database connection
            database.query("SELECT 1")
            db_status = "connected"
        except Exception:
            db_status = "disconnected"

        return HealthResponse(
            status="healthy" if db_status == "connected" else "degraded",
            version=__version__,
            database=db_status,
        )

    # Validation endpoints
    @v1_router.get("/validations", response_model=list[ValidationResult])
    @apply_rate_limit("100/minute")
    async def list_validations(
        request: Request,
        limit: int = Query(10, ge=1, le=100),
        offset: int = Query(0, ge=0),
        status: ValidationStatus | None = None,
        database: Database = Depends(get_db),
        api_key: str = Depends(verify_api_key),
    ):
        """List recent validations. Requires authentication.

        Rate limit: 100 requests/minute.
        """
        try:
            validations = database.get_recent_validations(limit=limit + offset)

            # Apply offset
            validations = validations[offset:offset + limit]

            # Filter by status if provided
            if status:
                validations = [v for v in validations if v.get("status") == status.value]

            return [
                ValidationResult(
                    id=v["id"],
                    filename=v["filename"],
                    source=v.get("source"),
                    status=ValidationStatus(v["status"]),
                    pass_rate=v.get("pass_rate"),
                    quality_score=v.get("quality_score"),
                    total_rows=v.get("total_rows"),
                    total_columns=v.get("total_columns"),
                    rules_run=v.get("rules_run"),
                    rules_passed=v.get("rules_passed"),
                    rules_failed=v.get("rules_failed"),
                    timestamp=v["timestamp"],
                    duration_seconds=v.get("duration_seconds"),
                )
                for v in validations
            ]

        except Exception:
            logger.error(f"API error in {request.url.path if 'request' in locals() else 'endpoint'}", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail="An error occurred processing your request. Please try again later."
            )

    @v1_router.get("/validations/summary", response_model=ValidationSummary)
    @apply_rate_limit("100/minute")
    async def get_validation_summary(
        request: Request,
        hours: int = Query(24, ge=1, le=720),
        database: Database = Depends(get_db),
        api_key: str = Depends(verify_api_key),
    ):
        """Get validation summary for last N hours. Requires authentication.

        Rate limit: 100 requests/minute.
        """
        try:
            since = datetime.utcnow() - timedelta(hours=hours)
            result = database.get_validation_summary(since=since)

            quality_label = _get_quality_label(result.get("avg_quality"))

            return ValidationSummary(
                total_checks=result.get("total_checks", 0) or 0,
                pass_rate=round(result.get("pass_rate", 0) or 0, 1),
                quality_score=quality_label,
                passed=result.get("passed", 0) or 0,
                failed=result.get("failed", 0) or 0,
                total_rows_checked=result.get("total_rows_checked", 0) or 0,
            )

        except Exception:
            logger.error(f"API error in {request.url.path if 'request' in locals() else 'endpoint'}", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail="An error occurred processing your request. Please try again later."
            )

    @v1_router.get("/validations/trends", response_model=list[TrendData])
    @apply_rate_limit("100/minute")
    async def get_validation_trends(
        request: Request,
        hours: int = Query(24, ge=1, le=720),
        group_by: str = Query("hour", pattern="^(hour|day|week)$"),
        database: Database = Depends(get_db),
        api_key: str = Depends(verify_api_key),
    ):
        """Get validation pass rate trends over time. Requires authentication.

        Rate limit: 100 requests/minute.
        """
        try:
            since = datetime.utcnow() - timedelta(hours=hours)
            results = database.get_trends(since=since, group_by=group_by)

            return [
                TrendData(
                    period=r["period"],
                    pass_rate=round(r["pass_rate"] or 0, 1),
                    count=r["count"],
                    avg_quality=r.get("avg_quality"),
                )
                for r in results
            ]

        except Exception:
            logger.error(f"API error in {request.url.path if 'request' in locals() else 'endpoint'}", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail="An error occurred processing your request. Please try again later."
            )

    @v1_router.get("/validations/top-issues", response_model=list[TopIssue])
    @apply_rate_limit("100/minute")
    async def get_top_issues(
        request: Request,
        limit: int = Query(10, ge=1, le=50),
        database: Database = Depends(get_db),
        api_key: str = Depends(verify_api_key),
    ):
        """Get most common validation failures. Requires authentication.

        Rate limit: 100 requests/minute.
        """
        try:
            results = database.get_top_issues(limit=limit)

            return [
                TopIssue(
                    rule_name=r["rule_name"],
                    rule_type=r.get("rule_type"),
                    column_name=r.get("column_name"),
                    failure_count=r["failure_count"],
                    avg_failed_rows=r["avg_failed_rows"] or 0,
                )
                for r in results
            ]

        except Exception:
            logger.error(f"API error in {request.url.path if 'request' in locals() else 'endpoint'}", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail="An error occurred processing your request. Please try again later."
            )

    @v1_router.get("/validations/{validation_id}", response_model=ValidationDetail)
    @apply_rate_limit("100/minute")
    async def get_validation_detail(
        request: Request,
        validation_id: int,
        database: Database = Depends(get_db),
        api_key: str = Depends(verify_api_key),
    ):
        """Get detailed validation results. Requires authentication.

        Rate limit: 100 requests/minute.
        """
        try:
            validation = database.get_validation(validation_id)

            if not validation:
                raise HTTPException(status_code=404, detail="Validation not found")

            rules = database.get_validation_rules(validation_id)

            return ValidationDetail(
                id=validation["id"],
                filename=validation["filename"],
                source=validation.get("source"),
                status=ValidationStatus(validation["status"]),
                pass_rate=validation.get("pass_rate"),
                quality_score=validation.get("quality_score"),
                total_rows=validation.get("total_rows"),
                total_columns=validation.get("total_columns"),
                rules_run=validation.get("rules_run"),
                rules_passed=validation.get("rules_passed"),
                rules_failed=validation.get("rules_failed"),
                timestamp=validation["timestamp"],
                duration_seconds=validation.get("duration_seconds"),
                rules=[
                    RuleResult(
                        id=r["id"],
                        rule_name=r["rule_name"],
                        rule_type=r.get("rule_type"),
                        column_name=r.get("column_name"),
                        status=ValidationStatus(r["status"]),
                        passed_rows=r.get("passed_rows", 0),
                        failed_rows=r.get("failed_rows", 0),
                        error_message=r.get("error_message"),
                    )
                    for r in rules
                ],
            )

        except HTTPException:
            raise
        except Exception:
            logger.error(f"API error in {request.url.path if 'request' in locals() else 'endpoint'}", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail="An error occurred processing your request. Please try again later."
            )

    @v1_router.post("/validations", response_model=ValidationResult)
    @apply_rate_limit("10/minute")
    async def create_validation(
        request: Request,
        validation: ValidationCreate,
        database: Database = Depends(get_db),
        api_key: str = Depends(verify_api_key),
    ):
        """Create a new validation record. Requires authentication.

        Rate limit: 10 requests/minute (write operation).
        """
        try:
            validation_id = database.insert_validation(validation.model_dump())

            return ValidationResult(
                id=validation_id,
                filename=validation.filename,
                source=validation.source,
                status=validation.status,
                pass_rate=validation.pass_rate,
                quality_score=validation.quality_score,
                total_rows=validation.total_rows,
                total_columns=validation.total_columns,
                rules_run=validation.rules_run,
                rules_passed=validation.rules_passed,
                rules_failed=validation.rules_failed,
                timestamp=datetime.utcnow(),
                duration_seconds=validation.duration_seconds,
            )

        except Exception:
            logger.error(f"API error in {request.url.path if 'request' in locals() else 'endpoint'}", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail="An error occurred processing your request. Please try again later."
            )

    @v1_router.post("/validations/{validation_id}/rules", response_model=RuleResult)
    @apply_rate_limit("10/minute")
    async def create_rule_result(
        request: Request,
        validation_id: int,
        rule: RuleResultCreate,
        database: Database = Depends(get_db),
        api_key: str = Depends(verify_api_key),
    ):
        """Create a rule result for a validation. Requires authentication.

        Rate limit: 10 requests/minute (write operation).
        """
        try:
            # Verify validation exists
            validation = database.get_validation(validation_id)
            if not validation:
                raise HTTPException(status_code=404, detail="Validation not found")

            rule_data = rule.model_dump()
            rule_data["validation_id"] = validation_id
            rule_id = database.insert_rule_result(rule_data)

            return RuleResult(
                id=rule_id,
                rule_name=rule.rule_name,
                rule_type=rule.rule_type,
                column_name=rule.column_name,
                status=rule.status,
                passed_rows=rule.passed_rows,
                failed_rows=rule.failed_rows,
                error_message=rule.error_message,
            )

        except HTTPException:
            raise
        except Exception:
            logger.error(f"API error in {request.url.path if 'request' in locals() else 'endpoint'}", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail="An error occurred processing your request. Please try again later."
            )

    # Alert endpoints
    @v1_router.get("/alerts", response_model=list[Alert])
    @apply_rate_limit("100/minute")
    async def list_alerts(
        request: Request,
        hours: int = Query(24, ge=1, le=720),
        unacknowledged_only: bool = Query(False),
        limit: int = Query(50, ge=1, le=200),
        database: Database = Depends(get_db),
        api_key: str = Depends(verify_api_key),
    ):
        """List alerts. Requires authentication.

        Rate limit: 100 requests/minute.
        """
        try:
            since = datetime.utcnow() - timedelta(hours=hours)
            results = database.get_alerts(
                since=since,
                unacknowledged_only=unacknowledged_only,
                limit=limit,
            )

            return [
                Alert(
                    id=r["id"],
                    validation_id=r.get("validation_id"),
                    severity=r["severity"],
                    title=r["title"],
                    message=r["message"],
                    source=r.get("source"),
                    timestamp=r["timestamp"],
                    acknowledged=bool(r.get("acknowledged")),
                    acknowledged_at=r.get("acknowledged_at"),
                )
                for r in results
            ]

        except Exception:
            logger.error(f"API error in {request.url.path if 'request' in locals() else 'endpoint'}", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail="An error occurred processing your request. Please try again later."
            )

    @v1_router.post("/alerts", response_model=Alert)
    @apply_rate_limit("10/minute")
    async def create_alert(
        request: Request,
        alert: AlertCreate,
        database: Database = Depends(get_db),
        api_key: str = Depends(verify_api_key),
    ):
        """Create a new alert. Requires authentication.

        Rate limit: 10 requests/minute (write operation).
        """
        try:
            alert_id = database.insert_alert(alert.model_dump())

            return Alert(
                id=alert_id,
                validation_id=alert.validation_id,
                severity=alert.severity,
                title=alert.title,
                message=alert.message,
                source=alert.source,
                timestamp=datetime.utcnow(),
                acknowledged=False,
            )

        except Exception:
            logger.error(f"API error in {request.url.path if 'request' in locals() else 'endpoint'}", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail="An error occurred processing your request. Please try again later."
            )

    @v1_router.post("/alerts/{alert_id}/acknowledge")
    @apply_rate_limit("10/minute")
    async def acknowledge_alert(
        request: Request,
        alert_id: int,
        database: Database = Depends(get_db),
        api_key: str = Depends(verify_api_key),
    ):
        """Acknowledge an alert. Requires authentication.

        Rate limit: 10 requests/minute (write operation).
        """
        try:
            success = database.acknowledge_alert(alert_id)

            if not success:
                raise HTTPException(status_code=404, detail="Alert not found")

            return {"status": "acknowledged", "alert_id": alert_id}

        except HTTPException:
            raise
        except Exception:
            logger.error(f"API error in {request.url.path if 'request' in locals() else 'endpoint'}", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail="An error occurred processing your request. Please try again later."
            )

    # Metrics endpoints
    @v1_router.post("/metrics")
    @apply_rate_limit("10/minute")
    async def create_metric(
        request: Request,
        metric: MetricCreate,
        database: Database = Depends(get_db),
        api_key: str = Depends(verify_api_key),
    ):
        """Record a metric. Requires authentication.

        Rate limit: 10 requests/minute (write operation).
        """
        try:
            metric_id = database.insert_metric(
                name=metric.name,
                value=metric.value,
                source=metric.source,
            )

            return {"status": "created", "metric_id": metric_id}

        except Exception:
            logger.error(f"API error in {request.url.path if 'request' in locals() else 'endpoint'}", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail="An error occurred processing your request. Please try again later."
            )

    # Register v1 router
    app.include_router(v1_router)

    return app


def _get_quality_label(score: float | None) -> str:
    """Convert quality score to label."""
    if score is None:
        return "Unknown"
    elif score >= 95:
        return "Excellent"
    elif score >= 85:
        return "Good"
    elif score >= 70:
        return "Fair"
    else:
        return "Poor"


# Default app instance
app = create_app()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
