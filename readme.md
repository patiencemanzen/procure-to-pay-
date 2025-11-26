# Procure-to-Pay System

Procurement management system that streamlines the entire purchasing process from request to payment. Built with Django REST Framework and React, this system helps organizations manage procurement workflows with multiple approval levels, document processing, and financial oversight.

## Why This Project?

Procurement can be a complex, time-consuming process filled with paperwork, approval bottlenecks, and miscommunication. Our Procure-to-Pay system transforms this experience by:

- **Simplifying** the request process for employees
- **Automating** approval workflows to reduce delays
- **Centralizing** all procurement documentation
- **Providing** real-time visibility into procurement status
- **Ensuring** compliance with organizational policies

## System Architecture

### Backend (Django REST Framework)

- **Python 3.11** with Django 4.2.7
- **PostgreSQL** database for production
- **Redis** for caching and task queuing
- **Celery** for background task processing
- **Tesseract OCR** for document text extraction

### Frontend (React 18)

- **React** with functional components and hooks
- **Tailwind CSS** for responsive, beautiful UI
- **React Router** for client-side navigation
- **Axios** for API communication
- **React Hook Form** for form management

### Infrastructure

- **Render.com** for backend hosting
- **Vercel** for frontend deployment
- **PostgreSQL** managed database
- **Docker** containerization support

## User Roles & Capabilities

### Staff Members

- Create and submit purchase requests
- Upload proforma invoices and supporting documents
- Track request status and approval progress
- View their procurement history

### Level 1 Approvers

- Review and approve/reject requests up to certain amounts
- Add comments and feedback to requests
- View team procurement activities
- Escalate complex requests to Level 2

### Level 2 Approvers

- Handle high-value purchase requests
- Final approval authority for complex purchases
- Override Level 1 decisions when necessary
- Strategic procurement oversight

### Finance Team

- Generate and manage purchase orders
- Validate receipts against POs
- Financial reporting and analytics
- Budget monitoring and compliance

### System Administrators

- User management and role assignments
- System configuration and settings
- Backup and maintenance tasks
- Security monitoring

## Technology Stack

| Component | Technology | Purpose |
|-----------|------------|---------|
| **Backend API** | Django REST Framework 3.14 | RESTful API development |
| **Database** | PostgreSQL | Reliable data storage |
| **Authentication** | JWT (SimpleJWT) | Secure user authentication |
| **File Processing** | Tesseract OCR | Document text extraction |
| **Task Queue** | Celery + Redis | Background job processing |
| **API Documentation** | DRF Spectacular | Interactive API docs |
| **Frontend** | React 18 | Modern user interface |
| **Styling** | Tailwind CSS | Responsive design |
| **State Management** | React Hooks | Component state management |
| **HTTP Client** | Axios | API communication |
| **Routing** | React Router | Client-side navigation |

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 16+
- PostgreSQL 13+
- Redis (for production)

### Backend Setup

1. **Clone the repository**

   ```bash
   git clone https://github.com/patiencemanzen/procure-to-pay-.git
   cd procure-to-pay-
   ```

2. **Set up Python environment**

   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Configure environment variables**

   ```bash
   cp .env.example .env
   # Edit .env with your database and other settings
   ```

4. **Set up database**

   ```bash
   python manage.py migrate
   python manage.py createsuperuser
   ```

5. **Run the development server**

   ```bash
   python manage.py runserver
   ```

### Frontend Setup

1. **Install dependencies**

   ```bash
   cd frontend
   npm install
   ```

2. **Start development server**

   ```bash
   npm start
   ```

The application will be available at:

- **Backend API**: <http://localhost:8000>
- **Frontend**: <http://localhost:3000>
- **API Documentation**: <http://localhost:8000/api/schema/swagger-ui/>

## Live Demo

- **Frontend Application**: [https://procure-to-pay-two.vercel.app](https://procure-to-pay-two.vercel.app)
- **Backend API**: [https://procure-to-pay-server.onrender.com](https://procure-to-pay-server.onrender.com)
- **API Documentation**: [https://procure-to-pay-server.onrender.com/api/schema/swagger-ui/](https://procure-to-pay-server.onrender.com/api/schema/swagger-ui/)

### Demo Accounts

Try the system with these pre-configured accounts:

| Role | Email | Password | Description |
|------|-------|----------|-------------|
| **Staff** | <staff@example.com> | password123 | Can create purchase requests |
| **Level 1 Approver** | <approver1@example.com> | password123 | Can approve small requests |
| **Level 2 Approver** | <approver2@example.com> | password123 | Can approve large requests |
| **Finance** | <finance@example.com> | password123 | Manages POs and receipts |
| **Admin** | <admin@example.com> | password123 | Full system access |

## API Endpoints

### Authentication

- `POST /api/auth/login/` - User login
- `POST /api/auth/refresh/` - Token refresh
- `GET /api/auth/user/` - Get user profile

### Purchase Requests

- `GET /api/requests/` - List all requests
- `POST /api/requests/` - Create new request
- `GET /api/requests/{id}/` - Get request details
- `PUT /api/requests/{id}/` - Update request
- `POST /api/requests/{id}/approve/` - Approve request
- `POST /api/requests/{id}/reject/` - Reject request

### Purchase Orders

- `GET /api/purchase-orders/` - List purchase orders
- `POST /api/purchase-orders/` - Create purchase order
- `GET /api/purchase-orders/{id}/` - Get PO details

### File Management

- `POST /api/upload/proforma/` - Upload proforma invoice
- `POST /api/upload/receipt/` - Upload receipt
- `GET /api/files/{id}/` - Download file

### Docker Deployment

```bash
# Build and run with Docker Compose
docker-compose up --build
```

## Contact

**Project Maintainer**: Patience Manzen  
**Email**: <patiencemanzen@example.com>  
**GitHub**: [@patiencemanzen](https://github.com/patiencemanzen)

---

Built with ❤️ for procurement management.
