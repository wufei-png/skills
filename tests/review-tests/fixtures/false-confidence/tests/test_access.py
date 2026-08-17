import unittest
from unittest.mock import patch

import access
from access import Document, User


class DeleteAuthorizationTests(unittest.TestCase):
    @patch("access.can_delete", return_value=True)
    def test_allows_an_admin_to_delete_any_document(self, mocked_can_delete) -> None:
        admin = User(id="admin-1", role="admin")
        document = Document(owner_id="owner-1")

        self.assertTrue(access.can_delete(admin, document))
        mocked_can_delete.assert_called_once_with(admin, document)

    def test_admin_can_delete_someone_elses_document(self) -> None:
        admin = User(id="admin-1", role="admin")
        document = Document(owner_id="owner-1")

        self.assertTrue(access.can_delete(admin, document))

    def test_administrator_can_delete_a_foreign_document(self) -> None:
        admin = User(id="admin-1", role="admin")
        document = Document(owner_id="owner-1")

        self.assertTrue(access.can_delete(admin, document))

    def test_owner_can_delete_their_document(self) -> None:
        owner = User(id="owner-1", role="member")
        document = Document(owner_id="owner-1")

        self.assertTrue(access.can_delete(owner, document))


if __name__ == "__main__":
    unittest.main()
