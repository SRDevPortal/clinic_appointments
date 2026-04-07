app_name = "clinic_appointments"
app_title = "Clinic Appointments"
app_publisher = "Admin"
app_description = "Appointment control app integrated with patient encounter workflow"
app_email = "admin@example.com"
app_license = "MIT"

# ----------------------------------------
# APP INCLUDE (Global JS/CSS)
# ----------------------------------------

app_include_js = [
    "/assets/clinic_appointments/js/clinic_appointment.js",
    # "/assets/clinic_appointments/js/crm_lead.js",
]

# ----------------------------------------
# DOCTYPE JS (Form-level JS)
# ----------------------------------------

doctype_js = {
    "Clinic Appointment": "public/js/clinic_appointment.js",
}

# ----------------------------------------
# DOCUMENT EVENTS
# ----------------------------------------
doc_events = {
    "Clinic Appointment": {
        "after_insert": "clinic_appointments.api.encounter.after_insert",
        # "on_update": "clinic_appointments.api.encounter.on_update"
    }
    # 🔥 Sync Appointment from Patient Encounter
    # "Patient Encounter": {
    #     "after_insert": "clinic_appointments.api.encounter_sync.create_or_update_clinic_appointment_from_encounter",
    #     "on_update": "clinic_appointments.api.encounter_sync.create_or_update_clinic_appointment_from_encounter",
    # }
}

# ----------------------------------------
# SCHEDULER EVENTS (Optional - Future Use)
# ----------------------------------------

scheduler_events = {
    # Example: auto update status (No Show, etc.)
    "hourly": [
        # "clinic_appointments.api.scheduler.update_appointment_status"
    ],
}

# ----------------------------------------
# FIXTURES (Optional)
# ----------------------------------------

fixtures = [
    # Example:
    # {"dt": "Custom Field", "filters": [["module", "=", "Clinic Appointments"]]}
]

# ----------------------------------------
# OVERRIDE WHITELISTED METHODS (Optional)
# ----------------------------------------

override_whitelisted_methods = {
    # Example:
    # "frappe.client.get_count": "clinic_appointments.api.custom.get_count"
}

# ----------------------------------------
# AFTER INSTALL (Optional)
# ----------------------------------------

after_install = "clinic_appointments.install.after_install"
after_migrate = "clinic_appointments.install.after_migrate"


# ----------------------------------------
# BEFORE UNINSTALL (Optional)
# ----------------------------------------

# before_uninstall = "clinic_appointments.install.before_uninstall"


# Apps
# ------------------

# required_apps = []

# Each item in the list will be shown as an app in the apps page
# add_to_apps_screen = [
# 	{
# 		"name": "clinic_appointments",
# 		"logo": "/assets/clinic_appointments/logo.png",
# 		"title": "Clinic Appointments",
# 		"route": "/clinic_appointments",
# 		"has_permission": "clinic_appointments.api.permission.has_app_permission"
# 	}
# ]

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/clinic_appointments/css/clinic_appointments.css"
# app_include_js = "/assets/clinic_appointments/js/clinic_appointments.js"

# include js, css files in header of web template
# web_include_css = "/assets/clinic_appointments/css/clinic_appointments.css"
# web_include_js = "/assets/clinic_appointments/js/clinic_appointments.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "clinic_appointments/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
# doctype_js = {"doctype" : "public/js/doctype.js"}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Svg Icons
# ------------------
# include app icons in desk
# app_include_icons = "clinic_appointments/public/icons.svg"

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
# 	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Jinja
# ----------

# add methods and filters to jinja environment
# jinja = {
# 	"methods": "clinic_appointments.utils.jinja_methods",
# 	"filters": "clinic_appointments.utils.jinja_filters"
# }

# Installation
# ------------

# before_install = "clinic_appointments.install.before_install"
# after_install = "clinic_appointments.install.after_install"

# Uninstallation
# ------------

# before_uninstall = "clinic_appointments.uninstall.before_uninstall"
# after_uninstall = "clinic_appointments.uninstall.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "clinic_appointments.utils.before_app_install"
# after_app_install = "clinic_appointments.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "clinic_appointments.utils.before_app_uninstall"
# after_app_uninstall = "clinic_appointments.utils.after_app_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "clinic_appointments.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# DocType Class
# ---------------
# Override standard doctype classes

# override_doctype_class = {
# 	"ToDo": "custom_app.overrides.CustomToDo"
# }

# Document Events
# ---------------
# Hook on document methods and events

# doc_events = {
# 	"*": {
# 		"on_update": "method",
# 		"on_cancel": "method",
# 		"on_trash": "method"
# 	}
# }

# Scheduled Tasks
# ---------------

# scheduler_events = {
# 	"all": [
# 		"clinic_appointments.tasks.all"
# 	],
# 	"daily": [
# 		"clinic_appointments.tasks.daily"
# 	],
# 	"hourly": [
# 		"clinic_appointments.tasks.hourly"
# 	],
# 	"weekly": [
# 		"clinic_appointments.tasks.weekly"
# 	],
# 	"monthly": [
# 		"clinic_appointments.tasks.monthly"
# 	],
# }

# Testing
# -------

# before_tests = "clinic_appointments.install.before_tests"

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "clinic_appointments.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "clinic_appointments.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["clinic_appointments.utils.before_request"]
# after_request = ["clinic_appointments.utils.after_request"]

# Job Events
# ----------
# before_job = ["clinic_appointments.utils.before_job"]
# after_job = ["clinic_appointments.utils.after_job"]

# User Data Protection
# --------------------

# user_data_fields = [
# 	{
# 		"doctype": "{doctype_1}",
# 		"filter_by": "{filter_by}",
# 		"redact_fields": ["{field_1}", "{field_2}"],
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_2}",
# 		"filter_by": "{filter_by}",
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_3}",
# 		"strict": False,
# 	},
# 	{
# 		"doctype": "{doctype_4}"
# 	}
# ]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
# 	"clinic_appointments.auth.validate"
# ]

# Automatically update python controller files with type annotations for this app.
# export_python_type_annotations = True

# default_log_clearing_doctypes = {
# 	"Logging DocType Name": 30  # days to retain logs
# }

# Translation
# ------------
# List of apps whose translatable strings should be excluded from this app's translations.
# ignore_translatable_strings_from = []

