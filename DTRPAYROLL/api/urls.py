from django.urls import path, include

urlpatterns = [
    path('accounts/', include('djoser.urls')),
    path('accounts/', include('djoser.urls.authtoken')),
]