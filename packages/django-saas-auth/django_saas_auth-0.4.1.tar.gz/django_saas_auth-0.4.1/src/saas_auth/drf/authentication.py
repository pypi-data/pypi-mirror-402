import time

from django.core.cache import cache
from django.utils import timezone
from rest_framework.authentication import (
    TokenAuthentication as _TokenAuthentication,
)
from rest_framework.request import Request

from saas_auth.models import UserToken


class TokenAuthentication(_TokenAuthentication):
    keyword = 'Bearer'
    model = UserToken

    def authenticate(self, request: Request):
        credentials = super().authenticate(request)
        if credentials is None:
            return None

        user, token = credentials
        if token.expires_at and token.expires_at < timezone.now():
            return None

        if token.tenant_id:
            tenant_id = token.tenant_id
        else:
            tenant_id = getattr(request._request, 'tenant_id', None)
        request.tenant_id = tenant_id

        # persist for 3 months
        cache.set(token._cache_key, int(time.time()), 90 * 86400)
        return user, token
