# Koloni API - README

## Table of Contents
1. [Introduction](#introduction)
2. [Getting Started with the Repository](#getting-started-with-the-repository)
3. [Docker Configuration](#docker-configuration)
4. [Database and SQL Setup](#database-and-sql-setup)
5. [Environment Configuration (.env)](#environment-configuration-env)
6. [Running the Project](#running-the-project)
7. [Contributing to the Project](#contributing-to-the-project)
8. [Testing the Features](#testing-the-features)
9. [Obtaining JWT for Mobile/Organization](#obtaining-jwt-for-mobileorganization)
10. [Troubleshooting and FAQs](#troubleshooting-and-faqs)
11. [Contact/Support](#contact-support)
12. [License](#license)

## Introduction
Koloni is a cutting-edge platform offering Smart Locker Solutions, designed to simplify and enhance delivery, storage, and rental applications. By deploying smart lockers swiftly, Koloni streamlines operations for a variety of use cases.

### Key Features:
- **Smart Locker Deployment:** Quick and easy setup of smart lockers for various applications.
- **Versatile Applications:** Ideal for delivery, storage, and rental needs.
- **Innovative Technology:** Utilizes the latest in smart technology to provide secure and efficient locker solutions.
- **User-Friendly Interface:** Designed for ease of use, ensuring a seamless experience for both operators and users.
- **Customizable Solutions:** Adaptable to meet the specific requirements of different environments and applications.

### Why Koloni?
Koloni aims to revolutionize how goods and services are stored, delivered, and rented, by offering a highly efficient, secure, and user-friendly solution. Whether it’s for commercial or personal use, Koloni’s smart lockers are designed to cater to the dynamic needs of modern-day logistics and storage.

For more information, visit our website: [Koloni](https://www.koloni.io/)

## Getting Started with the Repository

This section guides you through getting the Koloni project up and running on your local machine for development and testing purposes.

### Cloning the Repository
To start working with the Koloni project, you first need to clone the repository to your local machine. Use the following command:

```
git clone https://github.com/Koloni-Share/lockers-api.git
```

### Initial Setup
After cloning the repository, navigate to the project directory. The setup process is simplified thanks to Docker.

### Environment Configuration
To configure the environment for the Koloni project, you need to set up the `.env` file using the provided `.env.template` as a guide. The database variables are the most important for starting up the application. Follow these steps:

1. **Create `.env` File**: Copy the `.env.template` file and rename the copy to `.env`.

2. **Fill in Environment Variables**: Replace the placeholder values in the `.env` file with your actual data. Here's a breakdown of what each variable represents:

    ```env
    # FastAPI environment variables
    project_name=koloni-lockers
    backend_cors_origin=["*"]
    environment=local
    
    # Api Version
    api_endpoint_version="v3"

    # PostgreSQL database environment variables
    database_host=db
    database_user=<db_user>
    database_password=<db_password>
    database_name=docker
    database_port=5432

    test_database_user=<db_user>
    test_database_password=<db_password>
    test_database_host=localhost
    test_database_port=5432
    test_database_name=docker
    test_api_base_url=http://k/

    # Redis variables
    redis_host=localhost
    redis_port=6379
    redis_url=redis://cache:6379

    # Stripe variables
    stripe_api_key='<stripe_api_key>'

    # Twilio variables
    twilio_sid='<twilio_sid>'
    twilio_secret='<twilio_secret>'
    twilio_phone_number='<twilio_phone_number>'
    twilio_verification_sid='<twilio_verification_sid>'
    twilio_sendgrid_api_key='<twilio_sendgrid_api_key>'
    twilio_sendgrid_auth_sender='<twilio_sendgrid_auth_sender>'

    # Cognito variables
    cognito_client_secret='<cognito_client_secret>'

    # Other variables
    sentry_dsn='<sentry_dsn>'
    images_bucket='koloni-org-data'
    frontend_origin='https://test.lockers.koloni.io'

    aws_region='us-east-1'

    pinpoint_origination_number='<pinpoint_origination_number>'
    pinpoint_app_id='<pinpoint_app_id>'

    jwt_secret_key='<jwt_secret_key>'

    # AWS
    aws_access_key_id=<aws_access_key_id>
    aws_secret_access_key=<aws_secret_access_key>

    # Route 53 variables
    cluster_url='<aws_cluster_url>'
    twilio_messaging_service_sid='<twilio_messaging_service_sid>'

    limit=100
    interval=60

    # Test variables
    cognito_client_id=<cognito_client_id>
    cognito_username=<cognito_username>
    cognito_password=<cognito_password>

    ```
    Ensure to replace `<placeholder_values>` with your actual configuration values.

3. **Security Note**: Never commit your `.env` file or any file containing sensitive keys, passwords, or secret tokens to a public repository. Always keep such information confidential to prevent unauthorized access to your systems.
  ```bash
  cp .envrc.template .envrc
  ```
4. 

### Running the Application with Docker Compose
Using Docker simplifies the process of setting up the Koloni application, as there's no need to manually install dependencies. Docker Compose is used to build and run the application.

#### Starting the Application
- To start the application, run the following command in the root directory of the project:

  ```
  docker compose up --build
  ```
- This command builds the Docker images and starts the containers as outlined in your `docker-compose.yml` file.

- Once the build is complete, you can access the API documentation by navigating to `localhost:5002/docs`. This URL points to the API documentation and interactive UI provided by FastAPI.

#### Port Configuration
The API container is set to expose port `5000`. However, for convenience, especially for macOS users who might have port `5000` occupied, Docker Compose is configured to forward the host's `5002` port to the container's `5000` port.

Therefore, when accessing the application, use port `5002` (e.g., `localhost:5002`).

With these steps, the Koloni application should be running and accessible on your local machine.


## Database and SQL Setup

The Koloni project requires careful management of database migrations and SQL queries. This section provides guidelines for adding new columns, resetting the database, backing up changes, and handling migrations.

### Database Migrations
Database migrations are essential for maintaining and updating the database schema.

#### Adding New Columns
- To add a new column to a table:
  1. **SSH into the Database Container**: Access the Docker container running the database. The recommended approach is to use the Docker extension for VSCode or the following command:
     ```bash
     docker exec -it [database-container-name] bash
     ```
  2. **Run the SQL Query**: Execute the necessary SQL query to modify the database schema. Remember to document each query you run for tracking purposes.

#### Resetting the Database
- If you need to revert your database to its original state:
  1. **Remove All Docker Data**:
     ```bash
     docker system prune -a
     ```
  2. **Rebuild with Docker Compose**: This will reset the database to its base state using `init.sql`.
     ```bash
     docker compose up --build
     ```

#### Backing Up Changes
- After modifying the database:
  1. **Run Backup Script**: Execute `./backup.sh` in the root of the project while the database container is running. This script copies the updated `init.sql` from the database container to the project.
  2. **Create a Pull Request**: Document your changes and make a PR with the format:
     ```
     # Requirements
     <SQL formatted queries you've run>

     # Description
     <Screenshots/Description of the changes>
     ```
     Label the PR with `db upgrade`.

### Handling Migrations Issues
- During development, if you encounter issues like "missing column...from table...", it may be due to a recent migration. To resolve this:
  1. **Prune Docker System**:
     ```bash
     docker system prune -a
     ```
  2. **Rebuild with Docker Compose**:
     ```bash
     docker compose up --build
     ```

This approach ensures that database changes are properly managed, tracked, and integrated into the project, facilitating a smooth development process.



[//]: # (## Testing the Features)

[//]: # (- **Running Tests:**)

[//]: # (&#40;Instructions on how to execute tests, including any specific commands or frameworks used.&#41;)

## Obtaining JWT for Mobile/Organization

Obtaining a JSON Web Token (JWT) is essential for accessing protected routes in the Koloni application, especially for mobile and organization-level access. This section covers the steps for generating JWTs for these purposes.

### Generating JWT for Organization-Level Access
For organization-level or partner routes, you need to use the `/partner/login` endpoint to obtain a JWT.

#### Steps to Login as a Partner
1. **Fetch Organization Details**: To get the `user_pool_id` and `client_id`, use the public endpoint `/organization` with the organization's name:
   ```bash
   curl -X GET "https://[api-url]/organization?name=[organization-name]"
   ```
    Replace `[api-url]` with your API's URL and `[organization-name]` with the name of the organization.

2. **Login Endpoint**:
Use the `/partner/login` endpoint with the necessary credentials.
    ```bash
    curl -X POST "https://[api-url]/partner/login" -H "Content-Type: application/json" -d '{
        "username": "[username]",
        "password": "[password]",
        "user_pool_id": "[user_pool_id from step 1]",
        "client_id": "[client_id from step 1]"
    }'
    ```
    Replace [username], [password], [user_pool_id], and [client_id] with the appropriate values.

After successfully logging in, you will receive a JWT which can be used for authenticated requests to the Koloni API for organization-level operations.

[//]: # (## Troubleshooting and FAQs)

[//]: # (&#40;Include common issues and their solutions, along with frequently asked questions and answers.&#41;)

[//]: # ()
[//]: # (## Contact/Support)

[//]: # (&#40;Provide contact information or links for project support or queries.&#41;)

## License

Koloni is a private software and all rights are reserved. The source code, documentation, and other related materials are confidential and proprietary. Any unauthorized copying, distribution, modification, or use of this software is strictly prohibited.

For more information on licensing and permissible use, please contact [helpdesk@koloni.me](mailto:helpdesk@koloni.me).

This software is not subject to open source licensing, such as the MIT License, and is intended for authorized use only under the terms and conditions expressly agreed upon with [Koloni](https://www.koloni.io/).
