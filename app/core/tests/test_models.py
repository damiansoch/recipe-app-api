"""
Test for models
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from decimal import Decimal

from core import models


def create_user(email='user@example.com', password='<testpass123'):
    """Create and return user"""
    return get_user_model().objects.create_user(email, password)


class TestModels(TestCase):
    """Test models"""

    """Testing user model"""

    def test_create_user_with_email_successful(self):
        """Test creating user with email is successful"""
        email = "test@example.com"
        password = "testpass123"
        user = get_user_model().objects.create_user(
            email=email,
            password=password
        )

        self.assertEqual(user.email, email)
        self.assertTrue(user.check_password(password))

    def test_new_user_email_normalized(self):
        """Test the email for a new user is normalized"""
        sample_emails = [
            ["test1@EXAMPLE.com", "test1@example.com"],
            ["Test2@Example.COM", "Test2@example.com"],
            ["TEST3@EXAMPLE.com", "TEST3@example.com"],
            ["test4@example.COM", "test4@example.com"],
        ]

        for email, expected in sample_emails:
            user = get_user_model().objects.create_user(email, "sample123")
            self.assertEqual(user.email, expected)

    def test_new_user_without_email_raises_error(self):
        """Test creating user with no email is raised error"""
        with self.assertRaises(ValueError):
            get_user_model().objects.create_user("", "sample123")

    def test_create_superuser(self):
        """Test creating a superuser"""
        user = get_user_model().objects.create_superuser(
            "test@example.com", "testpass123"
        )
        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_staff)

    """Testing recipe models"""

    def test_create_recipe(self):
        """Test creating a recipe successful"""
        user = get_user_model().objects.create_user(
            "test@example.com", "testpass123"
        )
        recipe = models.Recipe.objects.create(
            user=user,
            title="Test Recipe",
            time_minutes=5,
            price=Decimal("5.00"),
            description="Test Description",
        )

        self.assertEqual(recipe.user, user)
        self.assertEqual(str(recipe), recipe.title)

    def test_create_tag(self):
        """Test creating a recipe tag successfull"""
        user = create_user()
        tag = models.Tag.objects.create(user=user, name="Vegan")
        self.assertEqual(str(tag), tag.name)
