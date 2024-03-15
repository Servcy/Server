from document.models import Document


class DocumentRepository:
    @staticmethod
    def add_document(**kwargs):
        return Document.objects.create(**kwargs)

    @staticmethod
    def remove_documents(document_ids: list[int]):
        documents = Document.objects.filter(id__in=document_ids)
        for document in documents:
            if document.file:
                document.file.delete()
        documents.delete()

    @staticmethod
    def get_documents(filters: dict, return_values: list[str] = None):
        qs = Document.objects.filter(**filters)
        if return_values:
            qs = qs.values(*return_values)
        return qs

    @staticmethod
    def get_document(filters: dict):
        return Document.objects.get(**filters, is_deleted=False)
