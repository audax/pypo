from rest_framework import routers

from readme.api import ItemViewSet

router = routers.DefaultRouter()
router.register(r'items', ItemViewSet)

urlpatterns = router.urls
