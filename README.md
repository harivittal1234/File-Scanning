# Credit-Based Document Scanning System


This project is a Flask-based web application that allows users to upload documents, analyze their content, and find similar documents based on text similarity using TF-IDF and cosine similarity. The application also includes user authentication, role-based access control, and credit management for document scans.

## Features

- **User Authentication**: Users can register, log in, and log out. Sessions are managed using Flask's built-in session management.
- **Role-Based Access Control**: Different roles (user, admin) have access to different parts of the application.
- **Document Upload and Analysis**: Users can upload documents (text files, PDFs, images) and analyze their content.
- **Document Similarity**: The application calculates the similarity between uploaded documents and previously stored documents using TF-IDF and cosine similarity.
- **Credit Management**: Users have a credit system where each document scan deducts credits. Users can request additional credits, which admins can approve or reject.
- **Admin Dashboard**: Admins can view analytics, manage credit requests, and view user activity.

## Prerequisites

Before running the application, ensure you have the following installed:

- Python 3.x
- Flask
- SQLite3

## Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/harivittal1234/File-Scanning.git
   
   

2. **Set up a virtual environment** (optional but recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

3. **Install the required dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Initialize the database**:
   - The application uses SQLite for database management. Run the following command to initialize the database:
     ```bash
     python init_db.py
     ```

5. **Run the application**:
   ```bash
   python app.py
   ```

6. **Access the application**:
   - Open your web browser and navigate to `http://127.0.0.1:5000/`.

## Usage

### User Registration and Login

1. **Register a new user**:
   - Navigate to the registration page (`/register`) and fill in the required details.
   - After successful registration, you will be redirected to the login page.

2. **Log in**:
   - Use your registered credentials to log in at the login page (`/login`).

### Document Upload and Analysis

1. **Upload a document**:
   - After logging in, navigate to the document upload section.
   - Select a document (text file, PDF, or image) and upload it.

2. **View analysis results**:
   - The application will analyze the document and display the results, including a content snippet, preprocessed words, term frequencies, and similarity scores with other documents.

### Credit Management

1. **Request credits**:
   - If you run out of credits, you can request additional credits from the admin.
   - Navigate to the credit request section and submit a request.

2. **Admin approval**:
   - Admins can view pending credit requests and approve or reject them.

### Admin Dashboard

1. **View analytics**:
   - Admins can access the analytics dashboard to view user activity, document scans, and credit usage statistics.

2. **Manage credit requests**:
   - Admins can approve or reject credit requests from users.

## API Endpoints

- **User Authentication**:
  - `POST /auth/login`: Log in a user.
  - `POST /auth/register`: Register a new user.
  - `POST /auth/logout`: Log out the current user.

- **Document Management**:
  - `POST /scan`: Upload and analyze a document.
  - `GET /matches/<int:doc_id>`: Get similar documents for a given document ID.

- **Credit Management**:
  - `POST /credits/request`: Request additional credits.
  - `GET /admin/credit-requests`: View pending credit requests (admin only).
  - `POST /admin/credit-requests/<int:request_id>/approve`: Approve a credit request (admin only).
  - `POST /admin/credit-requests/<int:request_id>/reject`: Reject a credit request (admin only).

- **Admin Analytics**:
  - `GET /admin/analytics`: View analytics data (admin only).

## Contributing


## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Flask for providing the web framework.
- SQLite for database management.
- The TF-IDF and cosine similarity algorithms for document analysis.
```

You can copy and paste this Markdown content directly into your `README.md` file on GitHub. Once added, you can click the "Preview" button to see how it will look.
