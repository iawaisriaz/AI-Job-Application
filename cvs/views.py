import os

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404, redirect, render

from .models import CV


# ==========================================================
# MY CVS PAGE
# ==========================================================

@login_required
def cv_page(request):

    cvs = CV.objects.filter(
        user=request.user
    ).order_by("-uploaded_at")

    context = {
        "cvs": cvs,
        "cv_count": cvs.count(),
    }

    return render(
        request,
        "cvs/cv.html",
        context
    )


# ==========================================================
# UPLOAD CV PAGE
# ==========================================================

@login_required
def upload_cv(request):

    if request.method == "POST":

        cv_name = request.POST.get(
            "cv_name",
            ""
        ).strip()

        cv_file = request.FILES.get(
            "cv_file"
        )


        # ------------------------------------------
        # CV NAME VALIDATION
        # ------------------------------------------

        if not cv_name:

            messages.error(
                request,
                "Please enter a name for your CV."
            )

            return redirect("upload_cv")


        # ------------------------------------------
        # FILE VALIDATION
        # ------------------------------------------

        if not cv_file:

            messages.error(
                request,
                "Please select a CV file."
            )

            return redirect("upload_cv")


        # ------------------------------------------
        # EXTENSION VALIDATION
        # ------------------------------------------

        allowed_extensions = [
            ".pdf",
            ".doc",
            ".docx",
        ]

        extension = os.path.splitext(
            cv_file.name
        )[1].lower()


        if extension not in allowed_extensions:

            messages.error(
                request,
                "Only PDF, DOC and DOCX files are allowed."
            )

            return redirect("upload_cv")


        # ------------------------------------------
        # FILE SIZE
        # Maximum 10 MB
        # ------------------------------------------

        max_size = 10 * 1024 * 1024

        if cv_file.size > max_size:

            messages.error(
                request,
                "CV file size must be less than 10 MB."
            )

            return redirect("upload_cv")


        # ------------------------------------------
        # SAVE CV
        # ------------------------------------------

        CV.objects.create(
            user=request.user,
            name=cv_name,
            file=cv_file
        )


        messages.success(
            request,
            "Your CV has been saved successfully."
        )


        # Upload ke baad My CVs page
        return redirect("cv")


    # ------------------------------------------
    # GET REQUEST
    # ------------------------------------------

    return render(
        request,
        "cvs/upload_cv.html"
    )

# ==========================================================
# DOWNLOAD CV
# ==========================================================

@login_required
def download_cv(request, cv_id):

    cv = get_object_or_404(
        CV,
        id=cv_id,
        user=request.user
    )


    if not cv.file:

        raise Http404(
            "CV file not found."
        )


    try:

        file_handle = cv.file.open("rb")

    except FileNotFoundError:

        raise Http404(
            "CV file not found."
        )


    extension = os.path.splitext(
        cv.file.name
    )[1].lower()


    if extension == ".pdf":

        content_type = "application/pdf"

    elif extension == ".doc":

        content_type = "application/msword"

    else:

        content_type = (
            "application/vnd.openxmlformats-officedocument."
            "wordprocessingml.document"
        )


    response = FileResponse(
        file_handle,
        content_type=content_type
    )


    filename = os.path.basename(
        cv.file.name
    )


    response["Content-Disposition"] = (
        f'attachment; filename="{filename}"'
    )


    return response


# ==========================================================
# DELETE CV
# ==========================================================

@login_required
def delete_cv(request, cv_id):

    if request.method != "POST":

        return redirect("cv")


    cv = get_object_or_404(
        CV,
        id=cv_id,
        user=request.user
    )


    # Delete physical file
    if cv.file:

        cv.file.delete(
            save=False
        )


    # Delete database record
    cv.delete()


    messages.success(
        request,
        "CV deleted successfully."
    )


    return redirect("cv")