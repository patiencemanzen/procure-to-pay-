"""
User utility functions for role-based access control.
"""


def get_user_role(user):
    """Determine user role based on username/email patterns."""
    if user.is_superuser:
        return 'admin'
    
    username_lower = user.username.lower()
    email_lower = user.email.lower()
    
    if 'staff' in username_lower or 'staff' in email_lower:
        return 'staff'
    elif 'approver1' in username_lower or 'approver1' in email_lower:
        return 'approver_lvl1'
    elif 'approver2' in username_lower or 'approver2' in email_lower:
        return 'approver_lvl2'
    elif 'finance' in username_lower or 'finance' in email_lower:
        return 'finance'
    else:
        return 'staff'  # Default role


def is_staff_member(user):
    """Check if user is a staff member."""
    return get_user_role(user) == 'staff'


def can_approve(user):
    """Check if user can approve requests."""
    role = get_user_role(user)
    return role in ['approver_lvl1', 'approver_lvl2']


def is_finance_user(user):
    """Check if user is a finance user."""
    return get_user_role(user) == 'finance'


def is_approver_level_1(user):
    """Check if user is level 1 approver."""
    return get_user_role(user) == 'approver_lvl1'


def is_approver_level_2(user):
    """Check if user is level 2 approver."""
    return get_user_role(user) == 'approver_lvl2'