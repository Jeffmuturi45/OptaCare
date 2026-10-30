from django.db import models


class TriageRecord(models.Model):
    visit = models.OneToOneField('core.Visit', on_delete=models.CASCADE,
                                 related_name='triage')
    temperature = models.DecimalField(max_digits=4, decimal_places=1,
                                      null=True, blank=True)
    bp_systolic = models.IntegerField(null=True, blank=True)
    bp_diastolic = models.IntegerField(null=True, blank=True)
    pulse = models.IntegerField(null=True, blank=True)
    spo2 = models.DecimalField(max_digits=4, decimal_places=1,
                               null=True, blank=True)
    weight_kg = models.DecimalField(max_digits=5, decimal_places=1,
                                    null=True, blank=True)
    height_cm = models.DecimalField(max_digits=5, decimal_places=1,
                                    null=True, blank=True)
    va_right = models.CharField(max_length=10, blank=True)  # eye clinic
    va_left = models.CharField(max_length=10, blank=True)
    chief_complaint = models.TextField(blank=True)
    triaged_by = models.ForeignKey('core.CustomUser',
                                   on_delete=models.PROTECT,
                                   null=True, blank=True)
    triaged_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'core_triage_record'

    def __str__(self):
        return f"Triage for Visit {self.visit_id}"
