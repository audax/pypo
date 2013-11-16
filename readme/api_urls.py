from rest_framework import routers

from readme.api import GroupViewSet, UserViewSet, ItemViewSet

router = routers.DefaultRouter()
router.register(r'users', UserViewSet)
router.register(r'groups', GroupViewSet)
router.register(r'items', ItemViewSet)

urlpatterns = router.urls
