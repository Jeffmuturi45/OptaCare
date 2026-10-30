from django.db import models


class Notification(models.Model):
    TYPES = [
        ('queue',        'Queue Update'),
        ('lab',          'Lab Result'),
        ('glasses_ready', 'Glasses Ready'),
        ('announcement', 'Announcement'),
        ('system',       'System'),
    ]
    recipient = models.ForeignKey('core.CustomUser',
                                  on_delete=models.CASCADE,
                                  related_name='notifications')
    branch = models.ForeignKey('core.Branch',
                               on_delete=models.CASCADE,
                               null=True, blank=True)
    notif_type = models.CharField(max_length=30, choices=TYPES)
    title = models.CharField(max_length=200)
    message = models.TextField(blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'core_notification'
        ordering = ['-created_at']
