"""
Tests for Ingredient API
"""
from decimal import Decimal

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse

from rest_framework.test import APIClient
from rest_framework import status

from core.models import (Ingredient, Recipe)
from recipe.serializers import IngredientSerializer

INGREDIENT_URL = reverse('recipe:ingredient-list')


def detail_url(ingredient_id):
    """Return recipe detail URL."""
    return reverse('recipe:ingredient-detail', args=[ingredient_id])


def create_user(email="example@user.com", password="testpass123"):
    """Create a new user."""
    return get_user_model().objects.create_user(email, password)


class PublicIngredientApiTests(TestCase):
    """Test unauthenticated API access."""

    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        """Test that authentication is required for retrieving ingredients."""
        res = self.client.get(INGREDIENT_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateIngredientApiTests(TestCase):
    """Test authenticated API access."""

    def setUp(self):
        self.client = APIClient()
        self.user = create_user()
        self.client.force_authenticate(self.user)

    def test_retrieve_ingredient_list(self):
        """Test retrieving a list of ingredients."""

        Ingredient.objects.create(user=self.user, name='Kale')
        Ingredient.objects.create(user=self.user, name='Salt')
        res = self.client.get(INGREDIENT_URL)

        ingredients = Ingredient.objects.all().order_by('-name')
        serializer = IngredientSerializer(ingredients, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_ingredient_limited_to_user(self):
        """Test retrieving ingredients for authenticated user."""
        user2 = create_user(email="other@user.com", password="otheruser123")
        Ingredient.objects.create(user=user2, name='Kale')
        ingredient = Ingredient.objects.create(user=self.user, name='Salt')
        res = self.client.get(INGREDIENT_URL)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]['name'], ingredient.name)
        self.assertEqual(res.data[0]['id'], ingredient.id)

    def test_update_ingredient_successful(self):
        """Test updating an ingredient is successful."""
        ingredient = Ingredient.objects.create(user=self.user, name='Kale')
        payload = {'name': 'Salt'}
        url = detail_url(ingredient.id)
        res = self.client.patch(url, payload)
        ingredient.refresh_from_db()

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(ingredient.name, payload["name"])
        self.assertEqual(ingredient.user, self.user)

    def test_delete_ingredient_successful(self):
        """Test deleting an ingredient is successful."""
        ingredient = Ingredient.objects.create(user=self.user, name='Kale')

        url = detail_url(ingredient.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        ingredients = Ingredient.objects.filter(user=self.user)
        self.assertFalse(ingredients.exists())

    def test_filter_ingredients_assigned_to_recipes(self):
        """Test filtering ingredients assigned to recipes."""
        ingredient1 = Ingredient.objects.create(user=self.user, name='Kale')
        ingredient2 = Ingredient.objects.create(user=self.user, name='Salt')
        ingredient3 = Ingredient.objects.create(user=self.user, name='Pepper')
        recipe = Recipe.objects.create(title="Some recipe", time_minutes=50, price="5.50", user=self.user)
        recipe.ingredients.add(ingredient1)
        recipe.ingredients.add(ingredient2)

        res = self.client.get(INGREDIENT_URL, {'assigned_only': 1})

        s1 = IngredientSerializer(ingredient1)
        s2 = IngredientSerializer(ingredient2)
        s3 = IngredientSerializer(ingredient3)

        self.assertIn(s1.data, res.data)
        self.assertIn(s2.data, res.data)
        self.assertNotIn(s3.data, res.data)

    def test_filtered_ingredients_unique(self):
        """Test filtering ingredients assigned to recipes list is unique."""
        ingredient1 = Ingredient.objects.create(user=self.user, name='Kale')
        Ingredient.objects.create(user=self.user, name='Salt')

        recipe1 = Recipe.objects.create(title="Some recipe", time_minutes=50, price="5.50", user=self.user)
        recipe2 = Recipe.objects.create(title="Some other recipe", time_minutes=50, price="5.50", user=self.user)

        recipe1.ingredients.add(ingredient1)
        recipe2.ingredients.add(ingredient1)

        res = self.client.get(INGREDIENT_URL, {'assigned_only': 1})

        self.assertEqual(len(res.data), 1)
