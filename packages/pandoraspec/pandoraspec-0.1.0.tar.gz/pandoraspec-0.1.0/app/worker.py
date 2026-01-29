from celery import Celery
import os

CELERY_BROKER_URL = os.environ.get("CELERY_BROKER_URL", "redis://localhost:6379/0")
CELERY_RESULT_BACKEND = os.environ.get("CELERY_RESULT_BACKEND", "redis://localhost:6379/0")

celery_app = Celery("pandoraspec", broker=CELERY_BROKER_URL, backend=CELERY_RESULT_BACKEND)
celery_app.conf.task_track_started = True

@celery_app.task(name="run_dora_audit")
def run_dora_audit(vendor_name: str, schema_url: str, api_key: str = None):
    from pandoraspec.core import AuditEngine
    from pandoraspec.reporting import generate_report
    
    engine = AuditEngine(schema_url=schema_url, api_key=api_key)
    audit_results = engine.run_full_audit()
    
    # Generate report
    report_path = generate_report(vendor_name, audit_results)
    
    return {
        "vendor_name": vendor_name,
        "status": "completed",
        "report_path": report_path,
        "results_summary": {
            "drift": {
                "passed": len([r for r in audit_results["drift_check"] if r.get("status") == "PASS"]),
                "failed": len([r for r in audit_results["drift_check"] if r.get("status") != "PASS"])
            },
            "resilience": {
                 "passed": len([r for r in audit_results["resilience"] if r.get("status") == "PASS"]),
                 "failed": len([r for r in audit_results["resilience"] if r.get("status") != "PASS"])
            },
            "security": {
                 "passed": len([r for r in audit_results["security"] if r.get("status") == "PASS"]),
                 "failed": len([r for r in audit_results["security"] if r.get("status") != "PASS"])
            }
        }
    }
