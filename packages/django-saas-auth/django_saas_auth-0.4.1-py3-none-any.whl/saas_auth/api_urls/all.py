from django.urls import include, path

urlpatterns = [
    path('sessions/', include('saas_auth.api_urls.session')),
    path('tokens/', include('saas_auth.api_urls.token')),
]
