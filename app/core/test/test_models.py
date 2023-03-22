"""
Test for models
"""
from unittest.mock import patch
from decimal import Decimal

from django.test import TestCase
from django.contrib.auth import get_user_model

from core import models

def create_user(email='user@example.com', password='testpass123'):
    """ Create and return a new user """
    return get_user_model().objects.create_user(email, password)


class ModelTest(TestCase):
    """ Test Models """

    def test_create_user_with_email_successfull(self):
        """ Test creating user with email and pass successfully """
        email = 'test@example.com'
        password='testpass123'
        user = get_user_model().objects.create_user(
            email=email,
            password = password
        )

        self.assertEqual(user.email, email)
        self.assertTrue(user.check_password(password))

    def test_new_user_email_normalized(self):
        """ Test email is normalized for new users """
        sample_emails = [
            ['test1@EXAMPLE.com','test1@example.com'],
            ['test2@Example.com','test2@example.com'],
            ['TEST3@EXAMPLE.COM','TEST3@example.com'],
            ['test4@example.COM','test4@example.com']
        ]

        for email , expected in sample_emails:
            user = get_user_model().objects.create_user(email, 'sample123')
            self.assertEqual(user.email, expected)

    def test_new_user_email_without_eamil_raises_error(self):
        """ Test the creating a user whitout an email rasies a ValueError """
        with self.assertRaises(ValueError):
            get_user_model().objects.create_user('','test123')

    def test_create_superuser(self):
        """ Tesing create superuser """
        user = get_user_model().objects.create_superuser('test@example.com','test123',)
        
        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_staff)

    def test_create_dataset(self):
        """ Test creating a dataset is successful """
        user = get_user_model().objects.create_user(
            'test@example.com',
            'testpass123'
        )
        dataset = models.Dataset.objects.create(
            user = user,
            title = 'Sample dataset test',
            time_minutes = 5,
            price = Decimal('5.50'),
            description = ' Sample dataset description',

        )

        self.assertEqual(str(dataset), dataset.title)

    def test_create_tag(self):
        """ Test creating a tag is successful """
        user =create_user()
        tag = models.Tag.objects.create(user=user, name='tag1')

        self.assertEqual(str(tag), tag.name)


    def test_create_ingredient(self):
        """ Test creating an ingredient is successful """
        user = create_user()
        ingredient = models.Ingredient.objects.create(
            user = user,
            name = 'Ingredient1'
        )

        self.assertEqual(str(ingredient), ingredient.name)


    @patch('core.models.uuid.uuid4')
    def test_dataset_file_name_uuid(self, mock_uuid):
        """ Test generating image path """
        uuid = 'test-build'
        mock_uuid.return_value= uuid
        file_path = models.dataset_image_file_path(None, 'example.jpg')

        self.assertEqual(file_path, f'uploads/dataset/{uuid}.jpg')
