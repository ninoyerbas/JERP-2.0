# JERP 2.0 - On-Premise Compliance ERP Suite

**Julio's Enterprise Resource Planning System - Version 2.0**

A comprehensive, on-premise ERP solution focused on **Labor Law Compliance** and **Financial Compliance (GAAP/IFRS**).

## 🎯 Overview

JERP 2.0 is a complete enterprise resource planning system designed for single-tenant, on-premise deployment. Built from the ground up with compliance as the core focus.

### Target Hardware
- **ACEMAGIC AM08Pro Mini PC**
- AMD Ryzen 9 6900HX (8 cores/16 threads)
- 32GB DDR5 RAM
- 1TB NVMe SSD

## 🔒 Compliance Focus

| Area | Standards |
|------|-----------|
| **Labor Law** | California Labor Code, Federal FLSA |
| **Financial** | GAAP (US), IFRS (International) |
| **Audit** | Immutable SHA-256 hash-chained logs |

## 📦 Modules

- Core (Auth, RBAC, Security)
- HR/HRIS
- Payroll (with compliance enforcement)
- CRM
- Finance (GAAP/IFRS validated)
- Inventory
- Procurement
- Manufacturing
- Project Management
- Helpdesk
- BI/Reports
- Notifications
- Documents
- Workflow Engine
- AI/ML
- Multi-language (i18n)
- Mobile Support

## 🚀 Quick Start

```bash
# Clone the repository
git clone https://github.com/ninoyerbas/JERP-2.0.git
cd JERP-2.0

# Configure environment
cp .env.example .env
# Edit .env with your settings

# Deploy
docker-compose up -d
```

## 📚 Documentation

- [Installation Guide](docs/INSTALLATION.md)
- [Compliance Guide](docs/COMPLIANCE_GUIDE.md)
- [Admin Guide](docs/ADMIN_GUIDE.md)
- [API Reference](docs/API_REFERENCE.md)
- [Statement of Work](SOW.md)

## 📄 License

MIT License - See LICENSE file for details.

---

**JERP 2.0** - Enterprise Compliance Made Simple