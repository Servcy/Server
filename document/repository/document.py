from document.models import Document


class DocumentRepository:
    @staticmethod
    def create(**kwargs):
        return Document.objects.create(**kwargs)

    @staticmethod
    def add_documents(documents: list[dict]):
        return Document.objects.bulk_create(
            [Document(**document) for document in documents]
        )
