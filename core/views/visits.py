from django.contrib.auth.decorators import login_required
from django.shortcuts import render


@login_required
def visit_list(request):
    return render(request, 'core/visits/list.html', {})


@login_required
def visit_create(request):
    return render(request, 'core/visits/create.html', {})


@login_required
def visit_transition(request, pk):
    return render(request, 'core/visits/detail.html', {})


@login_required
def triage_submit(request, pk):
    return render(request, 'core/visits/triage.html', {})
