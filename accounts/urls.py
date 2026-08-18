from django.urls import path

from .views import MeView, RegisterView, UserDetailView, UserListView

urlpatterns = [
    path("register/", RegisterView.as_view(), name="register"),
    path("users/", UserListView.as_view(), name="user-list"),
    path("users/<int:pk>/", UserDetailView.as_view(), name="user-detail"),
    path("profile/", MeView.as_view(), name="profile"),
]
