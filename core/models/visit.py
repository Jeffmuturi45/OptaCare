from django.db import models


class Visit(models.Model):
    VISIT_TYPES = [
        ('walk_in',           'Walk-in'),
        ('appointment',       'Appointment'),
        ('dispensing_only',   'Dispensing Only'),
    ]
    STATUSES = [
        ('registered',       'Registered'),
        ('arrived',          'Arrived'),
        ('in_triage',        'In Triage'),
        ('triaged',          'Triaged'),
        ('in_consultation',  'In Consultation'),
        ('completed',        'Completed'),
        ('cancelled',        'Cancelled'),
    ]
    # Forward-only transitions
    TRANSITIONS = {
        'registered':      ['arrived', 'cancelled'],
        'arrived':         ['in_triage', 'cancelled'],
        'in_triage':       ['triaged', 'cancelled'],
        'triaged':         ['in_consultation', 'cancelled'],
        'in_consultation': ['completed', 'cancelled'],
        'completed':       [],
        'cancelled':       [],
    }

    patient = models.ForeignKey('core.Patient', on_delete=models.PROTECT)
    branch = models.ForeignKey('core.Branch',  on_delete=models.PROTECT)
    visit_type = models.CharField(max_length=20, choices=VISIT_TYPES)
    visit_status = models.CharField(max_length=30, choices=STATUSES,
                                    default='registered')
    assigned_doctor = models.ForeignKey(
        'core.CustomUser', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='assigned_visits')
    appointment_id = models.IntegerField(null=True, blank=True)
    registered_by = models.ForeignKey(
        'core.CustomUser', on_delete=models.PROTECT,
        null=True, related_name='registered_visits')
    registered_at = models.DateTimeField(auto_now_add=True)
    triaged_at = models.DateTimeField(null=True, blank=True)
    consultation_started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    is_locked = models.BooleanField(default=False)

    class Meta:
        db_table = 'core_visit'

    def __str__(self):
        return f"Visit {self.id} — {self.patient} [{self.visit_status}]"

    def can_transition_to(self, new_status):
        return new_status in self.TRANSITIONS.get(self.visit_status, [])

    def transition(self, new_status, changed_by, note=''):
        if not self.can_transition_to(new_status):
            raise ValueError(
                f"Cannot move from '{self.visit_status}' to '{new_status}'")
        old = self.visit_status
        self.visit_status = new_status
        from django.utils import timezone
        if new_status == 'triaged':
            self.triaged_at = timezone.now()
        elif new_status == 'in_consultation':
            self.consultation_started_at = timezone.now()
        elif new_status == 'completed':
            self.completed_at = timezone.now()
            self.is_locked = True
        self.save(update_fields=['visit_status', 'triaged_at',
                                 'consultation_started_at',
                                 'completed_at', 'is_locked'])
        VisitStatusLog.objects.create(
            visit=self, from_status=old, to_status=new_status,
            changed_by=changed_by, note=note)


class VisitStatusLog(models.Model):
    visit = models.ForeignKey(Visit, on_delete=models.CASCADE,
                              related_name='status_logs')
    from_status = models.CharField(max_length=30, blank=True)
    to_status = models.CharField(max_length=30)
    changed_by = models.ForeignKey('core.CustomUser',
                                   on_delete=models.PROTECT,
                                   null=True, blank=True)
    changed_at = models.DateTimeField(auto_now_add=True)
    note = models.TextField(blank=True)

    class Meta:
        db_table = 'core_visit_status_log'
