import random
from django.contrib.auth import login, authenticate
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status, serializers
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from drf_spectacular.utils import extend_schema
from .models import User, VerificationCode
from .Serializers import UserSerializer, LoginSerializer, VerificationSerializer, ResendVerificationSerializer


# ======================
# Response Serializers (Swagger only)
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


# Request serializer to shape OpenAPI exactly as the product UI
class RegisterRequestSerializer(serializers.Serializer):
    name = serializers.CharField()
    email = serializers.EmailField()
    location = serializers.CharField(required=False, allow_blank=True)
    phonenumber = serializers.CharField(required=False, allow_blank=True)
    password = serializers.CharField()


# ======================
# Utility function
# ======================
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
# Views
# ======================

@extend_schema(
    tags=["Authentication"],
    request=RegisterRequestSerializer,
    responses={201: RegisterResponseSerializer, 400: ErrorResponseSerializer},
    summary="Register a new user",
    description="Registers a new user and sends a verification code via email."
)
@api_view(['POST'])
@permission_classes([AllowAny])
def register_user(request):
    # Use request serializer for documentation, but persist via UserSerializer
    _ = RegisterRequestSerializer(data=request.data)
    # We still validate/persist with the full user serializer which maps name/location/phonenumber
    serializer = UserSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()

        # Generate and save verification code
        verification_code = str(random.randint(100000, 999999))
        VerificationCode.objects.create(user=user, code=verification_code)

        # Send email
        send_verification_email(user, verification_code)

        # Store pending user in session for button-only resend flow
        try:
            request.session['pending_user_id'] = user.id
            request.session.save()
        except Exception:
            pass

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
    # Button-only flow: no body required. Resolve user in priority order.
    user = None
    if getattr(request, 'user', None) and request.user.is_authenticated:
        user = request.user
    else:
        pending_user_id = request.session.get('pending_user_id')
        if pending_user_id:
            try:
                user = User.objects.get(id=pending_user_id)
            except User.DoesNotExist:
                user = None

    if not user:
        return Response({'error': 'No pending user found for this session.'}, status=status.HTTP_400_BAD_REQUEST)

    # Generate new verification code
    verification_code = str(random.randint(100000, 999999))
    VerificationCode.objects.create(user=user, code=verification_code)

    # Send email to the already-registered email
    send_verification_email(user, verification_code)

    return Response({'message': 'Verification code sent successfully.'}, status=status.HTTP_200_OK)


# ======================
# User management APIs
# ======================

@extend_schema(
	tags=["Authentication"],
	responses=UserSerializer(many=True),
	summary="List users",
	description="List all users (admin only)."
)
@api_view(['GET'])
@permission_classes([AllowAny])
def users_list(request):
	if not request.user.is_staff:
		return Response({'detail': 'Not authorized.'}, status=status.HTTP_403_FORBIDDEN)
	users = User.objects.all().order_by('-date_joined')
	serializer = UserSerializer(users, many=True)
	return Response(serializer.data)


@extend_schema(
	tags=["Authentication"],
	responses=UserSerializer,
	summary="Retrieve user",
	description="Retrieve a user by ID (admin only)."
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_detail(request, id):
	if not request.user.is_staff:
		return Response({'detail': 'Not authorized.'}, status=status.HTTP_403_FORBIDDEN)
	try:
		user = User.objects.get(id=id)
	except User.DoesNotExist:
		return Response({'detail': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)
	serializer = UserSerializer(user)
	return Response(serializer.data)


@extend_schema(
	tags=["Authentication"],
	request=UserSerializer,
	responses=UserSerializer,
	summary="Update my profile",
	description="Update the authenticated user's profile."
)
@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def me_update(request):
	user = request.user
	serializer = UserSerializer(user, data=request.data, partial=True)
	if serializer.is_valid():
		serializer.save()
		return Response(serializer.data)
	return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
	tags=["Authentication"],
	responses=None,
	summary="Delete user",
	description="Delete a user by ID (admin only)."
)
@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def user_delete(request, id):
	if not request.user.is_staff:
		return Response({'detail': 'Not authorized.'}, status=status.HTTP_403_FORBIDDEN)
	try:
		user = User.objects.get(id=id)
	except User.DoesNotExist:
		return Response({'detail': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)
	user.delete()
	return Response(status=status.HTTP_204_NO_CONTENT)
