from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db import transaction
from django.utils import timezone
from django.http import JsonResponse

from core.models import Patient, Visit, VisitStatusLog, CustomUser
from core.models.patient import sha256_hash
from core.forms import PatientRegistrationForm
from core.permissions import has_role


REGISTER_ROLES = ('super_admin', 'branch_admin', 'nurse', 'receptionist')


@login_required
def patient_list(request):
    if not has_role(request.user, *REGISTER_ROLES):
        return redirect('dashboard')

    query = request.GET.get('q', '').strip()
    patients = []

    if query:
        h = sha256_hash(query)
        patients = Patient.objects.filter(
            is_active=True
        ).filter(
            phone_hash=h
        ) | Patient.objects.filter(
            is_active=True,
            national_id_hash=h
        ) | Patient.objects.filter(
            is_active=True,
            patient_uid__icontains=query
        )
        patients = patients.distinct().order_by('-created_at')[:50]
    else:
        patients = Patient.objects.filter(
            is_active=True
        ).order_by('-created_at')[:100]

    return render(request, 'core/patients/list.html', {
        'patients': patients,
        'query': query,
    })


@login_required
@require_http_methods(['GET', 'POST'])
def patient_register(request):
    if not has_role(request.user, *REGISTER_ROLES):
        return redirect('dashboard')

    if not request.branch:
        messages.error(
            request, 'No active branch. Please re-login and select a branch.')
        return redirect('dashboard')

    # Doctors available at this branch for assignment
    doctors = CustomUser.objects.filter(
        role='doctor',
        is_active=True,
        branches=request.branch
    )

    form = PatientRegistrationForm()
    generated_uid = Patient.generate_uid()

    if request.method == 'POST':
        form = PatientRegistrationForm(request.POST)
        if form.is_valid():
            d = form.cleaned_data
            try:
                with transaction.atomic():
                    # Check duplicate by phone hash
                    phone_hash = sha256_hash(d['phone'])
                    existing = Patient.objects.filter(
                        phone_hash=phone_hash,
                        is_active=True
                    ).first()

                    if existing and not request.POST.get('confirm_existing'):
                        return render(request, 'core/patients/register.html', {
                            'form':          form,
                            'doctors':       doctors,
                            'generated_uid': generated_uid,
                            'duplicate':     existing,
                        })

                    # Create patient
                    patient = Patient(
                        patient_uid=Patient.generate_uid(),
                        date_of_birth=d['date_of_birth'],
                        gender=d['gender'],
                        email=d.get('email', ''),
                        payment_type=d['payment_type'],
                        insurance_no=d.get('insurance_no', ''),
                        registered_at_branch=request.branch,
                        created_by=request.user,
                    )
                    patient.full_name = d['full_name']
                    patient.phone = d['phone']
                    patient.national_id = d.get('national_id', '')
                    patient.save()

                    # Create visit
                    assigned_doctor = None
                    if d.get('assigned_doctor'):
                        try:
                            assigned_doctor = CustomUser.objects.get(
                                pk=d['assigned_doctor'],
                                role='doctor',
                                is_active=True
                            )
                        except CustomUser.DoesNotExist:
                            pass

                    visit = Visit.objects.create(
                        patient=patient,
                        branch=request.branch,
                        visit_type=d['visit_type'],
                        visit_status='registered',
                        assigned_doctor=assigned_doctor,
                        registered_by=request.user,
                    )
                    VisitStatusLog.objects.create(
                        visit=visit,
                        from_status='',
                        to_status='registered',
                        changed_by=request.user,
                        note=d.get('notes', ''),
                    )

                messages.success(
                    request,
                    f'Patient {patient.patient_uid} registered successfully.'
                )
                return redirect('patient_detail', pk=patient.pk)

            except Exception as e:
                messages.error(request, f'Registration failed: {e}')

    return render(request, 'core/patients/register.html', {
        'form':          form,
        'doctors':       doctors,
        'generated_uid': generated_uid,
    })


@login_required
def patient_detail(request, pk):
    patient = get_object_or_404(Patient, pk=pk, is_active=True)

    # Branch scope — non-super-admins can only view their branch patients
    if not request.user.is_super_admin:
        if not Visit.objects.filter(
            patient=patient,
            branch=request.branch
        ).exists() and patient.registered_at_branch != request.branch:
            return redirect('patient_list')

    visits = Visit.objects.filter(
        patient=patient
    ).select_related(
        'branch', 'assigned_doctor', 'registered_by'
    ).order_by('-registered_at')

    return render(request, 'core/patients/detail.html', {
        'patient': patient,
        'visits':  visits,
    })


@login_required
def patient_search_ajax(request):
    """AJAX quick search for patient lookup during visit creation."""
    q = request.GET.get('q', '').strip()
    if len(q) < 2:
        return JsonResponse({'results': []})

    h = sha256_hash(q)
    patients = Patient.objects.filter(is_active=True).filter(
        phone_hash=h
    ) | Patient.objects.filter(
        is_active=True,
        patient_uid__icontains=q
    )
    patients = patients.distinct()[:10]

    results = []
    for p in patients:
        results.append({
            'id':          p.pk,
            'uid':         p.patient_uid,
            'name':        str(p.full_name),
            'dob':         str(p.date_of_birth),
            'gender':      p.gender,
            'phone':       str(p.phone),
            'payment':     p.payment_type,
        })
    return JsonResponse({'results': results})
