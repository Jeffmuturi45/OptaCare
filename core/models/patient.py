import hashlib
from django.db import models
from encrypted_model_fields.fields import EncryptedCharField, EncryptedTextField


def sha256_hash(value: str) -> str:
    return hashlib.sha256(value.strip().lower().encode()).hexdigest()


class Patient(models.Model):
    PAYMENT_TYPES = [
        ('cash',      'Cash'),
        ('insurance', 'Insurance'),
        ('deposit',   'Deposit'),
    ]

    patient_uid = models.CharField(max_length=20, unique=True)  # OC-YYYY-NNNNN
    full_name = EncryptedTextField()
    date_of_birth = models.DateField()
    gender = models.CharField(max_length=10, blank=True)
    national_id = EncryptedCharField(max_length=30, blank=True)
    national_id_hash = models.CharField(max_length=64, db_index=True)
    phone = EncryptedCharField(max_length=20)
    phone_hash = models.CharField(max_length=64, db_index=True)
    email = models.EmailField(blank=True)
    payment_type = models.CharField(max_length=30,
                                    choices=PAYMENT_TYPES, default='cash')
    insurance_no = models.CharField(max_length=60, blank=True)
    registered_at_branch = models.ForeignKey('core.Branch',
                                             on_delete=models.PROTECT,
                                             null=True, blank=True)
    created_by = models.ForeignKey('core.CustomUser',
                                   on_delete=models.PROTECT,
                                   null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'core_patient'

    def __str__(self):
        return f"{self.patient_uid}"

    def save(self, *args, **kwargs):
        if self.phone:
            self.phone_hash = sha256_hash(str(self.phone))
        if self.national_id:
            self.national_id_hash = sha256_hash(str(self.national_id))
        super().save(*args, **kwargs)

    @classmethod
    def generate_uid(cls):
        from django.utils import timezone
        year = timezone.now().year
        last = (cls.objects
                .filter(patient_uid__startswith=f'OC-{year}-')
                .order_by('-patient_uid')
                .first())
        if last:
            seq = int(last.patient_uid.split('-')[-1]) + 1
        else:
            seq = 1
        return f'OC-{year}-{seq:05d}'
