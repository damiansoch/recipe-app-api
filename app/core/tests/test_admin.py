"""
Test for the Django Admin interface.
"""

from django.test import TestCase
from django.test.client import Client
from django.urls import reverse
from django.contrib.auth import get_user_model


class AdminSiteTests(TestCase):
    """Tests for Django Admin interface."""

    def setUp(self):
        """Create user and test client."""
        self.client = Client()
        self.admin_user = get_user_model().objects.create_superuser(
            email='admin@example.com',
            password='testPass123',
        )
        self.client.force_login(self.admin_user)
        self.user = get_user_model().objects.create_user(
            email='user@example.com',
            password='testPass123',
            name='Test User',
        )

    def test_users_list(self):
        """Test that the users list is working."""
        url = reverse('admin:core_user_changelist')
        response = self.client.get(url)
        self.assertContains(response, self.user.name)
        self.assertContains(response, self.user.email)

    def test_edit_user_page(self):
        """Test edit user page"""
        url = reverse('admin:core_user_change', args=[self.user.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_create_user_page(self):
        """Test create user page"""
        url = reverse('admin:core_user_add')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
