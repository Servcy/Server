from django.contrib.auth.models import BaseUserManager


class UserAccountManager(BaseUserManager):
    def create_superuser(
        self,
        username: str,
        email: str,
        phone_number: str,
        password: str,
        **other_fields
    ):
        other_fields.setdefault("is_staff", True)
        other_fields.setdefault("is_superuser", True)
        other_fields.setdefault("is_active", True)
        if other_fields.get("is_staff") is not True:
            raise ValueError("Superuser must be assigned to is_staff=True")
        if other_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must be assigned to is_superuser=True")
        user = self.create_user(username, email, phone_number, password, **other_fields)
        user.set_password(password)
        user.save()
        return user

    def create_user(self, username, email, phone_number, password, **other_fields):
        if not email and not phone_number:
            raise ValueError("You must provide an email or phone number!")
        email = self.normalize_email(email)
        user = self.model(
            username=username,
            email=email,
            phone_number=phone_number,
            password=password,
            is_active=True,
            **other_fields
        )
        user.set_unusable_password()
        user.save()
        return user
