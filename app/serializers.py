from django.db.models import (
    AutoField,
    BooleanField,
    CharField,
    DateTimeField,
    DecimalField,
    ForeignKey,
    IntegerField,
    OneToOneField,
    SmallIntegerField,
    TextField,
)
from rest_framework import serializers
from serpy import BoolField, FloatField, IntField, Serializer, StrField
from serpy.serializer import SerializerBase, SerializerMeta

ALL_FIELDS = "__all__"


class ServcyFloatField(FloatField):
    """
    Overriding the base FloatField to handle null values.
    """

    def to_value(self, value):
        if not value:
            return float(0)
        return float(value)


class ServcyIntField(IntField):
    """
    Overriding the base IntField to handle null values.
    """

    def to_value(self, value):
        if not value:
            return 0
        return int(value)


class ServcyStrField(StrField):
    """
    Overriding the base StrField to handle null values.
    """

    def to_value(self, value):
        if not value:
            return ""
        return str(value)


class ServcyForeignKeyField(IntField):
    """
    Overriding the base IntField to handle null values.
    """

    def to_value(self, value):
        if not value:
            return None
        return int(value)


model_field_serializer_field_mapping = {
    IntegerField: ServcyIntField,
    AutoField: ServcyIntField,
    ForeignKey: ServcyForeignKeyField,
    CharField: StrField,
    DateTimeField: StrField,
    TextField: StrField,
    DecimalField: ServcyFloatField,
    OneToOneField: ServcyIntField,
    BooleanField: BoolField,
    SmallIntegerField: ServcyIntField,
}


class ServcyMeta(SerializerBase, SerializerMeta):
    def __new__(cls, name, bases, dct):
        meta_class = dct.get("Meta", None)
        if meta_class:
            # accessing model in Meta class of serializer
            model = meta_class.model
            # accessing fields in Meta class of serializer
            declared_fields = getattr(meta_class, "fields", ALL_FIELDS)
            if (
                declared_fields
                and declared_fields != ALL_FIELDS
                and not isinstance(declared_fields, (list, tuple))
            ):
                raise TypeError(
                    'The `fields` option must be a list or tuple or "__all__". '
                    f"Got {type(declared_fields).__name__}."
                )
            fields = model._meta.fields
            declared_field_check = declared_fields != ALL_FIELDS
            dct["_model"] = model
            for field in fields:
                data_type = type(field)
                field_name = field.name + (
                    "_id" if data_type in [ForeignKey, OneToOneField] else ""
                )
                # makes sure that only declared fields are set
                if declared_field_check and field_name not in declared_fields:
                    continue
                dct[field_name] = model_field_serializer_field_mapping.get(
                    data_type, StrField
                )()
        return super(ServcyMeta, cls).__new__(cls, name, bases, dct)

    def __init__(cls, name, bases, dct):
        super(ServcyMeta, cls).__init__(name, bases, dct)


class ServcyReadSerializer(Serializer, metaclass=ServcyMeta):
    pass


class ServcyBaseSerializer(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(read_only=True)


class ServcyDynamicBaseSerializer(ServcyBaseSerializer):
    def __init__(self, *args, **kwargs):
        """
        If 'fields' is provided in the arguments, remove it and store it separately.
        This is done so as not to pass this custom argument up to the superclass.
        """
        fields = kwargs.pop("fields", [])
        self.expand = kwargs.pop("expand", []) or []
        fields = self.expand
        super().__init__(*args, **kwargs)
        if fields is not None:
            self.fields = self._filter_fields(fields)

    def _filter_fields(self, fields):
        """
        Adjust the serializer's fields based on the provided 'fields' list.

        :param fields: List or dictionary specifying which fields to include in the serializer.
        :return: The updated fields for the serializer.
        """
        for field_name in fields:
            if isinstance(field_name, dict):
                for key, value in field_name.items():
                    if isinstance(value, list):
                        self._filter_fields(self.fields[key], value)
        allowed = []
        for item in fields:
            # If the item is a string, it directly represents a field's name.
            if isinstance(item, str):
                allowed.append(item)
            # If the item is a dictionary, it represents a nested field.
            # Add the key of this dictionary to the allowed list.
            elif isinstance(item, dict):
                allowed.append(list(item.keys())[0])
        for field in allowed:
            if field not in self.fields:
                from iam.serializers import UserLiteSerializer, WorkspaceLiteSerializer
                from project.serializers import (
                    CycleIssueSerializer,
                    IssueAttachmentLiteSerializer,
                    IssueLinkLiteSerializer,
                    IssueLiteSerializer,
                    IssueReactionLiteSerializer,
                    IssueRelationSerializer,
                    IssueSerializer,
                    LabelSerializer,
                    ProjectLiteSerializer,
                    StateLiteSerializer,
                )

                # Expansion mapper
                expansion = {
                    "user": UserLiteSerializer,
                    "workspace": WorkspaceLiteSerializer,
                    "project": ProjectLiteSerializer,
                    "default_assignee": UserLiteSerializer,
                    "lead": UserLiteSerializer,
                    "state": StateLiteSerializer,
                    "created_by": UserLiteSerializer,
                    "issue": IssueSerializer,
                    "actor": UserLiteSerializer,
                    "owned_by": UserLiteSerializer,
                    "members": UserLiteSerializer,
                    "assignees": UserLiteSerializer,
                    "labels": LabelSerializer,
                    "issue_cycle": CycleIssueSerializer,
                    "parent": IssueLiteSerializer,
                    "issue_relation": IssueRelationSerializer,
                    "issue_reactions": IssueReactionLiteSerializer,
                    "issue_attachment": IssueAttachmentLiteSerializer,
                    "issue_link": IssueLinkLiteSerializer,
                    "sub_issues": IssueLiteSerializer,
                }

                self.fields[field] = expansion[field](
                    many=(
                        True
                        if field
                        in [
                            "members",
                            "assignees",
                            "labels",
                            "issue_cycle",
                            "issue_relation",
                            "issue_inbox",
                            "issue_reactions",
                            "issue_attachment",
                            "issue_link",
                            "sub_issues",
                        ]
                        else False
                    )
                )
        return self.fields

    def to_representation(self, instance):
        """
        Overriding the default to_representation method to handle the expansion of fields.
        """
        response = super().to_representation(instance)
        if not self.expand:
            return response
        for expand in self.expand:
            if expand not in self.fields:
                continue
            from iam.serializers import UserLiteSerializer, WorkspaceLiteSerializer
            from project.serializers import (
                CycleIssueSerializer,
                IssueAttachmentLiteSerializer,
                IssueLinkLiteSerializer,
                IssueLiteSerializer,
                IssueReactionLiteSerializer,
                IssueRelationSerializer,
                IssueSerializer,
                LabelSerializer,
                ProjectLiteSerializer,
                StateLiteSerializer,
            )

            expansion = {
                "user": UserLiteSerializer,
                "workspace": WorkspaceLiteSerializer,
                "project": ProjectLiteSerializer,
                "default_assignee": UserLiteSerializer,
                "lead": UserLiteSerializer,
                "state": StateLiteSerializer,
                "created_by": UserLiteSerializer,
                "issue": IssueSerializer,
                "actor": UserLiteSerializer,
                "owned_by": UserLiteSerializer,
                "members": UserLiteSerializer,
                "assignees": UserLiteSerializer,
                "labels": LabelSerializer,
                "issue_cycle": CycleIssueSerializer,
                "parent": IssueLiteSerializer,
                "issue_relation": IssueRelationSerializer,
                "issue_reactions": IssueReactionLiteSerializer,
                "issue_attachment": IssueAttachmentLiteSerializer,
                "issue_link": IssueLinkLiteSerializer,
                "sub_issues": IssueLiteSerializer,
            }
            if expand in expansion:
                if isinstance(response.get(expand), list):
                    exp_serializer = expansion[expand](
                        getattr(instance, expand), many=True
                    )
                else:
                    exp_serializer = expansion[expand](getattr(instance, expand))
                response[expand] = exp_serializer.data
            else:
                response[expand] = getattr(instance, f"{expand}_id", None)
        return response
