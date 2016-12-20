"""coms_clone_backend URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.10/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url, include
from rest_framework import routers
from rest_framework.authtoken.views import obtain_auth_token
from rest_framework_nested import routers as nested_routers

from qualifications.views import QualificationViewSet
from clubs.views import ClubViewSet, RegionViewSet
from courses.views import CourseViewSet
from users.views import UserViewSet

router = routers.DefaultRouter()
router.register(r'users', UserViewSet, base_name='user')
router.register(r'clubs', ClubViewSet, base_name='club')
router.register(r'courses', CourseViewSet, base_name='course')
router.register(r'regions', RegionViewSet, base_name='region')

users_router = nested_routers.NestedSimpleRouter(router, r'users', lookup='user')
users_router.register(r'qualifications', QualificationViewSet, base_name='user-qualifications')

urlpatterns = [
        #url(r'^auth/', include('rest_framework.urls', namespace='rest_framework')),
        url(r'^auth/login/', obtain_auth_token), # Respond to username/password pairs with auth tokens
        url(r'^', include(router.urls)), # All other URLs are passed to the default router
        url(r'^', include(users_router.urls)),
]
