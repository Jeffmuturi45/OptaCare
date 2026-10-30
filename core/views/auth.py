from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.views.decorators.cache import never_cache
from django.http import JsonResponse
from django.utils import timezone
import json
import logging

from core.models import Branch   # FIX: import at top, no __import__ hack

logger = logging.getLogger(__name__)


@never_cache
@require_http_methods(['GET', 'POST'])
def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    error = None

    if request.method == 'POST':
        email = request.POST.get('email', '').strip().lower()
        password = request.POST.get('password', '')

        logger.debug("Login attempt: %s", email)

        # FIX: don't swallow all exceptions silently — log them
        blocked = False
        if hasattr(request, 'login_attempt'):
            try:
                blocked = request.login_attempt.is_ip_blocked()
            except Exception as exc:
                logger.warning("login_attempt.is_ip_blocked failed: %s", exc)

        if blocked:
            error = 'Too many failed attempts. Try again in 15 minutes.'
            return render(request, 'core/login.html', {'error': error})

        # FIX: authenticate() with email — only works if USERNAME_FIELD=email
        # OR you have a custom backend. Fall back to username=email for default User.
        user = authenticate(request, username=email, password=password)
        logger.warning("Auth result for %s: %r", email, user)  # FIX: WARNING level so it shows

        if user is None:
            if hasattr(request, 'login_attempt'):
                try:
                    request.login_attempt.record_failure(email)
                except Exception as exc:
                    logger.warning("record_failure failed: %s", exc)
            error = 'Invalid email or password.'
            return render(request, 'core/login.html', {'error': error})

        if not user.is_active:
            error = 'Your account is disabled. Contact admin.'
            return render(request, 'core/login.html', {'error': error})

        # Auth OK — log in
        login(request, user)
        request.session.pop('require_pin', None)
        request.session['last_activity'] = int(timezone.now().timestamp())

        if hasattr(request, 'login_attempt'):
            try:
                request.login_attempt.clear(email)
            except Exception as exc:
                logger.warning("login_attempt.clear failed: %s", exc)

        # Branch selection
        # FIX: wrapped in try/except so a broken relation can't 500 *after* login()
        try:
            if user.is_super_admin:
                branches = list(Branch.objects.filter(is_active=True))
            else:
                branches = list(user.branches.filter(is_active=True))
        except Exception as exc:
            logger.exception("Failed to fetch branches for user %s: %s", email, exc)
            branches = []

        if not branches:
            if user.is_super_admin:
                return redirect('superadmin_dashboard')
            logout(request)
            error = 'No branch assigned to your account. Contact admin.'
            return render(request, 'core/login.html', {'error': error})

        if len(branches) == 1:
            request.session['active_branch_id'] = branches[0].id
            return redirect('dashboard')

        return redirect('branch_select')

    return render(request, 'core/login.html', {'error': error})


@never_cache
@login_required
@require_http_methods(['GET', 'POST'])
def branch_select_view(request):
    if request.user.is_super_admin:
        branches = Branch.objects.filter(is_active=True)
    else:
        branches = request.user.branches.filter(is_active=True)

    if request.method == 'POST':
        branch_id = request.POST.get('branch_id', '')
        valid_ids = [str(b.id) for b in branches]
        if branch_id in valid_ids:
            request.session['active_branch_id'] = int(branch_id)
            return redirect('dashboard')

    return render(request, 'core/branch_select.html', {'branches': branches})


# FIX: logout must be POST-only to prevent CSRF logout via <img src="/logout/">
@require_http_methods(['POST'])
def logout_view(request):
    logout(request)
    return redirect('login')


@never_cache
@require_http_methods(['GET', 'POST'])
def pin_view(request):
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'

    if request.method == 'POST':
        if is_ajax:
            try:
                data = json.loads(request.body)
                pin = data.get('pin', '')
            except Exception:
                return JsonResponse({'ok': False}, status=400)
        else:
            pin = request.POST.get('pin', '')

        if len(pin) == 4 and pin.isdigit():
            request.session.pop('require_pin', None)
            request.session['last_activity'] = int(timezone.now().timestamp())
            if is_ajax:
                return JsonResponse({'ok': True})
            return redirect('dashboard')

        if is_ajax:
            return JsonResponse({'ok': False})
        return render(request, 'core/pin.html', {'error': 'Incorrect PIN'})

    return render(request, 'core/pin.html', {})