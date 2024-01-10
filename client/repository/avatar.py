from client.models import Avatar


class AvatarRepository:
    @staticmethod
    def create(**kwargs):
        return Avatar.objects.create(**kwargs)
