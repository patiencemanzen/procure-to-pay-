from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """Custom user model with additional fields for role-based access."""
    
    class Role(models.TextChoices):
        STAFF = 'staff', 'Staff'
        APPROVER_LVL1 = 'approver_lvl1', 'Approver Level 1'
        APPROVER_LVL2 = 'approver_lvl2', 'Approver Level 2'
        FINANCE = 'finance', 'Finance'
    
    full_name = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.STAFF)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'full_name']
    
    def __str__(self):
        return f"{self.full_name} ({self.email})"
    
    @property
    def is_staff_member(self):
        return self.role == self.Role.STAFF
    
    @property
    def is_approver_level_1(self):
        return self.role == self.Role.APPROVER_LVL1
    
    @property
    def is_approver_level_2(self):
        return self.role == self.Role.APPROVER_LVL2
    
    @property
    def is_finance_user(self):
        return self.role == self.Role.FINANCE
    
    @property
    def can_approve(self):
        return self.role in [self.Role.APPROVER_LVL1, self.Role.APPROVER_LVL2]