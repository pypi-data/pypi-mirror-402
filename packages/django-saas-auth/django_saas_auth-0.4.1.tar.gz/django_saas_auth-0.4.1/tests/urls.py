from django.urls import include, path

urlpatterns = [
    path('api/user/', include('saas_auth.api_urls.all')),
]
