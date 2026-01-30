#===----------------------------------------------------------------------===#
#
#         STAIRLab -- STructural Artificial Intelligence Laboratory
#
#===----------------------------------------------------------------------===#
#
#   Author: Claudio Perez
#
#----------------------------------------------------------------------------#
import rest_framework_simplejwt.views as jwt_views

from django.urls import path
from django.conf.urls.static import static

from . import views_events, views


urlpatterns = [
    path("event-table/",     views.asset_table, name="event_table"),
    # path("event-table/",     views.record_table, name="event_table"),
    path("event-table.html", views.record_table),
    path("event/(?P<anssid>[0-9 A-Z-]*)/", views.event_summary, name="event_profile"),

    path("events/", views_events.index),
    path('api/token/', jwt_views.TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', jwt_views.TokenRefreshView.as_view(), name='token_refresh'),
    path('api/events/', views_events.events),
    path('api/events/<int:event_id>/', views_events.event),
]
#+ static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

