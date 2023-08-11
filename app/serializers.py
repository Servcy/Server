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
