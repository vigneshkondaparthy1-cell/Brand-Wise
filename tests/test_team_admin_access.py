import unittest
from unittest.mock import patch

import accounts


class TeamAdminAccessTests(unittest.TestCase):
    def test_account_admin_can_view_team_without_active_company(self):
        people = [{'username': 'editor', 'role': 'Creator'}]
        with patch.object(accounts, 'current_user', return_value={'username': 'admin', 'role': 'Admin', 'activeCompanyId': None}), \
             patch.object(accounts, 'list_users', return_value=people) as list_users:
            self.assertEqual(accounts.list_workspace_users({}), people)
            list_users.assert_called_once_with()

    def test_non_admin_without_company_admin_membership_is_denied(self):
        with patch.object(accounts, 'current_user', return_value={'username': 'editor', 'role': 'Creator'}), \
             patch.object(accounts, 'active_membership', return_value=None), \
             patch.object(accounts, 'list_users') as list_users:
            with self.assertRaises(PermissionError):
                accounts.list_workspace_users({})
            list_users.assert_not_called()


if __name__ == '__main__':
    unittest.main()
