from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models


class CustomUserManager(BaseUserManager):
    def create_user(self, email, full_name, role, password=None, **extra):
        if not email:
            raise ValueError('Email required')
        email = self.normalize_email(email)
        user = self.model(email=email, full_name=full_name, role=role, **extra)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, full_name, password=None, **extra):
        extra.setdefault('role', 'super_admin')
        extra.setdefault('is_super_admin', True)
        extra.setdefault('is_staff', True)
        extra.setdefault('is_superuser', True)
        return self.create_user(email, full_name, extra.pop('role'),
                                password, **extra)


class CustomUser(AbstractBaseUser, PermissionsMixin):
    ROLES = [
        ('super_admin',   'Super Admin'),
        ('branch_admin',  'Branch Admin'),
        ('doctor',        'Doctor'),
        ('nurse',         'Nurse'),
        ('receptionist',  'Receptionist'),
        ('lab_tech',      'Lab Technician'),
        ('pharmacist',    'Pharmacist'),
    ]
    CLOCK_FORMATS = [('12h', '12-hour'), ('24h', '24-hour')]

    email = models.EmailField(unique=True)
    full_name = models.CharField(max_length=200)
    role = models.CharField(max_length=30, choices=ROLES)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_super_admin = models.BooleanField(default=False)
    pin_hash = models.CharField(max_length=128, blank=True, default='')
    clock_format = models.CharField(max_length=3, choices=CLOCK_FORMATS,
                                    default='12h')
    created_at = models.DateTimeField(auto_now_add=True)

    branches = models.ManyToManyField(
        'core.Branch',
        through='core.UserBranch',
        related_name='users',
    )

    objects = CustomUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['full_name']

    class Meta:
        db_table = 'core_user'

    def __str__(self):
        return f"{self.full_name} ({self.role})"

    @property
    def primary_branch(self):
        ub = self.userbranch_set.filter(is_primary=True).first()
        return ub.branch if ub else None


class UserBranch(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    branch = models.ForeignKey('core.Branch', on_delete=models.CASCADE)
    is_primary = models.BooleanField(default=True)

    class Meta:
        db_table = 'core_user_branch'
        unique_together = [('user', 'branch')]
