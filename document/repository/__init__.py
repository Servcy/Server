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

    @staticmethod
    def remove_documents(document_ids: list[int]):
        documents = Document.objects.filter(id__in=document_ids)
        for document in documents:
            if document.file:
                document.file.delete()
        documents.delete()

    @staticmethod
    def get_documents(self, filters: dict, return_values: list[str] = None):
        qs = Document.objects.filter(**filters)
        if return_values:
            qs = qs.values(*return_values)
        return qs
