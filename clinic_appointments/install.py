import frappe
import logging

from clinic_appointments.setup.runner import setup_all
from clinic_appointments.utils.setup_utils import (
    ensure_module_def,
    MODULE_DEF_NAME,
    APP_PY_MODULE,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------
# Utilities
# ---------------------------------------------------------
def _ensure_module():
    """Ensure Module Def exists"""
    ensure_module_def(MODULE_DEF_NAME, APP_PY_MODULE)


def _clear_cache():
    frappe.clear_cache()


# ---------------------------------------------------------
# Lifecycle Hooks
# ---------------------------------------------------------

def before_install():
    logger.info("===== Clinic Appointments: Before Install =====")
    _clear_cache()


def after_install():
    logger.info("===== Clinic Appointments: After Install Started =====")

    try:
        _ensure_module()

        # 🔥 Run full setup
        setup_all()

        _clear_cache()
        frappe.db.commit()

        logger.info("===== Clinic Appointments: After Install Completed =====")

    except Exception as e:
        frappe.db.rollback()
        logger.error(f"❌ Install failed: {e}")
        raise


def after_migrate():
    logger.info("===== Clinic Appointments: After Migrate Started =====")

    try:
        _ensure_module()

        # 🔁 Safe re-run
        setup_all()

        _clear_cache()
        frappe.db.commit()

        logger.info("===== Clinic Appointments: After Migrate Completed =====")

    except Exception as e:
        frappe.db.rollback()
        logger.error(f"❌ Migrate failed: {e}")
        raise