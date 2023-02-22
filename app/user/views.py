"""
Views for the User API
"""
import random

from django.core.mail import send_mail
from django.contrib.auth.models import User

from rest_framework import generics, authentication, permissions, status
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.settings import api_settings
from rest_framework.response import Response

from user.serializers import UserSerializer, AuthTokenSerializer

class CreateUserView(generics.CreateAPIView):
    """ Create a new user in the system """
    serializer_class = UserSerializer



class CreateTokenView(ObtainAuthToken):
    """ Create new auth-token for user """

    serializer_class = AuthTokenSerializer
    renderer_classes = api_settings.DEFAULT_RENDERER_CLASSES


class ManageUserView(generics.RetrieveUpdateAPIView):
    """ Manage the authentication user """
    serializer_class = UserSerializer
    authentication_classes = [authentication.TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        """ Retrieve and return the authenticated user. """
        return self.request.user

    def send_activation_code(self, user):
        " Sending activation code for retrieve user account"
        activation_code = random.randint(100000, 999999)
        user.forgot_password_token = activation_code
        user.save()

        send_mail(
            'Password Reset Request',
            f'Your password reset activation code is: {activation_code}',
            'from@example.com',
            [user.email],
            fail_silently=False,
        )

    def post(self, request, *args, **kwargs):
        email = request.data.get('email')
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({'error': 'User not found.'}, status=status.HTTP_404_NOT_FOUND)

        self.send_activation_code(user)

        return Response({'message': 'Password reset activation code sent.'}, status=status.HTTP_200_OK)

    
