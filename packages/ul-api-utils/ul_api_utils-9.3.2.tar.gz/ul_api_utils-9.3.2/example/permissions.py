from ul_api_utils.access import PermissionRegistry

permissions = PermissionRegistry('example-debug-log', 111, 222)

SOME_PERMISSION = permissions.add('SOME', 1, 'Param pam Pam', 'test')
SOME_PERMISSION2 = permissions.add('SOME2', 2, 'Param pam Pam2', 'test', flags='123,234')
