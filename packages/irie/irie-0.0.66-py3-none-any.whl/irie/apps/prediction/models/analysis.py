
import yaml
import uuid
from pathlib import Path

from django.db import models
from concurrent.futures import ThreadPoolExecutor, as_completed
import os

class AnalysisJob(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("running", "Running"),
        ("done",    "Done"),
        ("failed",  "Failed"),
    ]

    job_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    created = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="pending")
    bundles = models.ManyToManyField("Bundle")
    results = models.JSONField(blank=True, null=True)

    def __str__(self):
        return f"Analysis {self.job_id} ({self.status})"


    def run(self):
        import os

        self.status = "running"
        self.save()

        collected = []
        try:
            result = TestCase(script.path).run()
            status = result.get("status", "ok")
        except Exception as e:
            self.status = "failed"
            self.results = [{"error": str(e)}]

        collected.append({
            "bundle": bundle.key,
            "script": os.path.basename(script.path),
            "result": status
        })
        self.results = collected
        self.save()

        self.status = "done"
        self.results = collected

        self.save()
