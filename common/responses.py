import json
import logging
import traceback

from rest_framework import status
from rest_framework.response import Response


def success_response(
    results: list | dict = None,
    success_message: str = "Success!",
    status=status.HTTP_200_OK,
):
    return Response(
        {
            "detail": success_message,
            "results": json.dumps(results),
        },
        status=status,
    )


def error_response(
    error_message: str = "An error occurred. Please try again later!",
    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
    logger: logging.Logger = None,
    logger_message=None,
):
    if logger:
        logger.exception(
            logger_message if logger_message else error_message,
            extra={
                "traceback": traceback.format_exc(),
            },
        )
    return Response(
        {
            "detail": error_message,
        },
        status=status,
    )
