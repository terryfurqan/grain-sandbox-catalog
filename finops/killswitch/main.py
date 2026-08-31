import base64
import json
import logging
import os
from googleapiclient import discovery
from google.auth import default

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("finops-killswitch")

def billing_killswitch(event, context):
    """
    Cloud Function yang dipicu oleh Google Cloud Billing Budget Alert via Pub/Sub.
    Secara otomatis mencabut izin akses publik ('allUsers') dari Cloud Run Service
    jika ambang batas biaya terlampaui.
    """
    if 'data' not in event:
        logger.warning("Event Pub/Sub tidak memiliki data payload.")
        return

    try:
        pubsub_message = base64.b64decode(event['data']).decode('utf-8')
        data = json.loads(pubsub_message)
    except Exception as e:
        logger.error(f"Gagal mem-parsing pesan Pub/Sub: {e}")
        return

    cost_amount = data.get("costAmount", 0.0)
    budget_amount = data.get("budgetAmount", 0.0)
    currency_code = data.get("currencyCode", "USD")

    logger.info(f"[FinOps] Status Biaya: {cost_amount} {currency_code} / Target Budget: {budget_amount} {currency_code}")

    # Cek apakah biaya sudah mencapai atau melebihi budget
    if budget_amount > 0 and cost_amount >= budget_amount:
        logger.critical(f"[KILL-SWITCH TRIGGERED] Biaya ({cost_amount}) melebihi budget ({budget_amount})!")
        
        project_id = os.environ.get("GCP_PROJECT") or os.environ.get("GOOGLE_CLOUD_PROJECT")
        region = os.environ.get("SERVICE_REGION", "asia-southeast2")
        service_name = os.environ.get("SERVICE_NAME", "grain-server")

        if not project_id:
            logger.error("GCP_PROJECT tidak terdeteksi di environment variable.")
            return

        credentials, _ = default()
        service = discovery.build('run', 'v1', credentials=credentials)
        resource = f"projects/{project_id}/locations/{region}/services/{service_name}"

        try:
            # Ambil IAM Policy Cloud Run saat ini
            policy = service.projects().locations().services().getIamPolicy(resource=resource).execute()

            # Hapus binding allUsers dari roles/run.invoker
            updated = False
            if 'bindings' in policy:
                new_bindings = []
                for binding in policy['bindings']:
                    if binding.get('role') == 'roles/run.invoker':
                        original_members = binding.get('members', [])
                        filtered_members = [m for m in original_members if m != 'allUsers']
                        if len(original_members) != len(filtered_members):
                            updated = True
                            binding['members'] = filtered_members
                    if binding.get('members'):
                        new_bindings.append(binding)
                policy['bindings'] = new_bindings

            if updated:
                service.projects().locations().services().setIamPolicy(
                    resource=resource,
                    body={'policy': policy}
                ).execute()
                logger.critical(f"[KILL-SWITCH SUCCESS] Akses publik ke {service_name} berhasil dimatikan di Edge!")
            else:
                logger.info("allUsers sudah tidak ada di IAM policy (sudah dimatikan sebelumnya).")

        except Exception as e:
            logger.error(f"Gagal memodifikasi IAM policy Cloud Run: {e}")
    else:
        logger.info("[FinOps] Penggunaan biaya masih dalam batas aman.")
