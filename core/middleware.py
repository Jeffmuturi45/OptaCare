import redis as _redis_lib
import json
import time
import logging
from django.conf import settings
from django.http import JsonResponse
from django.utils import timezone
from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger(__name__)

SAFE_METHODS = {'GET', 'HEAD', 'OPTIONS', 'TRACE'}
AUDIT_EXEMPT_PATHS = {'/favicon.ico', '/static/', '/media/'}
SENSITIVE_KEYS = {'password', 'token', 'secret', 'key', 'authorization',
                  'mpesa_passkey', 'consumer_secret'}


def _sanitize(payload: dict) -> dict:
    if not isinstance(payload, dict):
        return {}
    return {
        k: '***' if any(s in k.lower() for s in SENSITIVE_KEYS) else v
        for k, v in payload.items()
    }


def _get_client_ip(request):
    xff = request.META.get('HTTP_X_FORWARDED_FOR')
    if xff:
        return xff.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR', '')


# ── 1. Security Headers ───────────────────────────────────────────────────────

class SecurityHeadersMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        response['X-Frame-Options'] = 'DENY'
        response['X-Content-Type-Options'] = 'nosniff'
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        response['Permissions-Policy'] = (
            'geolocation=(), camera=(), microphone=()'
        )
        response['Content-Security-Policy'] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval' "
            "https://cdn.jsdelivr.net https://cdnjs.cloudflare.com; "
            "style-src 'self' 'unsafe-inline' "
            "https://fonts.googleapis.com https://cdn.jsdelivr.net "
            "https://cdnjs.cloudflare.com; "
            "font-src 'self' https://fonts.gstatic.com https://cdnjs.cloudflare.com; "
            "img-src 'self' data: blob:; "
            "connect-src 'self' ws: wss: https://cdn.jsdelivr.net "
            "https://cdnjs.cloudflare.com; "
            "worker-src 'self' blob:;"
        )
        return response


# ── 2. Branch Context ─────────────────────────────────────────────────────────

class BranchContextMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.branch = None
        if request.user.is_authenticated:
            branch_id = request.session.get('active_branch_id')
            if branch_id:
                from core.models import Branch
                try:
                    branch = Branch.objects.get(id=branch_id, is_active=True)
                    # Verify user belongs to this branch (super_admin exempt)
                    if (request.user.is_super_admin or
                            request.user.branches.filter(id=branch_id).exists()):
                        request.branch = branch
                    else:
                        request.session.pop('active_branch_id', None)
                except Branch.DoesNotExist:
                    request.session.pop('active_branch_id', None)
        return self.get_response(request)


# ── 3. Audit ──────────────────────────────────────────────────────────────────

class AuditMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        if not request.user.is_authenticated:
            return response

        path = request.path
        if any(path.startswith(p) for p in AUDIT_EXEMPT_PATHS):
            return response

        method = request.method
        is_write = method not in SAFE_METHODS
        is_patient_access = '/patient' in path and method == 'GET'

        if not (is_write or is_patient_access):
            return response

        try:
            payload = {}
            if is_write and request.content_type == 'application/json':
                try:
                    payload = json.loads(request.body or '{}')
                except Exception:
                    pass
            elif is_write:
                payload = dict(request.POST)

            from core.models import AuditLog
            AuditLog.objects.create(
                user=request.user,
                branch_id=getattr(request.branch, 'id', None),
                action=f"{method} {path}",
                ip_address=_get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', '')[:500],
                payload=_sanitize(payload),
            )
        except Exception as e:
            logger.error("AuditMiddleware error: %s", e)

        return response


# ── 4. Idle Timeout ───────────────────────────────────────────────────────────

IDLE_EXEMPT = {'/auth/login/', '/auth/pin/', '/auth/logout/'}


class IdleTimeoutMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if (request.user.is_authenticated and
                request.path not in IDLE_EXEMPT):
            last = request.session.get('last_activity')
            now = int(time.time())
            timeout = getattr(settings, 'SESSION_IDLE_TIMEOUT', 900)

            if last and (now - last) > timeout:
                # Only lock with PIN if user has a PIN set
                has_pin = bool(getattr(request.user, 'pin_hash', None))

                if has_pin:
                    request.session['require_pin'] = True
                    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                        return JsonResponse(
                            {'lock_screen': True,
                             'message': 'Session idle. Enter PIN to continue.'},
                            status=401)
                else:
                    # No PIN set — force full re-login
                    from django.contrib.auth import logout
                    logout(request)
                    from django.shortcuts import redirect
                    return redirect(f"{settings.LOGIN_URL}?next={request.path}&reason=idle")

            request.session['last_activity'] = now

        return self.get_response(request)


# ── 5. Login Attempt Tracking ─────────────────────────────────────────────────

class LoginAttemptMiddleware:
    """
    Tracks failed logins via Redis.
    IP  : 10 failures  → 15 min block
    User: 5  failures  → account flagged
    Applied in the auth view; this middleware exposes helpers via request.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.login_attempt = _LoginAttemptHelper(request)
        return self.get_response(request)


class _LoginAttemptHelper:
    IP_LIMIT = 10
    USER_LIMIT = 5
    BLOCK_TTL = 900

    def __init__(self, request):
        self.request = request
        self.ip = _get_client_ip(request)
        self._redis = None

    def _get_redis(self):
        if self._redis is None:
            from django.conf import settings
            self._redis = _redis_lib.from_url(
                settings.REDIS_URL,
                decode_responses=True,
                socket_connect_timeout=3,
            )
        return self._redis

    def _ip_key(self):
        return f'login_fail_ip:{self.ip}'

    def _user_key(self, email):
        import hashlib
        h = hashlib.md5(email.lower().encode()).hexdigest()
        return f'login_fail_user:{h}'

    def is_ip_blocked(self):
        try:
            r = self._get_redis()
            val = r.get(self._ip_key())
            return val and int(val) >= self.IP_LIMIT
        except Exception:
            return False

    def record_failure(self, email=''):
        try:
            r = self._get_redis()
            ip_key = self._ip_key()
            pipe = r.pipeline()
            pipe.incr(ip_key)
            pipe.expire(ip_key, self.BLOCK_TTL)
            if email:
                uk = self._user_key(email)
                pipe.incr(uk)
                pipe.expire(uk, self.BLOCK_TTL * 4)
            pipe.execute()
        except Exception:
            pass

    def clear(self, email=''):
        try:
            r = self._get_redis()
            keys = [self._ip_key()]
            if email:
                keys.append(self._user_key(email))
            r.delete(*keys)
        except Exception:
            pass
