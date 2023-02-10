"""
Test for models
"""

from django.test import TestCase
from django.contrib.auth import get_user_model

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
