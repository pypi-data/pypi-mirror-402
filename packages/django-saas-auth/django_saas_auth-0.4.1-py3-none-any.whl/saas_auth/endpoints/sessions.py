from rest_framework.mixins import DestroyModelMixin, ListModelMixin, RetrieveModelMixin
from saas_base.drf.decorators import resource_permission
from saas_base.drf.views import AuthenticatedEndpoint

from saas_auth.models import Session
from saas_auth.serializers import SessionSerializer

__all__ = [
    'SessionRecordListEndpoint',
    'SessionRecordItemEndpoint',
]


class SessionRecordListEndpoint(ListModelMixin, AuthenticatedEndpoint):
    queryset = Session.objects.all()
    serializer_class = SessionSerializer

    def filter_queryset(self, queryset):
        return queryset.filter(user=self.request.user)

    @resource_permission('user.session.view')
    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)


class SessionRecordItemEndpoint(RetrieveModelMixin, DestroyModelMixin, AuthenticatedEndpoint):
    queryset = Session.objects.all()
    serializer_class = SessionSerializer

    def filter_queryset(self, queryset):
        return queryset.filter(user=self.request.user)

    @resource_permission('user.session.view')
    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)

    @resource_permission('user.session.manage')
    def delete(self, request, *args, **kwargs):
        return self.destroy(request, *args, **kwargs)

    def perform_destroy(self, instance):
        self.request.session.delete(instance.session_key)
        instance.delete()
