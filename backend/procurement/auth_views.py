from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView
from .user_utils import get_user_role


class EmailTokenObtainPairSerializer(TokenObtainPairSerializer):
    username_field = 'email'

    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')

        if email and password:
            # Try to authenticate using email as username
            try:
                user = User.objects.get(email=email)
                user = authenticate(username=user.username, password=password)
                if user:
                    # Add custom claims
                    refresh = RefreshToken.for_user(user)
                    data = {
                        'refresh': str(refresh),
                        'access': str(refresh.access_token),
                        'user': {
                            'id': user.id,
                            'username': user.username,
                            'email': user.email,
                            'full_name': user.get_full_name() or f"{user.first_name} {user.last_name}".strip(),
                            'role': get_user_role(user)
                        }
                    }
                    return data
                else:
                    raise ValueError('Invalid credentials')
            except User.DoesNotExist:
                raise ValueError('User not found')
        else:
            raise ValueError('Email and password required')


class EmailTokenObtainPairView(TokenObtainPairView):
    serializer_class = EmailTokenObtainPairSerializer


@api_view(['GET'])
@permission_classes([])
def get_profile(request):
    """Get user profile information"""
    if request.user.is_authenticated:
        return Response({
            'id': request.user.id,
            'username': request.user.username,
            'email': request.user.email,
            'full_name': request.user.get_full_name() or f"{request.user.first_name} {request.user.last_name}".strip(),
            'role': get_user_role(request.user)
        })
    else:
        return Response({'error': 'Not authenticated'}, status=status.HTTP_401_UNAUTHORIZED)