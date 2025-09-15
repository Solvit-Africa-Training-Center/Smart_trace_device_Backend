import random
from django.contrib.auth import login, authenticate
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status, serializers
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from drf_spectacular.utils import extend_schema
from .models import User, VerificationCode
from .Serializers import UserSerializer, LoginSerializer, VerificationSerializer, ResendVerificationSerializer


# ======================
# Response Serializers (for Swagger docs only)
# ======================
class RegisterResponseSerializer(serializers.Serializer):
    message = serializers.CharField()
    user_id = serializers.IntegerField()


class VerifyResponseSerializer(serializers.Serializer):
    message = serializers.CharField()
    refresh = serializers.CharField()
    access = serializers.CharField()


class LoginResponseSerializer(serializers.Serializer):
    message = serializers.CharField()
    refresh = serializers.CharField()
    access = serializers.CharField()
    user = UserSerializer()


class ResendCodeResponseSerializer(serializers.Serializer):
    message = serializers.CharField()


class ErrorResponseSerializer(serializers.Serializer):
    error = serializers.CharField()


def send_verification_email(user, verification_code):
    """Utility to send verification email."""
    subject = 'Verify Your Email - Lost and Found Tracker'
    html_message = render_to_string('emails/verification_code.html', {
        'user': user,
        'verification_code': verification_code,
    })
    plain_message = strip_tags(html_message)

    send_mail(
        subject,
        plain_message,
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
        html_message=html_message,
        fail_silently=False,
    )


# ======================
# Function-based Views
# ======================

@extend_schema(
    tags=["Authentication"],
    request=UserSerializer,
    responses={201: RegisterResponseSerializer, 400: ErrorResponseSerializer},
    summary="Register a new user",
    description="Registers a new user and sends a verification code via email."
)
@api_view(['POST'])
@permission_classes([AllowAny])
def register_user(request):
    serializer = UserSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()

        # Generate and save verification code
        verification_code = str(random.randint(100000, 999999))
        VerificationCode.objects.create(user=user, code=verification_code)

        # Send email
        send_verification_email(user, verification_code)

        return Response({
            'message': 'User registered successfully. Please check your email for the verification code.',
            'user_id': user.id
        }, status=status.HTTP_201_CREATED)

    return Response({'error': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    tags=["Authentication"],
    request=VerificationSerializer,
    responses={200: VerifyResponseSerializer, 400: ErrorResponseSerializer, 404: ErrorResponseSerializer},
    summary="Verify user's email",
    description="Verifies the user's email using the code sent via email and returns JWT tokens."
)
@api_view(['POST'])
@permission_classes([AllowAny])
def verify_email(request):
    serializer = VerificationSerializer(data=request.data)
    if serializer.is_valid():
        email = serializer.validated_data['email']
        code = serializer.validated_data['code']

        try:
            user = User.objects.get(email=email)
            verification_code = VerificationCode.objects.filter(
                user=user,
                code=code,
                is_used=False
            ).order_by('-created_at').first()

            if not verification_code:
                return Response({'error': 'Invalid or expired verification code.'},
                                status=status.HTTP_400_BAD_REQUEST)

            # Mark code as used and activate user
            verification_code.is_used = True
            verification_code.save()

            user.is_active = True
            user.save()

            # Generate JWT tokens
            refresh = RefreshToken.for_user(user)

            return Response({
                'message': 'Email verified successfully.',
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }, status=status.HTTP_200_OK)

        except User.DoesNotExist:
            return Response({'error': 'User not found.'}, status=status.HTTP_404_NOT_FOUND)

    return Response({'error': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    tags=["Authentication"],
    request=LoginSerializer,
    responses={200: LoginResponseSerializer, 400: ErrorResponseSerializer},
    summary="Login user",
    description="Logs in a user and returns JWT tokens."
)
@api_view(['POST'])
@permission_classes([AllowAny])
def login_user(request):
    serializer = LoginSerializer(data=request.data)
    if serializer.is_valid():
        email = serializer.validated_data['email']
        password = serializer.validated_data['password']

        user = authenticate(request, email=email, password=password)

        if not user:
            return Response({'error': 'Invalid credentials.'}, status=status.HTTP_400_BAD_REQUEST)

        if not user.is_active:
            return Response({'error': 'Account is not active. Please verify your email.'},
                            status=status.HTTP_400_BAD_REQUEST)

        # Login and generate tokens
        login(request, user)
        refresh = RefreshToken.for_user(user)

        return Response({
            'message': 'Login successful.',
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'user': UserSerializer(user).data
        }, status=status.HTTP_200_OK)

    return Response({'error': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    tags=["Authentication"],
    request=ResendVerificationSerializer,
    responses={200: ResendCodeResponseSerializer, 400: ErrorResponseSerializer, 404: ErrorResponseSerializer},
    summary="Resend verification code",
    description="Generates a new verification code and sends it to the user's email."
)
@api_view(['POST'])
@permission_classes([AllowAny])
def resend_verification_code(request):
    serializer = ResendVerificationSerializer(data=request.data)
    if serializer.is_valid():
        email = serializer.validated_data['email']

        try:
            user = User.objects.get(email=email)

            # Generate new verification code
            verification_code = str(random.randint(100000, 999999))
            # Deactivate all previous codes for this user/email
            VerificationCode.objects.filter(user=user, is_used=False).update(is_used=True)
            # Create new code
            VerificationCode.objects.create(user=user, code=verification_code)

            # Send email
            send_verification_email(user, verification_code)

            return Response({'message': 'Verification code sent successfully.'}, status=status.HTTP_200_OK)

        except User.DoesNotExist:
            return Response({'error': 'User not found.'}, status=status.HTTP_404_NOT_FOUND)

    return Response({'error': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)