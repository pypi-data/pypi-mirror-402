from django.urls import path

from ..endpoints.tokens import UserTokenItemEndpoint, UserTokenListEndpoint

urlpatterns = [
    path('', UserTokenListEndpoint.as_view()),
    path('<pk>/', UserTokenItemEndpoint.as_view()),
]
