# DocAppoint

**DocAppoint** is a patient appointment dashboard with Django REST framework and React frontend with design based on the course [Build Full Stack Doctor Appointment Booking System](https://www.youtube.com/watch?v=eRTTlS0zaW8). The application is containerized with Docker in order to provide high portability, easy scalability, and consistent deployment. All logics are kept separate and data are shared only through REST. This app is work in-progress and will be updated reguarly.

### Features
* Authentication:
  * User login/logout and sign up
  * Account email verification
    * Resend verification email
  * Secure access via JWT
    * Background JWT refresh via frontend interceptor

* Doctors:
  * Paginated list of active doctors with filter
  * Detailed doctor profile (education, fees, speciality, etc.)

* Company:
  * Display company information

* Scalability
  * Containeriztion of different services via Docker

* Safety
  * Database audit trail
  * Sensitive tables soft delete

* Misc
  * Unit tested backend

## Compliance & Security
* HIPAA Security Rule alignment (access control, encryption in transit, audit-log, rate-limiting)

* Unique user IDs & role-based permission

* Password hashed with PBKDF2, and JWT access/refresh tokens with rotation

* HTTPS enforced

## Getting Started

### Setup

You will need Docker, Django, and React.

### Acknowledgement

The project's frontend based on [Build Full Stack Doctor Appointment Booking System](https://www.youtube.com/watch?v=eRTTlS0zaW8) by [GreatStack](https://www.youtube.com/@GreatStackDev). This implementation refactored the code from JavaScript to TypeScript.
