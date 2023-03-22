"""
Test for the ingredients API
"""
from decimal import Decimal
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Ingredient, Dataset

from dataset.serializers import IngredientSerializer


INGREDIENT_URL = reverse('dataset:ingredient-list')

def detail_url(ingredient_id):
    """ Create and Return an ingredient detail URL """
    return reverse('dataset:ingredient-detail', args=[ingredient_id])

def create_user(email='user@example.com', password='testpass123'):
    """ Create and return a new user """
    return get_user_model().objects.create_user(email, password)

class PublicIngredientsApiTest(TestCase):
    """ Test unauthenticated api requests """

    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        """ Test auth is required for retrieving ingredients """
        res = self.client.get(INGREDIENT_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

class PrivateIngredientsApiTests(TestCase):
    """ Test authenticated API requests """
    """ Test authenticated API requests """
    def setUp(self):
        self.client = APIClient()
        self.user = create_user()
        self.client.force_authenticate(self.user)

    def test_retrieve_ingredients(self):
        """ Test retrieve a list of ingredients """
        Ingredient.objects.create(user = self.user, name ='Kale')
        Ingredient.objects.create(user = self.user, name ='Vanilla')

        res = self.client.get(INGREDIENT_URL)

        ingredients = Ingredient.objects.all().order_by('-name')
        serializer = IngredientSerializer(ingredients, many = True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_ingredient_limited_to_user(self):
        """ Test list of ingredients is limited to authenticated user """
        user2 = create_user(email = 'user2@example.com')
        Ingredient.objects.create(user = user2, name ='Salt')
        ingredient = Ingredient.objects.create(user = self.user, name ='Pepper')
        
        res = self.client.get(INGREDIENT_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]['name'], ingredient.name)
        self.assertEqual(res.data[0]['id'], ingredient.id)

    def test_update_ingredient(self):
        """ Test updating an ingredient """
        ingredient = Ingredient.objects.create(user = self.user, name = 'Cilantro')
        payload = {'name':'Coriander'}
        url = detail_url(ingredient.id)
        res = self.client.patch(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        ingredient.refresh_from_db()
        self.assertEqual(ingredient.name, payload['name'])

    def test_delete_ingredient(self):
        """ test deleting a ingredeint successful """
        ingredient = Ingredient.objects.create(user = self.user, name = 'Lettuce')

        url = detail_url(ingredient.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Ingredient.objects.filter(id=ingredient.id).exists())

    def filter_ingredient_assigned_to_dataset(self):
        """ Test liting ingredients by those assigned to dataset """
        in1 = Ingredient.objects.create(user = self.user, name='Apples')
        in2 = Ingredient.objects.create(user = self.user, name='Turkey')

        dataset = Dataset.objects.create(
            title='Apple Crumble',
            time_minutes=5,
            price=Decimal('4.50'),
            user=self.user
        )

        dataset.ingredients.add(in1)

        res = self.client.get(INGREDIENT_URL, {'assigned_only':1})

        s1 = IngredientSerializer(in1)
        s2 = IngredientSerializer(in2)

        self.assertIn(s1.data, res.data)
        self.assertNotIn(s2.data, res.data)

    def test_filtered_ingredient_unique(self):
        """ Test filtered ingredients returns a unique list """
        ing = Ingredient.objects.create(user = self.user, name = 'Eggs')
        Ingredient.objects.create(user = self.user, name = 'Lentils')
        dataset1 = Dataset.objects.create(
            title = 'Herb Eggs',
            time_minutes = 60,
            price = Decimal('7.00'),
            user = self.user,
        )

        dataset2 = Dataset.objects.create(
            title = 'Eggs Benedict',
            time_minutes = 20,
            price = Decimal('5.00'),
            user = self.user,
        )

        dataset1.ingredients.add(ing)
        dataset2.ingredients.add(ing)

        res = self.client.get(INGREDIENT_URL, {'assigned_only':1})
        self.assertEqual(len(res.data), 1)

        