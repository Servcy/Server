from rest_framework_simplejwt.serializers import TokenObtainPairSerializer


class JWTTokenSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token["id"] = user.id
        token["email"] = user.email
        token["username"] = user.username
        token["phone_number"] = user.phone_number
        token["invited_by"] = user.invited_by.id if user.invited_by else None
        token["profile_image"] = user.profile_image.url if user.profile_image else ""
        return token
