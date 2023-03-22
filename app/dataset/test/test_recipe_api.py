"""
Test for dataset APIs.
"""

from decimal import Decimal
import tempfile
import os

from PIL import Image

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Dataset, Tag, Ingredient

from dataset.serializers import DatasetSerializer, DatasetDetailSerializer

RECIPES_URL = reverse('dataset:dataset-list')

def detail_url(dataset_id):
    """ Create and return a dataset detail UTL  """
    return reverse('dataset:dataset-detail', args=[dataset_id])

def image_upload_url(dataset_id):
    """ Create and Return a dataset detail URL """
    return reverse('dataset:dataset-upload-image', args=[dataset_id])

def create_dataset(user, **params):
    """ Create and Return a sample dataset. """
    defaults = {
        'title':'Sample dataset title',
        'time_minutes':22,
        'price':Decimal('5.25'),
        'description':'Sample Description',
        'link':'http://example.com/dataset.pdf'
    }

    defaults.update(params)
    dataset = Dataset.objects.create(user=user, **defaults)
    return dataset


def create_user(**params):
    """ Create and Return a new user """
    return get_user_model().objects.create_user(**params)

class PublicDatasetAPITest(TestCase):
    """ Test unauthenticated API requests """
    def setUp(self):
        self.client = APIClient()
    
    def test_auth_required(self):
        """ Test auth is required to call API """
        res = self.client.get(RECIPES_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateDatasetAPITest(TestCase):
    """ Test authenticated API requests """
    def setUp(self):
        self.client = APIClient()
        self.user = create_user(email = 'user@example.com', password = 'testpass123')
        self.client.force_authenticate(self.user)

    def test_retrieve_datasets(self):
        """ Test retrieve a list of datasets """
        create_dataset(user=self.user)
        create_dataset(user=self.user)

        res = self.client.get(RECIPES_URL)

        datasets = Dataset.objects.all().order_by('-id')
        serializer = DatasetSerializer(datasets, many = True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_dataset_list_limited_to_user(self):
        """ Test list of datasets is limited to authenticated user """
        other_user = create_user(email = 'other@example.com', password = 'testpass123')
        create_dataset(user=other_user)
        create_dataset(user=self.user)

        res = self.client.get(RECIPES_URL)

        datasets = Dataset.objects.filter(user=self.user)
        serializer = DatasetSerializer(datasets, many = True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_get_dataset_detail(self):
        """ Test get dataset detail """
        dataset = create_dataset(user=self.user)

        url = detail_url(dataset.id)
        res = self.client.get(url)

        serializer = DatasetDetailSerializer(dataset)
        self.assertEqual(res.data, serializer.data)


    def test_create_dataset(self):
        """ Test creating a dataset """
        payload = {
            'title':'Sample Dataset',
            'time_minutes':30,
            'price':Decimal('5.99'),
        }

        res = self.client.post(RECIPES_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        dataset = Dataset.objects.get(id = res.data['id'])
        for k, v in payload.items():
            self.assertEqual(getattr(dataset, k), v)
        self.assertEqual(dataset.user, self.user)


    def test_partial_update(self):
        """ Test partial update of a dataset """
        original_link = 'https://example.com/dataset.pdf'
        dataset = create_dataset(
            user=self.user,
            title = 'Sample Dataset Title',
            link = original_link
        )

        payload = {'title':'New Dataset Title'}

        url = detail_url(dataset.id)
        res = self.client.patch(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        dataset.refresh_from_db()
        self.assertEqual(dataset.title, payload['title'])
        self.assertEqual(dataset.link, original_link)
        self.assertEqual(dataset.user, self.user)

    def test_full_update(self):
        """ Test full update of dataset """
        dataset = create_dataset(
            user=self.user,
            title = 'Sample Dataset Title',
            link = 'https://example.com/dataset.pdf',
            description = 'Sample dataset description'
        )

        payload = {
            'title':'New Dataset Title',
            'link':'https://example.com/new_dataset.pdf',
            'description':'new dataset description',
            'time_minutes':10,
            'price':Decimal('2.50')
        }

        url = detail_url(dataset.id)
        res = self.client.put(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        dataset.refresh_from_db()
        for k, v in payload.items():
            self.assertEqual(getattr(dataset, k),v)
        self.assertEqual(dataset.user, self.user)

    def test_update_user_returns_error(self):
        """ Test changing the dataset user results in an error """
        new_user = create_user(email='user2@example.com', password = 'test123')
        dataset = create_dataset(user=self.user)

        payload = {
            'user':new_user.id
        }

        url = detail_url(dataset.id)
        self.client.patch(url, payload)

        dataset.refresh_from_db()
        self.assertEqual(dataset.user, self.user)

    def test_delete_dataset(self):
        """ test deleting a dataset successful """
        dataset = create_dataset(user=self.user)

        url = detail_url(dataset.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Dataset.objects.filter(id=dataset.id).exists())

    def test_delete_other_user_dataset_error(self):
        """ Test trying to delete other users dataset gives error """
        new_user = create_user(email='user2@example.com', password = 'test123')
        dataset = create_dataset(user=new_user)

        url = detail_url(dataset.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(Dataset.objects.filter(id = dataset.id).exists())

    def test_create_dataset_with_new_tags(self):
        """ Test creating a dataset with new tags """
        payload = {
            'title':'Thai prawn Curry',
            'time_minutes':10,
            'price':Decimal('2.50'),
            'tags':[{'name':'Thai'},{'name':'Dinner'}]
        }       

        res = self.client.post(RECIPES_URL, payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        datasets = Dataset.objects.filter(user=self.user)
        self.assertEqual(datasets.count(),1)
        dataset = datasets[0]
        self.assertEqual(dataset.tags.count(), 2)
        for tag in payload['tags']:
            exists = dataset.tags.filter(
                name = tag['name'],
                user = self.user,
            ).exists()
            self.assertTrue(exists)

    def test_creating_dataset_with_existing_tags(self):
        """ Test creating a dataset with existing tag """
        tag_indian = Tag.objects.create(user = self.user, name = 'Indian')
        payload = {
            'title':'Pongal',
            'time_minutes':60,
            'price':Decimal('4.50'),
            'tags':[{'name':'Indian'},{'name':'Breakfast'}]
        }

        res =  self.client.post(RECIPES_URL, payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        datasets = Dataset.objects.filter(user=self.user)
        self.assertEqual(datasets.count(),1)
        dataset = datasets[0]
        self.assertEqual(dataset.tags.count(), 2)
        self.assertIn(tag_indian, dataset.tags.all())
        for tag in payload['tags']:
            exists = dataset.tags.filter(
                name = tag['name'],
                user = self.user,
            ).exists()
            self.assertTrue(exists)

    def test_create_tag_on_update(self):
        """ Test creating tag when updating a dataset """
        dataset = create_dataset(user=self.user)

        payload = {
            'tags':[
                {
                    'name':'Lunch'
                }
            ]
        }

        url = detail_url(dataset.id)
        res = self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        new_tag = Tag.objects.get(user = self.user, name = 'Lunch')
        self.assertIn(new_tag, dataset.tags.all())

    def test_update_dataset_assign_tag(self):
        """ Test assigning an existing tag when updating a dataset """
        tag_breakfast = Tag.objects.create(user = self.user, name='Breakfast')
        dataset = create_dataset(user = self.user)
        dataset.tags.add(tag_breakfast)

        tag_lunch = Tag.objects.create(user = self.user, name='Lunch')
        payload = {
            'tags':[
                {
                    'name':'Lunch'
                }
            ]
        }

        url = detail_url(dataset.id)
        res = self.client.patch(url, payload, format='json')    
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn(tag_lunch, dataset.tags.all())
        self.assertNotIn(tag_breakfast, dataset.tags.all())

    def test_clear_dataset_tags(self):
        """ Test clearing a dataset tag """
        tag = Tag.objects.create(user = self.user, name = 'Dessert')
        dataset = create_dataset(user = self.user)
        dataset.tags.add(tag)

        payload = {'tags':[]}
        url = detail_url(dataset.id)
        res = self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(dataset.tags.count(), 0)

    def test_creating_dataset_with_new_ingredient(self):
        """ Test creating a dataset with new ingredient """
        payload = {
            'title':'Caulifalower Taco',
            'time_minutes':60,
            'price':Decimal('4.50'),
            'ingredients':[{'name':'Cauliflower'},{'name':'Salt'}]
        }
        res =  self.client.post(RECIPES_URL, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        datasets = Dataset.objects.filter(user=self.user)
        self.assertEqual(datasets.count(),1)
        dataset = datasets[0]
        self.assertEqual(dataset.ingredients.count(), 2)
        
        for ingredient in payload['ingredients']:
            exists = dataset.ingredients.filter(
                name = ingredient['name'],
                user = self.user,
            ).exists()
            self.assertTrue(exists)


    def test_creating_dataset_with_existing_ingredients(self):
            """ Test creating a dataset with existing ingredients """
            ingredient = Ingredient.objects.create(user = self.user, name = 'Lemon')
            payload = {
                'title':'Vietnamese Soup',
                'time_minutes':20,
                'price':Decimal('4.55'),
                'ingredients':[{'name':'Lemon'},{'name':'Fish Sauce'}]
            }

            res =  self.client.post(RECIPES_URL, payload, format='json')
            self.assertEqual(res.status_code, status.HTTP_201_CREATED)
            datasets = Dataset.objects.filter(user=self.user)
            self.assertEqual(datasets.count(),1)
            dataset = datasets[0]
            self.assertEqual(dataset.ingredients.count(), 2)
            self.assertIn(ingredient, dataset.ingredients.all())
            for ingredient in payload['ingredients']:
                exists = dataset.ingredients.filter(
                    name = ingredient['name'],
                    user = self.user,
                ).exists()
                self.assertTrue(exists)


    def test_create_ingredient_on_update(self):
        """ Test creating ingredient when updating a dataset """
        dataset = create_dataset(user=self.user)

        payload = {
            'ingredients':[
                {
                    'name':'Limes'
                }
            ]
        }

        url = detail_url(dataset.id)
        res = self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        new_ingredient = Ingredient.objects.get(user = self.user, name = 'Limes')
        self.assertIn(new_ingredient, dataset.ingredients.all())


    def test_update_dataset_assign_ingredient(self):
        """ Test assigning an existing ingredient when updating a dataset """
        ingredient1 = Ingredient.objects.create(user = self.user, name='Pepper')
        dataset = create_dataset(user = self.user)
        dataset.ingredients.add(ingredient1)

        ingredient2 = Ingredient.objects.create(user = self.user, name='Chili')

        payload = {
            'ingredients':[
                {
                    'name':'Chili'
                }
            ]
        }

        url = detail_url(dataset.id)
        res = self.client.patch(url, payload, format='json')    
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        self.assertIn(ingredient2, dataset.ingredients.all())
        self.assertNotIn(ingredient1, dataset.ingredients.all())

    def test_clear_dataset_ingredients(self):
        """ Test clearing a dataset ingredient """
        ingredient = Ingredient.objects.create(user = self.user, name = 'Garlic')
        dataset = create_dataset(user = self.user)
        dataset.ingredients.add(ingredient)

        payload = {'ingredients':[]}
        url = detail_url(dataset.id)
        res = self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(dataset.ingredients.count(), 0)


    def test_filter_by_tags(self):
        """ Test filtering datasets by tags """
        r1 = create_dataset(user=self.user, title = "Thai Vegetable Curry")
        r2 = create_dataset(user=self.user, title = "Aubergine  with Tahini")
        tag1 = Tag.objects.create(user = self.user, name = 'Vegan')
        tag2 = Tag.objects.create(user = self.user, name = 'Vegeterian')
        r1.tags.add(tag1)
        r2.tags.add(tag2)

        r3 = create_dataset(user=self.user, title = "Fish and Chips")

        params = {'tags': f'{tag1.id},{tag2.id}'}
        res = self.client.get(RECIPES_URL, params)

        s1 = DatasetSerializer(r1)
        s2 = DatasetSerializer(r2)
        s3 = DatasetSerializer(r3)

        self.assertIn(s1.data, res.data)
        self.assertIn(s2.data, res.data)
        self.assertNotIn(s3.data, res.data)

    def test_filter_by_ingredients(self):
        """ Test filtering datasets by ingredients """
        r1 = create_dataset(user=self.user, title = "Posh beans on toast")
        r2 = create_dataset(user=self.user, title = "Chicken Cacciatore")
        in1 = Ingredient.objects.create(user = self.user, name = 'Feta Chease')
        in2 = Ingredient.objects.create(user = self.user, name = 'Chicken')
        r1.ingredients.add(in1)
        r2.ingredients.add(in2)

        r3 = create_dataset(user=self.user, title = "Red Lentil")

        params = {'ingredients': f'{in1.id},{in2.id}'}
        res = self.client.get(RECIPES_URL, params)

        s1 = DatasetSerializer(r1)
        s2 = DatasetSerializer(r2)
        s3 = DatasetSerializer(r3)

        self.assertIn(s1.data, res.data)
        self.assertIn(s2.data, res.data)
        self.assertNotIn(s3.data, res.data)

class ImageUploadTest(TestCase):
    """ Test for the image upload API """
    
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            'user@example.com',
            'password123',
        )

        self.client.force_authenticate(self.user)
        self.dataset = create_dataset(user = self.user)

    def tearDown(self):
        self.dataset.image.delete() 

    def test_upload_image(self):
        """ Test uploading an image to a dataset """
        url = image_upload_url(self.dataset.id)
        with tempfile.NamedTemporaryFile(suffix='.jpg') as image_file:
            img = Image.new('RGB',(10,10))
            img.save(image_file, format='JPEG')
            image_file.seek(0)
            payload = {'image':image_file}
            res = self.client.post(url, payload, format='multipart')

        self.dataset.refresh_from_db()
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn('image', res.data)
        self.assertTrue(os.path.exists(self.dataset.image.path))

    def test_upload_image_bad_request(self):
        """ Test uploading invalid image """
        url = image_upload_url(self.dataset.id)
        payload = {'image':'notanimage'}
        res = self.client.post(url, payload, format='multipart')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
       