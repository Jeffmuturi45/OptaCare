from django.db import models


class AuditLog(models.Model):
    user = models.ForeignKey('core.CustomUser',
                             on_delete=models.SET_NULL,
                             null=True, blank=True)
    branch_id = models.IntegerField(null=True, blank=True)
    action = models.CharField(max_length=80)
    target_model = models.CharField(max_length=60, blank=True)
    target_id = models.IntegerField(null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    payload = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'core_audit_log'
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['target_model', 'target_id']),
        ]

    def __str__(self):
        return f"{self.action} by user {self.user_id} @ {self.created_at}"
