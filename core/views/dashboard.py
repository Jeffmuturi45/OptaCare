from django.contrib.auth.decorators import login_required
from django.shortcuts import render


@login_required
def dashboard_view(request):
    from core.models import Branch, CustomUser
    from django.contrib.sessions.models import Session

    ctx = {}
    if request.user.role == 'super_admin':
        ctx['branches'] = Branch.objects.filter(is_active=True)
        ctx['branch_count'] = Branch.objects.filter(is_active=True).count()
        ctx['user_count'] = CustomUser.objects.filter(is_active=True).count()
        ctx['active_sessions'] = Session.objects.count()
        ctx['visits_today'] = 0  # wired when visit views are built

    return render(request, 'core/dashboard.html', ctx)
