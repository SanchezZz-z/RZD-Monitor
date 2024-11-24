"""Import all routers and add them to routers_list."""
from .admin import admin_router
from .echo import echo_router
from .simple_menu import menu_router
from .user import user_router
from .train_menu import train_menu_router
from .monitor_menu import monitor_menu_router
# from .check_free_seats_menu import free_seats_menu_router

routers_list = [
    admin_router,
    menu_router,
    user_router,
    train_menu_router,
    monitor_menu_router,
    # free_seats_menu_router,
    echo_router,  # echo_router must be last
]

__all__ = [
    "routers_list",
]
