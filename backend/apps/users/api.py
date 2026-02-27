from django.contrib.auth import authenticate, login

from ninja import Router

from apps.users.models import User, TrustedSender
from apps.users.schemas import (
    LoginIn,
    RegistrationIn,
    RegistrationOut,
    TrustedSenderIn,
    TrustedSenderOut,
    UserMeOut,
    UserMePatchIn,
)
from apps.users.services import generate_forwarding_address

router = Router(tags=["users"])


def _user_me_out(user: User) -> UserMeOut:
    return UserMeOut(
        id=str(user.id),
        email=user.email,
        forwarding_address=user.forwarding_address,
        full_name=user.full_name,
        target_role=user.target_role,
        onboarding_completed=user.onboarding_completed,
    )


@router.post("register", response={201: RegistrationOut, 400: dict})
def register(request, payload: RegistrationIn):
    """Register with email and password. Forwarding address generated if omitted (ONB-01)."""
    email = payload.email.strip().lower()
    if payload.forwarding_address is not None and payload.forwarding_address.strip():
        forwarding_address = payload.forwarding_address.strip().lower()
        if User.objects.filter(forwarding_address=forwarding_address).exists():
            return 400, {"detail": "This forwarding address is already in use."}
    else:
        forwarding_address = generate_forwarding_address()
    if User.objects.filter(email=email).exists():
        return 400, {"detail": "A user with this email already exists."}
    user = User.objects.create_user(
        email=email,
        forwarding_address=forwarding_address,
        password=payload.password,
        full_name=payload.full_name,
    )
    return 201, RegistrationOut(
        id=str(user.id),
        email=user.email,
        forwarding_address=user.forwarding_address,
    )


@router.post("login", response={200: UserMeOut, 401: dict})
def login_view(request, payload: LoginIn):
    """Log in with email and password. Uses Django session (cookie)."""
    email = payload.email.strip().lower()
    user = authenticate(request, username=email, password=payload.password)
    if user is None:
        return 401, {"detail": "Invalid email or password."}
    login(request, user)
    return 200, _user_me_out(user)


@router.get("/me", response={200: UserMeOut, 401: dict})
def me(request):
    """Current authenticated user."""
    if not request.user.is_authenticated:
        return 401, {"detail": "Authentication required"}
    return 200, _user_me_out(request.user)


@router.patch("/me", response={200: UserMeOut, 401: dict})
def patch_me(request, payload: UserMePatchIn):
    """Update current user (full_name, target_role, onboarding_completed)."""
    if not request.user.is_authenticated:
        return 401, {"detail": "Authentication required"}
    user = request.user
    if payload.full_name is not None:
        user.full_name = payload.full_name.strip() or None
    if payload.target_role is not None:
        user.target_role = payload.target_role.strip() or None
    if payload.onboarding_completed is not None:
        user.onboarding_completed = payload.onboarding_completed
    user.save()
    return 200, _user_me_out(user)


@router.get("trusted-senders", response={200: list[TrustedSenderOut], 401: dict})
def list_trusted_senders(request):
    """List trusted senders for the current user."""
    if not request.user.is_authenticated:
        return 401, {"detail": "Authentication required"}
    senders = TrustedSender.objects.filter(user=request.user)
    return 200, [
        TrustedSenderOut(
            id=str(s.id),
            sender_email=s.sender_email,
            label=s.label,
        )
        for s in senders
    ]


@router.post(
    "trusted-senders",
    response={201: TrustedSenderOut, 400: dict, 401: dict},
)
def add_trusted_sender(request, payload: TrustedSenderIn):
    """Add a trusted sender for email parsing."""
    if not request.user.is_authenticated:
        return 401, {"detail": "Authentication required"}
    email = payload.sender_email.strip().lower()
    if not email:
        return 400, {"detail": "Sender email is required."}
    if TrustedSender.objects.filter(user=request.user, sender_email=email).exists():
        return 400, {"detail": "This sender is already in your trusted list."}
    sender = TrustedSender.objects.create(
        user=request.user,
        sender_email=email,
        label=payload.label.strip() or None,
    )
    return 201, TrustedSenderOut(
        id=str(sender.id),
        sender_email=sender.sender_email,
        label=sender.label,
    )
