import os

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from .models import JobAnalysis
from cvs.models import CV

from ml.predictor import predict_match


# ============================================================
# NEW ANALYSIS
# STEP 1
# ============================================================

@login_required
def new_analysis(request):
    if request.method == "POST":
        company_name = request.POST.get("company_name", "").strip()
        job_title = request.POST.get("job_title", "").strip()
        job_description = request.POST.get("job_description", "").strip()

        if not company_name:
            messages.error(request, "Please enter the company name.")
            return render(request, "analysis/new_analysis.html")

        if not job_title:
            messages.error(request, "Please enter the job title.")
            return render(request, "analysis/new_analysis.html")

        if not job_description:
            messages.error(request, "Please enter the job description.")
            return render(request, "analysis/new_analysis.html")

        analysis = JobAnalysis.objects.create(
            user=request.user,
            company_name=company_name,
            job_title=job_title,
            job_description=job_description,
            status="draft",
        )

        return redirect("select_cv", analysis_id=analysis.id)

    return render(request, "analysis/new_analysis.html")


# ============================================================
# SELECT CV
# STEP 2
# ============================================================

@login_required
def select_cv(request, analysis_id):
    analysis = get_object_or_404(
        JobAnalysis,
        id=analysis_id,
        user=request.user,
    )

    cvs = CV.objects.filter(
        user_id=request.user.id
    ).order_by("-uploaded_at")

    if request.method == "POST":
        cv_id = request.POST.get("cv_id")

        if not cv_id:
            messages.error(request, "Please select a CV first.")
            return redirect("select_cv", analysis_id=analysis.id)

        cv = get_object_or_404(
            CV,
            id=cv_id,
            user_id=request.user.id,
        )

        analysis.cv = cv
        analysis.status = "draft"
        analysis.save(
            update_fields=["cv", "status", "updated_at"]
        )

        return redirect(
            "analysis_loading",
            analysis_id=analysis.id,
        )

    return render(
        request,
        "analysis/select_cv.html",
        {
            "cvs": cvs,
            "analysis": analysis,
        },
    )


# ============================================================
# STEP 3
# ANALYSIS LOADING PAGE
# ============================================================

@login_required
def analysis_loading(request, analysis_id):
    analysis = get_object_or_404(
        JobAnalysis,
        id=analysis_id,
        user=request.user,
    )

    if not analysis.cv:
        messages.error(request, "Please select a CV first.")
        return redirect(
            "select_cv",
            analysis_id=analysis.id,
        )

    return render(
        request,
        "analysis/analysis_loading.html",
        {"analysis": analysis},
    )


# ============================================================
# EXTRACT TEXT FROM CV
# ============================================================

def extract_cv_text(cv):
    """
    Reads PDF / DOCX / TXT CV files.
    Automatically detects the FileField on the CV model.
    """

    file_field = None

    for field in cv._meta.fields:
        if field.get_internal_type() == "FileField":
            file_field = field
            break

    if not file_field:
        raise ValueError("No FileField found on the CV model.")

    uploaded_file = getattr(cv, file_field.name)

    if not uploaded_file:
        raise ValueError("The selected CV does not contain a file.")

    filename = uploaded_file.name.lower()
    uploaded_file.open("rb")

    try:
        if filename.endswith(".pdf"):
            from pypdf import PdfReader

            reader = PdfReader(uploaded_file)
            pages = []

            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    pages.append(page_text)

            return "\n".join(pages)

        if filename.endswith(".docx"):
            from docx import Document

            document = Document(uploaded_file)

            paragraphs = [
                paragraph.text.strip()
                for paragraph in document.paragraphs
                if paragraph.text.strip()
            ]

            return "\n".join(paragraphs)

        if filename.endswith(".txt"):
            return uploaded_file.read().decode(
                "utf-8",
                errors="ignore",
            )

        raise ValueError(
            "Unsupported CV format. Please use PDF, DOCX or TXT."
        )

    finally:
        uploaded_file.close()


# ============================================================
# STEP 3
# LOCAL ML ANALYSIS
# ============================================================

@login_required
@require_POST
def run_analysis(request, analysis_id):
    analysis = get_object_or_404(
        JobAnalysis,
        id=analysis_id,
        user=request.user,
    )

    if not analysis.cv:
        return JsonResponse(
            {
                "success": False,
                "error": "No CV selected.",
            },
            status=400,
        )

    try:
        analysis.status = "processing"
        analysis.error_message = ""
        analysis.save(
            update_fields=[
                "status",
                "error_message",
                "updated_at",
            ]
        )

        # 1. Extract CV text locally.
        cv_text = extract_cv_text(analysis.cv)

        if not cv_text.strip():
            raise ValueError(
                "Could not extract any text from the CV."
            )

        # 2. Run the local NLP + XGBoost pipeline.
        result = predict_match(
            cv_text=cv_text,
            job_text=analysis.job_description,
        )

        # 3. Validate the prediction.
        match_score = int(
            max(0, min(100, result.get("match_score", 0)))
        )

        matched_skills = result.get("matched_skills", [])
        missing_skills = result.get("missing_skills", [])
        strengths = result.get("strengths", [])
        weak_areas = result.get("weak_areas", [])

        analysis.match_score = match_score
        analysis.match_label = str(
            result.get("match_label", "Match")
        )

        analysis.matched_skills = (
            matched_skills if isinstance(matched_skills, list) else []
        )
        analysis.missing_skills = (
            missing_skills if isinstance(missing_skills, list) else []
        )
        analysis.strengths = (
            strengths if isinstance(strengths, list) else []
        )
        analysis.weak_areas = (
            weak_areas if isinstance(weak_areas, list) else []
        )

        analysis.detailed_analysis = str(
            result.get("detailed_analysis", "")
        )

        analysis.status = "completed"
        analysis.save()

        return JsonResponse(
            {
                "success": True,
                "redirect_url": reverse(
                    "result_analysis",
                    kwargs={"analysis_id": analysis.id},
                ),
            }
        )

    except Exception as e:
        analysis.status = "failed"
        analysis.error_message = str(e)

        analysis.save(
            update_fields=[
                "status",
                "error_message",
                "updated_at",
            ]
        )

        return JsonResponse(
            {
                "success": False,
                "error": str(e),
            },
            status=500,
        )


# ============================================================
# STEP 4
# RESULTS
# ============================================================

@login_required
def result_analysis(request, analysis_id):
    analysis = get_object_or_404(
        JobAnalysis,
        id=analysis_id,
        user=request.user,
    )

    if analysis.status != "completed":
        if analysis.status in ["draft", "processing"]:
            return redirect(
                "analysis_loading",
                analysis_id=analysis.id,
            )

        messages.error(
            request,
            "The analysis could not be completed.",
        )

        return redirect(
            "select_cv",
            analysis_id=analysis.id,
        )

    total_skills = (
        len(analysis.matched_skills)
        + len(analysis.missing_skills)
    )

    score = analysis.match_score
    circumference = 314

    dashoffset = (
        circumference
        - (circumference * score / 100)
    )

    return render(
        request,
        "analysis/result_analysis.html",
        {
            "analysis": analysis,
            "match_score": score,
            "match_label": analysis.match_label or "Match",
            "matched_skills": analysis.matched_skills,
            "missing_skills": analysis.missing_skills,
            "strengths": analysis.strengths,
            "weak_areas": analysis.weak_areas,
            "detailed_analysis": analysis.detailed_analysis,
            "matched_count": len(analysis.matched_skills),
            "missing_count": len(analysis.missing_skills),
            "total_skill_count": total_skills,
            "score_dashoffset": round(dashoffset, 2),
        },
    )
