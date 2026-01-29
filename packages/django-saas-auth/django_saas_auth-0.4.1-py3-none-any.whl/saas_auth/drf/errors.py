from rest_framework import status
from rest_framework.exceptions import APIException


class MFARequiredError(APIException):
    status_code = status.HTTP_401_UNAUTHORIZED
    default_detail = 'MFA required'
    default_code = 'mfa_required'


class MFAVerificationFailed(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = 'MFA verification failed'
    default_code = 'mfa_failed'
