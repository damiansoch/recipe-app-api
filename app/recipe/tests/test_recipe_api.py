"""Test for recipe API."""
from decimal import Decimal

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse

from rest_framework.test import APIClient
from rest_framework import status

from core.models import (Recipe, Tag, Ingredient)
from recipe.serializers import (RecipeSerializer, RecipeDetailSerializer, )

RECIPES_URL = reverse('recipe:recipe-list')


def detail_url(recipe_id):
    """Return recipe detail URL."""
    return reverse('recipe:recipe-detail', args=[recipe_id])


def create_recipe(user, **params):
    """Create and return a sample recipe"""
    defaults = {
        "title": "Test Recipe",
        "time_minutes": 10,
        "price": Decimal(10.20),
        "description": "Test Recipe",
        "link": "http://example.com/recipe.pdf",

    }
    defaults.update(params)
    return Recipe.objects.create(user=user, **defaults)


def create_user(**params):
    """Create and return a sample user"""
    return get_user_model().objects.create_user(**params)


class PublicRecipeApiTests(TestCase):
    """Test unauthenticated recipe API access."""

    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        """Test that authentication is required."""
        res = self.client.get(RECIPES_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateRecipeApiTests(TestCase):
    """Test authenticated recipe API access."""

    def setUp(self):
        self.user = create_user(email="user@example.com", password="testpass123")
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def test_retrieve_recipes(self):
        """Test retrieving a list of recipes."""
        create_recipe(user=self.user)
        create_recipe(user=self.user)
        res = self.client.get(RECIPES_URL)
        recipes = Recipe.objects.all().order_by('-id')
        serializer = RecipeSerializer(recipes, many=True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_recipes_limited_to_user(self):
        """Test retrieving recipes for user."""
        user2 = create_user(email="user2@example.com", password="othertestpass123")
        create_recipe(user=user2)
        create_recipe(user=self.user)

        res = self.client.get(RECIPES_URL)
        recipes = Recipe.objects.filter(user=self.user)
        serializer = RecipeSerializer(recipes, many=True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_get_recipe_detail(self):
        """Test retrieving recipe detail."""
        recipe = create_recipe(user=self.user)

        url = detail_url(recipe.id)
        res = self.client.get(url)

        serializer = RecipeDetailSerializer(recipe)
        self.assertEqual(res.data, serializer.data)

    def test_create_basic_recipe(self):
        """Test creating recipe."""

        payload = {
            "title": "Test Title",
            "time_minutes": 10,
            "price": Decimal("10.20"),
        }
        res = self.client.post(RECIPES_URL, payload)
        if res.status_code != status.HTTP_201_CREATED:
            print("Response content:", res.content)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipe = Recipe.objects.get(id=res.data['id'])
        for k, v in payload.items():
            self.assertEqual(getattr(recipe, k), v)
        self.assertEqual(recipe.user, self.user)

    def test_partial_update_of_recipy(self):
        """Test updating recipe."""
        original_link = "http://example.com/recipe.pdf"
        recipe = create_recipe(
            user=self.user,
            title="Test Recipe",
            time_minutes=10,
            price=Decimal(10.20),
            description="Test Recipe",
            link=original_link,
        )
        payload = {"title": "New recipe title"}
        url = detail_url(recipe.id)
        res = self.client.patch(url, payload)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        recipe.refresh_from_db()
        self.assertEqual(recipe.title, payload['title'])
        self.assertEqual(recipe.link, original_link)
        self.assertEqual(recipe.user, self.user)

    def test_full_update_of_recipe(self):
        """Test fully updating recipe."""
        original_link = "http://example.com/recipe.pdf"
        original_title = "Test Recipe"
        original_time_minutes = 10
        original_price = Decimal("10.20")
        original_description = "Test Recipe"

        recipe = create_recipe(
            user=self.user,
            title=original_title,
            time_minutes=original_time_minutes,
            price=original_price,
            description=original_description,
            link=original_link,
        )
        payload = {
            "title": "Test Recipe updated",
            "time_minutes": 11,
            "price": Decimal("10.10"),
            "description": "Test Recipe desc updated",
            "link": "http://example.com/recipe_updated.pdf",
        }
        url = detail_url(recipe.id)
        res = self.client.put(url, payload)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        recipe.refresh_from_db()
        for key, value in payload.items():
            self.assertEqual(getattr(recipe, key), value)
        self.assertEqual(recipe.user, self.user)

    def test_update_user_returns_error(self):
        recipe = create_recipe(user=self.user)
        url = detail_url(recipe.id)
        other_user = create_user(email="user3@example.com", password="passexample123")
        self.client.patch(url, payload={"user": other_user.id})
        recipe.refresh_from_db()
        self.assertEqual(recipe.user, self.user)

    def test_delete_recipe(self):
        """Test deleting recipe."""
        original_recipes_count = Recipe.objects.count()
        recipe = create_recipe(user=self.user)
        recipes_after_adding_count = Recipe.objects.count()
        self.assertEqual(recipes_after_adding_count, original_recipes_count + 1)

        url = detail_url(recipe.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        recipes_after_deleting_count = Recipe.objects.count()
        self.assertEqual(recipes_after_deleting_count, original_recipes_count)
        self.assertFalse(Recipe.objects.filter(id=recipe.id).exists())

    def test_delete_other_users_recipe_error(self):
        """Test that other users delete recipes gives error ."""

        other_user = create_user(email="user3@example.com", password="testpass123")

        recipe = create_recipe(user=other_user)
        url = detail_url(recipe.id)
        res = self.client.delete(url)
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(Recipe.objects.filter(id=recipe.id).exists())

    # TESTS FOR TAGS
    def test_create_recipy_with_new_tag(self):
        """Test creating recipy with new tag"""
        payload = {
            "title": "New title",
            "time_minutes": 10,
            "price": Decimal("10.20"),
            "description": "Test Recipe",
            "link": "http://example.com/recipe.pdf",
            "tags": [
                {"name": "tag1", }, {"name": "tag2"}, ]
        }
        res = self.client.post(RECIPES_URL, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipes = Recipe.objects.filter(user=self.user)
        self.assertEqual(recipes.count(), 1)
        recipe = recipes[0]
        self.assertEqual(recipe.tags.count(), 2)
        for tag in payload['tags']:
            exists = Tag.objects.filter(name=tag['name'], user=self.user, ).exists()
            self.assertTrue(exists)

    def test_create_recipe_with_existing_tag(self):
        """Test creating recipe with existing tag"""
        tag_indian = Tag.objects.create(user=self.user, name="Indian")

        payload = {
            "title": "New title",
            "time_minutes": 10,
            "price": Decimal("10.20"),
            "description": "Test Recipe",
            "link": "http://example.com/recipe.pdf",
            "tags": [
                {"name": "Indian"}, {"name": "Breakfast"}, ]
        }
        res = self.client.post(RECIPES_URL, payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipes = Recipe.objects.filter(user=self.user)
        self.assertEqual(recipes.count(), 1)
        recipe = recipes[0]
        self.assertEqual(recipe.tags.count(), 2)
        self.assertIn(tag_indian, recipe.tags.all())
        for tag in payload['tags']:
            exists = Tag.objects.filter(name=tag['name'], user=self.user, ).exists()
            self.assertTrue(exists)

    def test_create_tag_on_update_recipe(self):
        """Test creating tag on update recipe."""
        recipe = create_recipe(user=self.user)
        payload = {
            "tags": [
                {"name": "Breakfast"},
            ]
        }
        url = detail_url(recipe.id)
        res = self.client.patch(url, payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        new_tag = Tag.objects.get(user=self.user, name="Breakfast")
        self.assertIn(new_tag, recipe.tags.all())

    def test_update_recipe_assign_tag(self):
        """Test assigning an existing tag when updating a recipe"""
        tag_breakfast = Tag.objects.create(user=self.user, name="Breakfast")
        recipe = create_recipe(user=self.user)
        recipe.tags.add(tag_breakfast)

        tag_lunch = Tag.objects.create(user=self.user, name="Lunch")
        payload = {
            "tags": [{"name": "Lunch"}, ]
        }
        url = detail_url(recipe.id)
        res = self.client.patch(url, payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn(tag_lunch, recipe.tags.all())
        self.assertNotIn(tag_breakfast, recipe.tags.all())

    def test_update_clear_recipe_tags(self):
        """Test clearing tags on update recipe."""
        recipe = create_recipe(user=self.user)
        recipe.tags.add(Tag.objects.create(user=self.user, name="Breakfast"))
        recipe.tags.add(Tag.objects.create(user=self.user, name="Fat Breakfast"))

        payload = {"tags": []}

        url = detail_url(recipe.id)
        res = self.client.patch(url, payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        recipe.refresh_from_db()
        self.assertEqual(recipe.tags.count(), 0)

    # TEST FOR INGREDIENTS
    def test_create_recipy_with_new_ingredients(self):
        """Test creating recipy with new ingredient"""
        payload = {
            "title": "New title",
            "time_minutes": 10,
            "price": Decimal("10.20"),
            "description": "Test Recipe",
            "link": "http://example.com/recipe.pdf",
            "ingredients": [
                {"name": "ingredient1", }, {"name": "ingredient2"}, ]
        }
        res = self.client.post(RECIPES_URL, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipes = Recipe.objects.filter(user=self.user)
        self.assertEqual(recipes.count(), 1)
        recipe = recipes[0]
        self.assertEqual(recipe.ingredients.count(), 2)
        for ingredient in payload['ingredients']:
            exists = Ingredient.objects.filter(name=ingredient['name'], user=self.user, ).exists()
            self.assertTrue(exists)

    def test_create_recipe_with_existing_ingredient(self):
        """Test creating recipe with existing ingredient"""
        salad_ingredient = Ingredient.objects.create(user=self.user, name="Salad")

        payload = {
            "title": "New title",
            "time_minutes": 10,
            "price": "10.20",
            "description": "Test Recipe",
            "link": "http://example.com/recipe.pdf",
            "ingredients": [
                {"name": "Salad"}, {"name": "Brocolli"}, ]
        }
        res = self.client.post(RECIPES_URL, payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipes = Recipe.objects.filter(user=self.user)
        self.assertEqual(recipes.count(), 1)
        recipe = recipes[0]
        self.assertEqual(recipe.ingredients.count(), 2)
        self.assertIn(salad_ingredient, recipe.ingredients.all())
        for ingredient in payload['ingredients']:
            exists = recipe.ingredients.filter(name=ingredient['name'], user=self.user, ).exists()
            self.assertTrue(exists)

    def test_create_ingredient_on_update_recipe(self):
        """Test creating ingredient on update recipe."""
        recipe = create_recipe(user=self.user)
        payload = {
            "ingredients": [
                {"name": "Pepper"},
            ]
        }
        url = detail_url(recipe.id)
        res = self.client.patch(url, payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        new_ingredient = Ingredient.objects.get(user=self.user, name="Pepper")
        self.assertIn(new_ingredient, recipe.ingredients.all())

    def test_update_recipe_assign_ingredient(self):
        """Test assigning an existing ingredient when updating a recipe"""
        ingredient1 = Ingredient.objects.create(user=self.user, name="Salt")
        recipe = create_recipe(user=self.user)
        recipe.ingredients.add(ingredient1)

        ingredient2 = Ingredient.objects.create(user=self.user, name="Pepper")
        payload = {
            "ingredients": [{"name": "Pepper"}, ]
        }
        url = detail_url(recipe.id)
        res = self.client.patch(url, payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn(ingredient2, recipe.ingredients.all())
        self.assertNotIn(ingredient1, recipe.ingredients.all())

    def test_update_clear_recipe_ingredients(self):
        """Test clearing ingredients on update recipe."""
        recipe = create_recipe(user=self.user)
        recipe.ingredients.add(Ingredient.objects.create(user=self.user, name="Salt"))
        recipe.ingredients.add(Ingredient.objects.create(user=self.user, name="Fat Breakfast"))

        payload = {"ingredients": []}

        url = detail_url(recipe.id)
        res = self.client.patch(url, payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        recipe.refresh_from_db()
        self.assertEqual(recipe.ingredients.count(), 0)
