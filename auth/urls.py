from django.urls import path,include
from auth import views

app_name = "authentication"

urlpatterns = [
    path("register/", views.UserRegistrationView.as_view(), name="register"),
    path("login/", views.UserLoginView.as_view(), name="login" ),
]