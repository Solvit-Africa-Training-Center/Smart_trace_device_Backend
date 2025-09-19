# authentication/Serializers.py
from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import User


class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    name = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = User
        fields = (
            'id',
            'username',
            'email',
            'password',
            'name',
            'first_name',
            'last_name',
            'phone',
            'lost_location',
            'role',
            # 'serial_number',
            # 'device_image',
            # 'description',
            # 'lost_location',
        )
        extra_kwargs = {
            'username': {'required': False, 'allow_blank': True},
        }

    def to_internal_value(self, data):
        # map client fields to model
        data = data.copy()
        if 'phonenumber' in data and 'phone' not in data:
            data['phone'] = data.get('phonenumber')
        if 'location' in data and 'lost_location' not in data:
            data['lost_location'] = data.get('location')
        # split name into first/last
        if data.get('name') and not (data.get('first_name') or data.get('last_name')):
            full = str(data.get('name')).strip()
            parts = [p for p in full.split(' ') if p]
            if len(parts) == 1:
                data['first_name'] = parts[0]
                data['last_name'] = ''
            elif len(parts) > 1:
                data['first_name'] = parts[0]
                data['last_name'] = ' '.join(parts[1:])
        return super().to_internal_value(data)

    def create(self, validated_data):
        password = validated_data.pop('password')
        username = validated_data.get('username')
        if not username:
            base = (validated_data.get('first_name') or 'user').lower()
            suffix = 1
            candidate = base
            from .models import User as UserModel
            while UserModel.objects.filter(username=candidate).exists():
                suffix += 1
                candidate = f"{base}{suffix}"
            username = candidate
        user = User(
            username=username,
            email=validated_data.get('email'),
            phone=validated_data.get('phone'),
            lost_location=validated_data.get('lost_location'),
            role=validated_data.get('role', 'user'),
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', ''),
        )
        user.set_password(password)
        user.is_active = False  # User needs to verify email
        user.save()
        return user


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        email = data.get('email')
        password = data.get('password')

        if email and password:
            user = authenticate(email=email, password=password)
            if user:
                if user.is_active:
                    data['user'] = user
                else:
                    raise serializers.ValidationError('Account is not active.')
            else:
                raise serializers.ValidationError('Invalid credentials.')
        else:
            raise serializers.ValidationError('Must include email and password.')

        return data


class VerificationSerializer(serializers.Serializer):
    email = serializers.EmailField()
    code = serializers.CharField(max_length=6)


class ResendVerificationSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value):
        if not User.objects.filter(email=value).exists():
            raise serializers.ValidationError("No user with this email found.")
        return value
