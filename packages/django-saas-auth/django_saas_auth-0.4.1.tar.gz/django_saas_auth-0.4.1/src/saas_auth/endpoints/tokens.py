from rest_framework.mixins import CreateModelMixin, DestroyModelMixin, ListModelMixin
from saas_base.drf.views import AuthenticatedEndpoint

from saas_auth.drf.permissions import NotUseToken

from ..models import UserToken
from ..serializers import UserTokenSerializer

__all__ = [
    'UserTokenListEndpoint',
    'UserTokenItemEndpoint',
]


class UserTokenListEndpoint(ListModelMixin, CreateModelMixin, AuthenticatedEndpoint):
    serializer_class = UserTokenSerializer
    pagination_class = None
    queryset = UserToken.objects.all()
    permission_classes = [NotUseToken]

    def filter_queryset(self, queryset):
        return queryset.filter(user=self.request.user)

    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        return self.create(request, *args, **kwargs)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class UserTokenItemEndpoint(DestroyModelMixin, AuthenticatedEndpoint):
    serializer_class = UserTokenSerializer
    queryset = UserToken.objects.all()
    permission_classes = [NotUseToken]

    def filter_queryset(self, queryset):
        return queryset.filter(user=self.request.user)

    def delete(self, request, *args, **kwargs):
        return self.destroy(request, *args, **kwargs)
