from django.urls import path
from apps.user.views import RegisterView, ActiveView, LoginView, LogoutView, \
    UserInfoView, UserAddressView, UserOrderView

urlpatterns = [
    path("register/", RegisterView.as_view(), name="register"),
    path("active/<str:token>", ActiveView.as_view(), name="active"),
    path("login/", LoginView.as_view(), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),

    path("", UserInfoView.as_view(), name="user"),
    path("address/", UserAddressView.as_view(), name="address"),
    path("order/", UserOrderView.as_view(), name="order"),
]
