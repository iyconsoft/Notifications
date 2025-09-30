from .error_types import *
from .error_messages import *
from ..libs.logging import logging


class BaseError(Exception):
    def __init__(self, message: str, verboseMessage=None, errorType=None, httpCode=None):
        self.message = message or internalServerErrorMessage
        self.verboseMessage = verboseMessage
        self.errorType = errorType or errorTypes['INTERNAL_SERVER_ERROR']
        self.httpCode = httpCode or statusCodes['500']

        logging.error(self.message)


class UnprocessableEntityError(BaseError):
    def __init__(self, message: str = unprocessableEntityErrorMessage, verboseMessage=None, errorType=None):
        super().__init__(
            message=message,
            httpCode=statusCodes["422"],
            errorType=errorType or errorTypes["UNPROCESSABLE_ENTITY"],
            verboseMessage=verboseMessage,
        )


class OperationForbiddenError(BaseError):
    def __init__(self, message: str = operationForbiddenErrorMessage, verboseMessage=None, errorType=None):
        super().__init__(
            message=message,
            httpCode=statusCodes["403"],
            errorType=errorType or errorTypes["OPERATION_FORBIDDEN"],
            verboseMessage=verboseMessage,
        )


class NotFoundError(BaseError):
    def __init__(self, message: str = notFoundErrorMessage, verboseMessage=None, errorType=None):
        super().__init__(
            message=message,
            httpCode=statusCodes["404"],
            errorType=errorType or errorTypes["NOT_FOUND_ERROR"],
            verboseMessage=verboseMessage,
        )


class UnauthorizedError(BaseError):
    def __init__(self, message: str = unauthorizedErrorMessage, verboseMessage=None):
        super().__init__(
            message=message,
            verboseMessage=verboseMessage,
            httpCode=statusCodes["401"],
            errorType=errorTypes["UNAUTHORIZED_ACCESS"],
        )


class BadRequestError(BaseError):
    def __init__(self, message: str = badRequestErrorMessage, verboseMessage=None):
        super().__init__(
            message=message,
            verboseMessage=verboseMessage,
            httpCode=statusCodes["400"],
            errorType=errorTypes["BAD_REQUEST"],
        )


class ServiceUnavailableError(BaseError):
    def __init__(self, message: str = serviceUnavailableErrorMessage, verboseMessage=None):
        super().__init__(
            message=message,
            verboseMessage=verboseMessage,
            httpCode=statusCodes["503"],
            errorType=errorTypes["SERVICE_UNAVAILABLE"],
        )


class RateLimitExceededError(BaseError):
    def __init__(self, message: str = rateLimitExceededMessage, verboseMessage=None):
        super().__init__(
            message=message,
            verboseMessage=verboseMessage,
            httpCode=statusCodes["429"],
            errorType=errorTypes["RATE_LIMIT_EXCEEDED"],
        )


class DuplicateResourceError(BaseError):
    def __init__(self, message: str, verboseMessage=None):
        super().__init__(
            message=message,
            verboseMessage=verboseMessage,
            httpCode=statusCodes["400"],
            errorType=errorTypes["DUPLICATE_RESOURCE"],
        )


class DatabaseCommitError(BaseError):
    def __init__(self, message: str = databaseCommitErrorMessage, verboseMessage=None):
        super().__init__(
            message=message,
            verboseMessage=verboseMessage,
            httpCode=statusCodes["500"],
            errorType=errorTypes["DATABASE_COMMIT_ERROR"]
        )