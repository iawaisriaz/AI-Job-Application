from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_decode
from .models import Profile
from django.contrib.auth.decorators import login_required
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
# Create your views here.

def signup(request):

    if request.method == "POST":

        first_name = request.POST.get("first_name", "").strip()
        last_name = request.POST.get("last_name", "").strip()
        email = request.POST.get("email", "").strip().lower()
        password = request.POST.get("password", "")
        confirm_password = request.POST.get("confirm_password", "")

        # Password match check
        if password != confirm_password:
            messages.error(request, "Passwords do not match.")
            return render(request, "accounts/signup.html")

        # Email already exists check
        if User.objects.filter(email=email).exists():
            messages.error(
                request,
                "An account with this email already exists."
            )
            return render(request, "accounts/signup.html")

        # Create user This is Important
        user = User.objects.create_user(
            username=email,
            first_name=first_name,
            last_name=last_name,
            email=email,
            password=password
        )

        messages.success(
            request,
            "Your account has been created successfully."
        )

        return redirect("login")

    return render(request, "accounts/signup.html")


def user_login(request):

    if request.method == "POST":

        email = request.POST.get("email", "").strip().lower()
        password = request.POST.get("password", "")

        # Check if email is registered
        if not User.objects.filter(email=email).exists():

            messages.error(
                request,
                "Email is not registered."
            )

            return render(request, "accounts/login.html")


        # Check email + password
        user = authenticate(
            request,
            username=email,
            password=password
        )


        # Password is incorrect
        if user is None:

            messages.error(
                request,
                "Password is not correct."
            )

            return render(request, "accounts/login.html")


        # Login successful
        login(request, user)

        return redirect("dashboard")


    return render(request, "accounts/login.html")




def forgot_password(request):

    if request.method == "POST":

        email = request.POST.get("email")

        # Check if email exists
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            messages.error(request, "Email is not registered.")
            return render(request, "accounts/forgot_password.html")


        # Generate reset token
        token = default_token_generator.make_token(user)

        # Encode user ID
        uid = urlsafe_base64_encode(force_bytes(user.pk))


        # Create reset link
        reset_link = (
            request.build_absolute_uri(
                f"/reset-password/{uid}/{token}/"
            )
        )


        # Send email
        subject = "Reset Your Password"

        message = f"""
Hello {user.username},

You requested to reset your password.

Click the link below to create a new password:

{reset_link}

If you did not request this password reset, you can safely ignore this email.

Thanks,
AI Job Application Assistant
"""


        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=False,
        )


        messages.success(
            request,
            "Password reset link has been sent to your email."
        )

        return render(request, "accounts/forgot_password.html")


    return render(request, "accounts/forgot_password.html")



def reset_password(request, uidb64, token):

    # Decode user ID
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = User.objects.get(pk=uid)

    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        messages.error(request, "Invalid password reset link.")
        return redirect("forgot_password")


    # Check whether token is valid
    if not default_token_generator.check_token(user, token):
        messages.error(request, "This password reset link is invalid or has expired.")
        return redirect("forgot_password")


    # Handle password form
    if request.method == "POST":

        new_password = request.POST.get("new_password")
        confirm_password = request.POST.get("confirm_password")


        # Check passwords match
        if new_password != confirm_password:
            messages.error(request, "Passwords do not match.")
            return render(request, "accounts/reset_password.html")


        # Check password length
        if len(new_password) < 8:
            messages.error(
                request,
                "Password must be at least 8 characters long."
            )
            return render(request, "accounts/reset_password.html")


        # Set new password
        user.set_password(new_password)
        user.save()


        messages.success(
            request,
            "Your password has been reset successfully. Please login."
        )

        return redirect("login")


    return render(request, "accounts/reset_password.html")


@login_required
def profile(request):

    # Get existing profile or create one automatically
    profile, created = Profile.objects.get_or_create(
        user=request.user
    )

    # ==========================================
    # POST REQUEST
    # ==========================================

    if request.method == "POST":

        action = request.POST.get("action")


        # ==========================================
        # UPDATE PROFILE
        # ==========================================

        if action == "update_profile":

            first_name = request.POST.get(
                "first_name",
                ""
            ).strip()

            last_name = request.POST.get(
                "last_name",
                ""
            ).strip()


            # Update existing auth_user
            request.user.first_name = first_name
            request.user.last_name = last_name


            # ======================================
            # PROFILE PICTURE
            # ======================================

            if request.FILES.get("profile_picture"):

                # Delete old picture
                if profile.profile_picture:

                    profile.profile_picture.delete(
                        save=False
                    )

                # Save new picture
                profile.profile_picture = (
                    request.FILES["profile_picture"]
                )


            # Save changes
            request.user.save()
            profile.save()


            messages.success(
                request,
                "Profile updated successfully."
            )

            return redirect("profile")


        # ==========================================
        # CHANGE PASSWORD
        # ==========================================

        elif action == "change_password":

            current_password = request.POST.get(
                "current_password",
                ""
            )

            new_password = request.POST.get(
                "new_password",
                ""
            )

            confirm_password = request.POST.get(
                "confirm_password",
                ""
            )


            # ======================================
            # CURRENT PASSWORD CHECK
            # ======================================

            if not request.user.check_password(
                current_password
            ):

                messages.error(
                    request,
                    "Current password is incorrect."
                )

                return redirect("profile")


            # ======================================
            # NEW PASSWORD MATCH CHECK
            # ======================================

            if new_password != confirm_password:

                messages.error(
                    request,
                    "New password and confirm password do not match."
                )

                return redirect("profile")


            # ======================================
            # EMPTY PASSWORD CHECK
            # ======================================

            if not new_password:

                messages.error(
                    request,
                    "New password cannot be empty."
                )

                return redirect("profile")


            # ======================================
            # DJANGO PASSWORD VALIDATION
            # ======================================

            try:

                validate_password(
                    new_password,
                    request.user
                )

            except ValidationError as error:

                for error_message in error.messages:

                    messages.error(
                        request,
                        error_message
                    )

                return redirect("profile")


            # ======================================
            # SET NEW PASSWORD
            # ======================================

            request.user.set_password(
                new_password
            )

            request.user.save()


            # Keep user logged in
            update_session_auth_hash(
                request,
                request.user
            )


            messages.success(
                request,
                "Password changed successfully."
            )

            return redirect("profile")


        # ==========================================
        # DELETE ACCOUNT
        # ==========================================

        elif action == "delete_account":

            user = request.user


            # ======================================
            # DELETE PROFILE PICTURE
            # ======================================

            if profile.profile_picture:

                profile.profile_picture.delete(
                    save=False
                )


            # ======================================
            # DELETE PROFILE
            # ======================================

            profile.delete()


            # ======================================
            # DELETE USER FROM auth_user
            # ======================================

            user.delete()


            # ======================================
            # GO TO LANDING PAGE
            # ======================================

            return redirect("landing_page")


    # ==========================================
    # GET REQUEST
    # ==========================================

    return render(
        request,
        "accounts/profile.html",
        {
            "profile": profile
        }
    )