from netbox.api.routers import NetBoxRouter

from .views import (
    NetBoxLoadBalancerRootView,
    LBServiceViewSet,
    LBServiceAssignmentViewSet,
    PoolViewSet,
    PoolAssignmentViewSet,
    ListenerViewSet,
    HealthMonitorViewSet,
    HealthMonitorAssignmentViewSet,
    MemberViewSet,
    MemberAssignmentViewSet,
    VirtualIPPoolViewSet,
    VirtualIPPoolAssignmentViewSet,
    VirtualIPViewSet,
)

app_name = "netbox_load_balancing"

router = NetBoxRouter()
router.APIRootView = NetBoxLoadBalancerRootView
router.register("pools", PoolViewSet)
router.register("pool-assignments", PoolAssignmentViewSet)
router.register("members", MemberViewSet)
router.register("member-assignments", MemberAssignmentViewSet)
router.register("health-monitors", HealthMonitorViewSet)
router.register("health-monitor-assignments", HealthMonitorAssignmentViewSet)
router.register("services", LBServiceViewSet)
router.register("service-assignments", LBServiceAssignmentViewSet)
router.register("virtual-pools", VirtualIPPoolViewSet)
router.register("virtual-pool-assignments", VirtualIPPoolAssignmentViewSet)
router.register("virtual-addresses", VirtualIPViewSet)
router.register("listeners", ListenerViewSet)

urlpatterns = router.urls
