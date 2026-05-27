from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from apps.dashboard.views import stats

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/', include('apps.accounts.urls')),
    path('api/', include('apps.projects.urls')),
    path('api/', include('apps.testcases.urls')),
    path('api/', include('apps.testplans.urls')),
    path('api/', include('apps.testruns.urls')),
    path('api/', include('apps.defects.urls')),
    path('api/dashboard/stats/', stats, name='dashboard_stats'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
