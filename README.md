### Clinic Appointments

Appointment control app integrated with patient encounter workflow

---

## Features

---

## Requirements

- **Frappe Framework** v15+
- **ERPNext** v15+
- **Python** 3.10+
- **Bench CLI**

---

## Installation

Install the app using the **Bench CLI**.

```bash
cd $PATH_TO_YOUR_BENCH

bench get-app https://github.com/YOUR_GITHUB_USERNAME/clinic_appointments.git

bench --site <your-site-name> install-app clinic_appointments

bench --site <your-site-name> migrate

bench build

bench restart
```

---

## Contributing

This app uses `pre-commit` for code formatting and linting. Please [install pre-commit](https://pre-commit.com/#installation) and enable it for this repository:

```bash
cd apps/clinic_appointments
pre-commit install
```

Pre-commit is configured to use the following tools for checking and formatting your code:

- ruff
- eslint
- prettier
- pyupgrade

---

## License

MIT