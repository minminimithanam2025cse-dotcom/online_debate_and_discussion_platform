from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

from debates import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('django.contrib.auth.urls')),
    path('', include('debates.urls')),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

handler404 = views.custom_404
handler500 = views.custom_500
