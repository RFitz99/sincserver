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
from django.contrib import admin
from rest_framework import routers
from rest_framework.authtoken.views import obtain_auth_token
from rest_framework_nested import routers as nested_routers

from qualifications.views import QualificationViewSet
from clubs.views import ClubViewSet, RegionViewSet
from courses.views import CertificateViewSet, CourseViewSet, CourseEnrolmentViewSet, CourseInstructionViewSet
from users.views import UserViewSet

admin.autodiscover()

router = routers.DefaultRouter()
router.register(r'users', UserViewSet, base_name='user')
router.register(r'certificates', CertificateViewSet, base_name='certificate')
router.register(r'qualifications', QualificationViewSet, base_name='qualification')
router.register(r'clubs', ClubViewSet, base_name='club')
router.register(r'courses', CourseViewSet, base_name='course')
router.register(r'regions', RegionViewSet, base_name='region')
router.register(r'courseenrolments', CourseEnrolmentViewSet, base_name='courseenrolment')

clubs_router = nested_routers.NestedSimpleRouter(router, r'clubs', lookup='club')
clubs_router.register(r'users', UserViewSet, base_name='club-users')

courses_router = nested_routers.NestedSimpleRouter(router, r'courses', lookup='course')
courses_router.register(r'enrolments', CourseEnrolmentViewSet, base_name='course-enrolment')
courses_router.register(r'instructions', CourseInstructionViewSet, base_name='course-instruction')

users_router = nested_routers.NestedSimpleRouter(router, r'users', lookup='user')
users_router.register(r'qualifications', QualificationViewSet, base_name='user-qualification')
users_router.register(r'courses-organized', CourseViewSet, base_name='user-courses-organized')
users_router.register(r'courses-taught', CourseInstructionViewSet, base_name='user-course-instruction')

regions_router = nested_routers.NestedSimpleRouter(router, r'regions', lookup='region')
regions_router.register(r'courses', CourseViewSet, base_name='region-course')

urlpatterns = [
    url(r'^admin/', admin.site.urls),
    #url(r'^auth/', include('rest_framework.urls', namespace='rest_framework')),
    url(r'^auth/login/', obtain_auth_token), # Respond to username/password pairs with auth tokens
    url(r'^', include(router.urls)), # All other URLs are passed to the default router
    url(r'^', include(users_router.urls)),
    url(r'^', include(clubs_router.urls)),
    url(r'^', include(regions_router.urls)),
    url(r'^', include(courses_router.urls)),
]
