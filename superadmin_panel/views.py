from django.contrib.auth.decorators import login_required
from django.shortcuts import render


@login_required
def dashboard(request): return render(request, 'superadmin/dashboard.html', {})


@login_required
def users(request): return render(request, 'superadmin/users.html', {})


@login_required
def branches(request): return render(request, 'superadmin/branches.html', {})
