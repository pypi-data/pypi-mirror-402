from ..base import ImmichBaseClient

class JobsMixin(ImmichBaseClient):
    """
    Mixin for Jobs related endpoints.
    """
    def list_jobs(self):
        """Get all jobs status"""
        return self.get("jobs")

    def run_job(self, job_id, command, force=False):
        """Send a command to a job (start, stop, etc.)"""
        return self.put(f"jobs/{job_id}", json={"command": command, "force": force})
