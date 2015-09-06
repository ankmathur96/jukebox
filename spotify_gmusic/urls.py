from django.conf.urls import url

from . import views

urlpatterns = [
				url(r'^$', views.index, name='index'),
				url(r'^authenticate/', views.authenticate, name='authenticate'),
				url(r'^auth_result/', views.process, name='process'),
				]