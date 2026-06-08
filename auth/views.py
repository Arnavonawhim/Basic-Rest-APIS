import logging
from django.conf import settings
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.exceptions import ValidationError as DRFValidationError
from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiExample, OpenApiTypes
from rest_framework_simplejwt.tokens import RefreshToken
from auth import serializers

# Create your views here.

User = get_user_model()
logger = logging.getLogger("account")

def _get_tokens_for_user(user) -> dict:
    refresh = RefreshToken.for_user(user)
    return {"access": str(refresh.access_token),
            "refresh": str(refresh),}

_ERROR_400 = OpenApiResponse(response=OpenApiTypes.OBJECT,description="Validation error or bad request",
                             examples=[OpenApiExample("Validation Error",value={"status": "error", 
                                                                                "message": "...", "errors": {"field": ["detail"]}},)],)


_ERROR_429 = OpenApiResponse(response=OpenApiTypes.OBJECT,description="Rate limit exceeded or account locked",
                             examples=[OpenApiExample("Rate Limited",value={"status": "error", 
                                                                            "message": "Account locked."},)],)

class UserRegistrationView(APIView):
    @extend_schema(request=serializers.UserRegistrationSerializer,
                   responses={200: OpenApiResponse(response=OpenApiTypes.OBJECT,description="Registration Completed",
                                                   examples=[OpenApiExample("Success", value={"status": "success",
                                                                                              "message": "Registration Is Completed User added to database",
                                                                                              "data": {"Username": "example_username", "Email": "example@gmail.com"},},)],),
            400: _ERROR_400,
            429: _ERROR_429,},
        tags=["Authentication"],
        summary="Register",
        description=("Call `/login next"),)
    
    def post(self, request):
        serializer = serializers.UserRegistrationSerializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
        except DRFValidationError:
            raise
        Email = serializer.validated_data["email"]
        Username = serializer.validated_data["username"]
        Password = serializer.validated_data["password"]
        if User.objects.filter(email=Email, is_email_verified=True).exists():
            return Response({"status": "error", "message": "An account with this email already exists.",
                             "errors": {"email": ["This email is already registered."]}},
                             status=status.HTTP_400_BAD_REQUEST,)
        if User.objects.filter(username=Username).exists():
            return Response({"status": "error", "message": "This username is already taken.",
                             "errors": {"username": ["This username is already taken."]}},
                             status=status.HTTP_400_BAD_REQUEST,)
        user = User.objects.create_user(username=Username,password=Password,email=Email)
        user.save()
        tokens = _get_tokens_for_user(user)
        logger.info("Account created for %s (@%s)", user.email, user.username)
        return Response({"status": "success",
                "message": "Registration Completed.",
                "data": {"Username": f"{Username}", "email": f"{Email}"}},
                status=status.HTTP_200_OK,)

class UserLoginView(APIView):
    @extend_schema(request=serializers.UserLoginSerializer,
                   responses={200: OpenApiResponse(response=OpenApiTypes.OBJECT,description="Login successful",
                                                   examples=[OpenApiExample("Success",value={"status": "success",
                                                          "message": "Login successful.",
                                                          "data": {"user": {"id": 1, "email": "example@gmail.com", "username": "example_user"},
                                                                   "tokens": {"access": "eyJ...", "refresh": "eyJ..."},},},)],),
            400: _ERROR_400,
            429: _ERROR_429,},
        tags=["Authentication"],
        summary="Login",
        description="Authenticate with email or username + password.",)
    def post(self, request):
        serializer = serializers.UserLoginSerializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
        except DRFValidationError:
            raise
        identifier = serializer.validated_data["identifier"]
        password = serializer.validated_data["password"]
        try:
            if "@" in identifier:
                user = User.objects.get(email=identifier)
            else:
                user = User.objects.get(username=identifier)
        except User.DoesNotExist:
            return Response({"status": "error", "message": "Invalid credentials.",
                             "errors": {"identifier": ["No account found with these credentials."]}},
                             status=status.HTTP_400_BAD_REQUEST,)
        if not user.check_password(password):
            return Response(
                {"status": "error", "message": f"Invalid credentials.",
                 "errors": {"password": ["Incorrect password."]}},
                status=status.HTTP_400_BAD_REQUEST,)
        tokens = _get_tokens_for_user(user)
        logger.info("User logged in: %s", user.email)
        return Response({"status": "success",
                         "message": "Login successful.",
                         "data": {"user": {"id": user.id, "email": user.email, "username": user.username},},},
                         status=status.HTTP_200_OK,)