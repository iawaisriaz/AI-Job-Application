
from django.contrib.auth.decorators import login_required
from django.db.models import Avg
from django.shortcuts import render

from analysis.models import JobAnalysis


@login_required
def dashboard(request):

    # Only the logged-in user's completed analyses
    analyses = JobAnalysis.objects.filter(
        user=request.user,
        status="completed"
    )

    # Total completed analyses
    total_analyses = analyses.count()

    # Most recent completed analysis
    latest_analysis = analyses.order_by(
        "-created_at"
    ).first()

    # Average match score
    average_match = analyses.aggregate(
        average=Avg("match_score")
    )["average"]

    # Five most recent analyses
    recent_analyses = analyses.order_by(
        "-created_at"
    )[:5]

    context = {
        "total_analyses": total_analyses,
        "latest_analysis": latest_analysis,
        "average_match": average_match,
        "recent_analyses": recent_analyses,
    }

    return render(
        request,
        "dashboard/dashboard.html",
        context
    )
