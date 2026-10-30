from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _
from core.models import (
    CustomUser, UserBranch, Branch, BranchModule,
    Patient, Visit, VisitStatusLog, TriageRecord,
    AuditLog, Notification
)


class UserBranchInline(admin.TabularInline):
    model = UserBranch
    extra = 1
    autocomplete_fields = ['branch']


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = ['email', 'full_name', 'role',
                    'is_active', 'is_super_admin', 'created_at']
    list_filter = ['role', 'is_active', 'is_super_admin']
    search_fields = ['email', 'full_name']
    ordering = ['-created_at']
    inlines = [UserBranchInline]

    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        (_('Personal'), {'fields': ('full_name', 'clock_format')}),
        (_('Role & Access'), {
         'fields': ('role', 'is_super_admin', 'is_active', 'is_staff')}),
        (_('Permissions'), {
         'fields': ('is_superuser', 'groups', 'user_permissions')}),
        (_('Dates'), {'fields': ('last_login',)}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'full_name', 'role', 'password1', 'password2',
                       'is_active', 'is_staff', 'is_super_admin'),
        }),
    )
    readonly_fields = ['last_login']


@admin.register(Branch)
class BranchAdmin(admin.ModelAdmin):
    list_display = ['name', 'branch_type', 'location',
                    'phone', 'is_active', 'created_at']
    list_filter = ['branch_type', 'is_active']
    search_fields = ['name', 'location']


@admin.register(BranchModule)
class BranchModuleAdmin(admin.ModelAdmin):
    list_display = ['branch', 'module_slug', 'enabled', 'enabled_at']
    list_filter = ['enabled', 'module_slug']
    search_fields = ['branch__name', 'module_slug']


@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = ['patient_uid', 'date_of_birth', 'gender',
                    'payment_type', 'registered_at_branch', 'created_at']
    list_filter = ['gender', 'payment_type', 'registered_at_branch']
    search_fields = ['patient_uid', 'phone_hash', 'national_id_hash']
    readonly_fields = ['patient_uid', 'phone_hash',
                       'national_id_hash', 'created_at']


@admin.register(Visit)
class VisitAdmin(admin.ModelAdmin):
    list_display = ['id', 'patient', 'branch', 'visit_type',
                    'visit_status', 'assigned_doctor', 'registered_at']
    list_filter = ['visit_status', 'visit_type', 'branch']
    search_fields = ['patient__patient_uid']
    readonly_fields = ['registered_at', 'triaged_at',
                       'consultation_started_at', 'completed_at']


@admin.register(VisitStatusLog)
class VisitStatusLogAdmin(admin.ModelAdmin):
    list_display = ['visit', 'from_status',
                    'to_status', 'changed_by', 'changed_at']
    readonly_fields = ['changed_at']


@admin.register(TriageRecord)
class TriageRecordAdmin(admin.ModelAdmin):
    list_display = ['visit', 'bp_systolic', 'bp_diastolic',
                    'pulse', 'weight_kg', 'triaged_by', 'triaged_at']
    readonly_fields = ['triaged_at']


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ['user', 'action', 'target_model', 'target_id',
                    'ip_address', 'created_at']
    list_filter = ['action']
    search_fields = ['user__email', 'action', 'target_model']
    readonly_fields = ['user', 'branch_id', 'action', 'target_model',
                       'target_id', 'ip_address', 'user_agent',
                       'payload', 'created_at']

    def has_add_permission(self, request): return False
    def has_change_permission(self, request, obj=None): return False
    def has_delete_permission(self, request, obj=None): return False


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['recipient', 'notif_type',
                    'title', 'is_read', 'created_at']
    list_filter = ['notif_type', 'is_read']
