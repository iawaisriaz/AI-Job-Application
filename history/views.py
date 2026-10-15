
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from analysis.models import JobAnalysis


# ==========================================
# ANALYSIS HISTORY
# ==========================================

@login_required
def history_list(request):

    analyses = (
        JobAnalysis.objects
        .filter(
            user=request.user,
            status="completed"
        )
        .select_related("cv")
        .order_by("-created_at")
    )

    paginator = Paginator(analyses, 10)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = {
        "analyses": page_obj,
        "page_obj": page_obj,
        "total_analyses": paginator.count,
    }

    return render(
        request,
        "history/history.html",
        context
    )


# ==========================================
# DELETE ANALYSIS
# ==========================================

@login_required
@require_POST
def delete_analysis(request, analysis_id):

    analysis = get_object_or_404(
        JobAnalysis,
        id=analysis_id,
        user=request.user,
        status="completed"
    )

    analysis.delete()

    messages.success(
        request,
        "Analysis deleted successfully."
    )

    return redirect("history")
