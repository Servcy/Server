from django.db import DatabaseError
from rest_framework import status
from rest_framework.exceptions import APIException


class ServcyBaseException(Exception):
    """
    Custom Exception Base Class for Servcy.
    """


class ServcyAPIException(APIException, ServcyBaseException):
    """
    Custom Rest Framework APIException for the Servcy server.
    """

    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    default_detail = "Servcy API encountered an error!"
    default_code = "APIException"


class MicroserviceException(ServcyAPIException):
    """
    Custom Exception for Servcy Microservices.
    """

    default_detail = "A Servcy microservice encountered an error!"
    default_code = "MicroServiceException"


class BusinessException(ServcyAPIException):
    """
    Custom Exception for Servcy Business Logic.
    """

    default_detail = "A Business Exception has occurred"
    default_code = "BusinessException"


class ServcyDBException(DatabaseError, ServcyBaseException):
    """
    Custom Database Exception BaseClass.
    """


class DisplayableError(ServcyBaseException):
    """
    Custom class for exceptions that have error messages that can be directly exposed to the user.
    """


class DataError(Exception):
    """
    To be used for custom classification of errors.
    """

    @property
    def message(self):
        return str(self)


class SerializerException(ServcyBaseException):
    """
    Custom class for exception raised from serializers.
    """

    default_detail = "A Serializer Exception has occured"
    default_code = "SerializerException"


class WriteSerializerException(SerializerException):
    """
    Custom class for exception raises from Write Serializers.
    """

    default_detail = "Exception occured while writing serializer"
    default_code = "WriteSerializer exception"


class ReadSerializerException(SerializerException):
    """
    Custom class for exceptions raised from Read Serializers.
    """

    default_detail = "Exception occured while reading serializer"
    default_code = "ReadSerializer exception"


class InadequateDataException(BusinessException):
    status_code = status.HTTP_412_PRECONDITION_FAILED
    default_detail = "Inadequate data available"


class JsonDataException(BusinessException):
    status_code = status.HTTP_412_PRECONDITION_FAILED
    default_detail = "JSON data is invalid. Possible Key Error."
