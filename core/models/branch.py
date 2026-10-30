from django.db import models


class Branch(models.Model):
    BRANCH_TYPES = [
        ('eye_clinic', 'Eye Clinic'),
        ('hospital',   'Hospital'),
    ]
    name = models.CharField(max_length=120)
    branch_type = models.CharField(max_length=20, choices=BRANCH_TYPES)
    location = models.CharField(max_length=200, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'core_branch'
        verbose_name_plural = 'Branches'

    def __str__(self):
        return self.name


class BranchModule(models.Model):
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE,
                               related_name='modules')
    module_slug = models.CharField(max_length=60)
    enabled = models.BooleanField(default=False)
    config = models.JSONField(default=dict)
    enabled_at = models.DateTimeField(null=True, blank=True)
    enabled_by = models.IntegerField(null=True, blank=True)

    class Meta:
        db_table = 'core_branch_module'
        unique_together = [('branch', 'module_slug')]

    def __str__(self):
        return f"{self.branch.name} — {self.module_slug}"
