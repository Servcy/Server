from document.models import Document


class DocumentRepository:
    @staticmethod
    def create(**kwargs):
        return Document.objects.create(**kwargs)
