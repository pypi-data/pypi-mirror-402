from django.urls import path

from ..endpoints.sessions import SessionRecordItemEndpoint, SessionRecordListEndpoint

urlpatterns = [
    path('', SessionRecordListEndpoint.as_view()),
    path('<pk>/', SessionRecordItemEndpoint.as_view()),
]
