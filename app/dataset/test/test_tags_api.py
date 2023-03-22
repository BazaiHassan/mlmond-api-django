"""
Tests for the tags api
"""
from decimal import Decimal
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Tag, Dataset

from dataset.serializers import TagSerializer

TAGS_URL = reverse('dataset:tag-list')

def detail_url(tag_id):
    """ Create and return a tag detail url """
    return reverse('dataset:tag-detail', args=[tag_id])

def create_user(email='user@example.com', password='testpass123'):
    """ Create and return a new user """
    return get_user_model().objects.create_user(email=email, password=password)

class PublicTagsApiTests(TestCase):
    """ Test unauthenticated API requests """
    def setUp(self):
        self.client = APIClient()
    
    def test_auth_required(self):
        """ Test auth is required to call API """
        res = self.client.get(TAGS_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateTagsApiTests(TestCase):
    """ Test authenticated API requests """
    def setUp(self):
        self.client = APIClient()
        self.user = create_user()
        self.client.force_authenticate(self.user)

    def test_retrieve_tags(self):
        """ Test retrieving a list of tags """
        Tag.objects.create(user = self.user, name = 'Vegan')
        Tag.objects.create(user = self.user, name = 'Dessert')

        res = self.client.get(TAGS_URL)

        tags = Tag.objects.all().order_by('-name')
        serializer = TagSerializer(tags, many = True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_tags_limited_to_user(self):
        """ Test list of tags is limited to authenticated user. """
        user2 = create_user(email = 'user2@example.com')
        tag = Tag.objects.create(user = self.user, name = 'Comfort food')

        res = self.client.get(TAGS_URL)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data),1)
        self.assertEqual(res.data[0]['name'], tag.name)
        self.assertEqual(res.data[0]['id'], tag.id)

    def test_update_tag(self):
        """ Test updating a tag """
        tag = Tag.objects.create(user= self.user, name = 'after dinner')
        payload = {'name':'Dessert'}
        url = detail_url(tag.id)
        res = self.client.patch(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        tag.refresh_from_db()
        self.assertEqual(tag.name, payload['name'])

    def test_delete_tag(self):
        """ Test deleting a tag """
        tag = Tag.objects.create(user= self.user, name = 'breakfast')
        url = detail_url(tag.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        tags = Tag.objects.filter(user = self.user)
        self.assertFalse(tags.exists())

    def filter_tag_assigned_to_dataset(self):
        """ Test liting tags by those assigned to dataset """
        tag1 = Tag.objects.create(user = self.user, name='Breakfast')
        tag2 = Tag.objects.create(user = self.user, name='Launch')

        dataset = Dataset.objects.create(
            title='Green eggs on toast',
            time_minutes=5,
            price=Decimal('4.50'),
            user=self.user
        )

        dataset.tags.add(tag1)

        res = self.client.get(TAGS_URL, {'assigned_only':1})

        s1 = TagSerializer(tag1)
        s2 = TagSerializer(tag2)

        self.assertIn(s1.data, res.data)
        self.assertNotIn(s2.data, res.data)

    def test_filtered_tag_unique(self):
        """ Test filtered tags returns a unique list """
        tag = Tag.objects.create(user = self.user, name = 'Breakfast')
        Tag.objects.create(user = self.user, name = 'Dinner')
        dataset1 = Dataset.objects.create(
            title = 'pancakes',
            time_minutes = 5,
            price = Decimal('1.00'),
            user = self.user,
        )

        dataset2 = Dataset.objects.create(
            title = 'Porridge',
            time_minutes = 3,
            price = Decimal('5.00'),
            user = self.user,
        )

        dataset1.tags.add(tag)
        dataset2.tags.add(tag)

        res = self.client.get(TAGS_URL, {'assigned_only':1})
        self.assertEqual(len(res.data), 1)


        








