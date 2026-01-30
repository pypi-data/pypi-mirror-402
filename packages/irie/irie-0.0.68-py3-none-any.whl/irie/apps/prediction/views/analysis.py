import os
from uuid import uuid4
import time

from django_tables2 import RequestConfig
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render
from django.http import JsonResponse
from django.views.generic import ListView
from django_filters.views import FilterView
from django_filters.views import FilterView
from django.shortcuts import redirect
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.http import Http404
from django.views import View
from django.views import View
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string

from irie.apps.prediction.models import AnalysisJob

# POST endpoint to create analysis job
def analyze_bundles(request):
    if request.method == "POST":
        bundle_ids = request.POST.getlist("bundle_ids")
        job = AnalysisJob.objects.create()
        job.bundles.set(Bundle.objects.filter(id__in=bundle_ids))
        job.save()
        return redirect("bundle_analysis_status", job_id=job.job_id)
    raise Http404()


class BundleAnalysisStatusView(View):
    def get(self, request, job_id):
        job = get_object_or_404(AnalysisJob, job_id=job_id)

        if job.status == "pending":
            job.run()
            return redirect("bundle_analysis_result", job_id=job_id)

        elif job.status == "done":
            return redirect("bundle_analysis_result", job_id=job_id)

        elif job.status == "failed":
            return render(request, "app/analyze_results.html", {"results": job.results, "job": job})

        return render(request, "app/analysis_status.html", {"job_id": job_id})

# Final result display
def bundle_analysis_result(request, job_id):
    job = get_object_or_404(AnalysisJob, job_id=job_id)
    return render(request, "app/analyze_results.html", {"results": job.results, "job": job})



class BundleAnalysisPollView(View):
    def get(self, request, job_id):
        job = get_object_or_404(AnalysisJob, job_id=job_id)
        html = render_to_string("app/_results_fragment.html", {"results": job.results or []})
        return JsonResponse({"html": html, "status": job.status})
