from django.urls import path,include,re_path
from . import views
from django.conf import settings
from django.conf.urls.static import static
from django.views.static import serve

urlpatterns = [
      re_path(r"^media/(?P<path>.*)$", serve, {'document_root': settings.MEDIA_ROOT}),
    re_path(r"^static/(?P<path>.*)$", serve, {'document_root': settings.STATIC_ROOT}),


    path('financial/', views.payment_dashboard, name='financial'),  
    path('login_view/', views.login_view, name='login_view'),
    path('generate_invoice/<int:payment_id>/', views.generate_invoice, name='generate_invoice'),
    path('', views.home, name='home'),
        path('forgot-password/', views.forgot_password, name='forgot_password'),
path('reset-password/<uidb64>/<token>/', views.reset_password, name='reset_password'),
    path('profile/', views.profile, name='profile'),
    path('logout/', views.logout_view, name='logout'),
    path('raise_issue/', views.raiseIssue, name='raise_issue'),
] 
