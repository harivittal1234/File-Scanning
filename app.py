from flask import Flask, request, jsonify, session, render_template #We are adding session from Flask because we'll use Flask's built-in session management to keep users logged in after successful login. We are also adding render_template because we will need to serve the login.html file later.
import sqlite3
from werkzeug.utils import secure_filename
from models import User, Document
from db import get_db_connection 
from functools import wraps # Import wraps for decorator best practices
import re
import os
import math
from collections import Counter


app = Flask(__name__)
app.config['SECRET_KEY'] = 'qwerty1234'  # this should be a long random string

###FRONTEND ROUTES
@app.route('/')
def home():
    return render_template("index.html")

@app.route('/login')
def login_page():
    return render_template('login.html') # Serve login.html template

@app.route('/register')
def register_page():
    return render_template('register.html')



#Decorators
#checks if user is logged in and has the required role
def role_required(role): #Decorator factory function to check user role
    def decorator(f):  #the actual decorator function. It takes the route handler function f as an argument
        @wraps(f) # Keeps original function metadata
        def wrapper(*args, **kwargs):
            user_role = session.get('user_role') # Get user role from session

            if not session.get('user_id'): # Check if user_id is in session (logged in)
                return jsonify({'message': 'Unauthorized - Login required'}), 401 # 401 Unauthorized

            if user_role != role: # Check if user has the required role
                return jsonify({'message': f'Forbidden - Requires {role} role'}), 403 # 403 Forbidden

            return f(*args, **kwargs) # If authorized, execute the route handler function

        return wrapper
    return decorator

#frontend_ADMIN
@app.route('/admin/dashboard')
@role_required('admin')  # Ensure only admins can access this route
def admin_dashboard():
    return render_template('admin_dashboard.html')


#LOGIN ENDPOINT
@app.route('/auth/login', methods=['POST'])
def login_user():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({'message': 'Both Username and password are required'}), 400

    user = User.get_user_by_username(username)

    if not user:
        return jsonify({'message': 'Invalid username'}), 401  # 401 Unauthorized

    if not user.check_password(password):
        return jsonify({'message': 'Invalid password'}), 401  # 401 Unauthorized

    session['user_id'] = user.id  # Store user ID in session
    session['user_role'] = user.role  # Store user role in session

    return jsonify({
        'message': 'Login successful',
        'role': user.role  # Include the user's role in the response
    }), 200  # 200 OK

#REGISTER ENDPOINT
@app.route('/auth/register', methods=['POST'])
def register_user():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({'message': 'Username and password are required'}), 400

    if User.get_user_by_username(username):
        return jsonify({'message': 'Username already exists'}), 409 # 409 Conflict

    user_id = User.create_user(username, password)
    if user_id:
        return jsonify({'message': 'User registered successfully'}), 201 # 201 Created
    else: # Should not reach here ideally if username conflict is handled above, but for safety
        return jsonify({'message': 'Registration failed'}), 500 # 500 Internal Server Error

#User Profile Endpoint
@app.route('/user/profile', methods=['GET'])
@role_required('user')  # Apply the role_required decorator, requiring 'user' role
def get_user_profile():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'message': 'Unauthorized'}), 401
    user = User.get_user_by_id(user_id)
    if not user:
        return jsonify({'message': 'User not found'}), 404

    user_profile = {
        'username': user.username,
        'credits': user.total_credits,
        'role': user.role
    }
    return jsonify(user_profile), 200

#Logout Endpoint
@app.route('/auth/logout', methods=['POST'])
def logout_user():
    session.clear() # Clear the Flask session, effectively logging the user out
    return jsonify({'message': 'Logout successful'}), 200 # 200 OK, logout success message



def preprocess_text(text):
    """
    Preprocesses text by converting to lowercase, removing punctuation, and splitting into words.

    Args:
        text: The input text string.

    Returns:
        A list of preprocessed words.
    """
    text = text.lower()  # Convert text to lowercase
    text = re.sub(r'[^\w\s]', '', text)  # Remove punctuation using regular expressions
    words = text.split()  # Split text into words (by whitespace)
    return words

def calculate_term_frequency(word_list):
    """
    Calculates term frequency from a list of words.

    Args:
        word_list: A list of words (strings).

    Returns:
        A dictionary where keys are unique words and values are their term frequencies.
    """
    # Count occurrences of each word
    word_counts = Counter(word_list)
    # Calculate term frequency
    total_words = len(word_list)
    return {word: count/total_words for word, count in word_counts.items()}

def calculate_document_frequency(documents_words):
    """
    Calculates document frequency for each word.

    Args:
        documents_words: A list of lists, where each inner list contains the words in a document.

    Returns:
        A dictionary mapping words to their document frequency.
    """
    df = {}
    num_docs = len(documents_words)
    
    # Count number of documents containing each word
    for doc_words in documents_words:
        unique_words = set(doc_words)
        for word in unique_words:
            df[word] = df.get(word, 0) + 1
    
    # Convert to IDF (Inverse Document Frequency)
    idf = {word: math.log(num_docs / (freq + 1)) + 1 for word, freq in df.items()}
    return idf

def calculate_tfidf_vector(term_freq, idf):
    """
    Calculates TF-IDF vector for a document.

    Args:
        term_freq: Term frequency dictionary for the document.
        idf: IDF dictionary.

    Returns:
        A dictionary representing the TF-IDF vector.
    """
    return {word: tf * idf.get(word, 0) for word, tf in term_freq.items()}

def cosine_similarity(vec1, vec2):
   #returns the cosine similarity between two vectors
    # Find common words
    common_words = set(vec1.keys()) & set(vec2.keys())
    
    # Calculate dot product
    dot_product = sum(vec1[word] * vec2[word] for word in common_words)
    
    # Calculate magnitudes
    magnitude1 = math.sqrt(sum(val * val for val in vec1.values()))
    magnitude2 = math.sqrt(sum(val * val for val in vec2.values()))
    
    # Avoid division by zero
    if magnitude1 == 0 or magnitude2 == 0:
        return 0
    
    # Calculate cosine similarity
    return dot_product / (magnitude1 * magnitude2)

def get_documents_from_uploads():
    """
    Reads all text files from the uploads directory and returns their content.

    Returns:
        A dictionary mapping filenames to their content.
    """
    documents = {}
    upload_folder = 'uploads'
    
    # Make sure the folder exists
    os.makedirs(upload_folder, exist_ok=True)
    
    # Read all text files in the uploads folder
    for filename in os.listdir(upload_folder):
        filepath = os.path.join(upload_folder, filename)
        
        # Only process text files for now
        if filename.endswith('.txt') and os.path.isfile(filepath):
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                documents[filename] = content
            except Exception as e:
                print(f"Error reading {filename}: {e}")
    
    return documents

# This will be called when the Flask app starts and whenever we need fresh data
def update_document_vectors():
    # Get documents from uploads folder
    stored_documents = get_documents_from_uploads()
    
    if not stored_documents:
        print("Warning: No documents found in uploads folder.")
        return {}, {}, []
    
    # Preprocess all documents
    preprocessed_docs = {doc_id: preprocess_text(content) for doc_id, content in stored_documents.items()}
    
    # Calculate document frequency across all documents
    all_doc_words = list(preprocessed_docs.values())
    idf = calculate_document_frequency(all_doc_words)
    
    # Calculate TF-IDF vectors for all documents
    tfidf_vectors = {}
    for doc_id, words in preprocessed_docs.items():
        tf = calculate_term_frequency(words)
        tfidf_vectors[doc_id] = calculate_tfidf_vector(tf, idf)
    
    return stored_documents, tfidf_vectors, idf

# Initialize document data variables
STORED_DOCUMENTS, DOCUMENT_VECTORS, GLOBAL_IDF = {}, {}, {}


#Scan endpoint
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg'} # Or similar set of allowed extensions

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# Preprocess STORED_DOCUMENTS and calculate word frequencies


def calculate_word_overlap_similarity(doc1_frequencies, doc2_frequencies):
    """
    Calculates word overlap similarity between two documents based on word frequencies.

    Args:
        doc1_frequencies: Word frequency dictionary for document 1.
        doc2_frequencies: Word frequency dictionary for document 2.

    Returns:
        The word overlap similarity score (number of common words).
    """
    doc1_words = set(doc1_frequencies.keys()) # Get unique words from doc1
    doc2_words = set(doc2_frequencies.keys()) # Get unique words from doc2
    common_words = doc1_words.intersection(doc2_words) # Find common words (intersection of sets)
    overlap_score = len(common_words) # Word overlap score is the number of common words
    return overlap_score

STORED_DOCUMENTS = {}
DOCUMENT_VECTORS = {} 
GLOBAL_IDF = {}

@app.route('/scan', methods=['POST'])
@role_required('user')
def scan_document():
    # --- Credit Deduction Logic ---

    global STORED_DOCUMENTS, DOCUMENT_VECTORS, GLOBAL_IDF

    user_id = session.get('user_id')
    user = User.get_user_by_id(user_id)

    if not user:
        return jsonify({'message': 'User not found'}), 404

    if user.total_credits <= 0:
        return jsonify({'message': 'Insufficient credits'}), 402

    User.decrement_credits(user_id)
    
    # --- Document Upload Handling ---
    if 'document' not in request.files:
        return jsonify({'message': 'No document part'}), 400

    file = request.files['document']

    if file.filename == '':
        return jsonify({'message': 'No selected file'}), 400

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        upload_folder = 'uploads'
        os.makedirs(upload_folder, exist_ok=True)
        filepath = os.path.join(upload_folder, filename)
        file.save(filepath)

        # --- Document Processing ---
        scan_results = {}
        file_extension = filename.rsplit('.', 1)[1].lower()
        
        if file_extension == 'txt':
            document_type = "Text Document"
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    uploaded_document_content = f.read()
                
                # Process the document content
                preprocessed_words = preprocess_text(uploaded_document_content)
                term_frequencies = calculate_term_frequency(preprocessed_words)
                
                # Calculate TF-IDF for the uploaded document
                uploaded_tfidf = calculate_tfidf_vector(term_frequencies, GLOBAL_IDF)
                
                # Get a content snippet for display
                content_snippet = uploaded_document_content[:200] + "..." if len(uploaded_document_content) > 200 else uploaded_document_content
                
                # Refresh document vectors to include any new documents
                
                STORED_DOCUMENTS, DOCUMENT_VECTORS, GLOBAL_IDF = update_document_vectors()
                
                # Calculate similarity with all stored documents
                document_similarities = {}
                for doc_id, doc_vector in DOCUMENT_VECTORS.items():
                    # Skip comparing to itself if it's already in the stored documents
                    if doc_id == filename:
                        continue
                    similarity_score = cosine_similarity(uploaded_tfidf, doc_vector)
                    document_similarities[doc_id] = similarity_score
                
                # Find the best match
                best_match_doc_id = "No Match Found"
                max_similarity_score = 0
                for doc_id, score in document_similarities.items():
                    if score > max_similarity_score:
                        max_similarity_score = score
                        best_match_doc_id = doc_id
                
                processing_status = "Text Content Extracted, Preprocessed, and TF-IDF Similarity Analysis Completed"
                
                scan_results['document_type'] = document_type
                scan_results['content_snippet'] = content_snippet
                scan_results['processing_status'] = processing_status
                scan_results['uploaded_document_content'] = uploaded_document_content
                scan_results['preprocessed_words'] = preprocessed_words
                scan_results['term_frequencies'] = term_frequencies
                scan_results['document_similarities'] = document_similarities
                scan_results['best_match_document_id'] = best_match_doc_id
                scan_results['best_match_similarity_score'] = round(max_similarity_score * 100, 2)  # Convert to percentage for clarity
                
            except Exception as e:
                document_type = "Text Document (Error Reading Content)"
                content_snippet = "Error reading document content."
                processing_status = f"Error: {str(e)}"
                uploaded_document_content = "Error reading file content"
                scan_results['document_type'] = document_type
                scan_results['content_snippet'] = content_snippet
                scan_results['processing_status'] = processing_status
                scan_results['uploaded_document_content'] = uploaded_document_content
                scan_results['preprocessed_words'] = []
                scan_results['term_frequencies'] = {}
                scan_results['document_similarities'] = {}
                scan_results['best_match_document_id'] = "N/A"
                scan_results['best_match_similarity_score'] = 0
        
        else:  # For non-text files (binary files)
            document_type = "Binary Document (Content Preview Unavailable)"
            content_snippet = "N/A - Binary file, cannot preview text content"
            processing_status = "Binary File - Content Extraction Skipped"
            uploaded_document_content = "Binary File - Content N/A"
            
            scan_results['document_type'] = document_type
            scan_results['content_snippet'] = content_snippet
            scan_results['processing_status'] = processing_status
            scan_results['uploaded_document_content'] = uploaded_document_content
            scan_results['preprocessed_words'] = []
            scan_results['term_frequencies'] = {}
            scan_results['document_similarities'] = {}
            scan_results['best_match_document_id'] = "N/A"
            scan_results['best_match_similarity_score'] = 0
        
        scan_results['filename'] = filename
        scan_results['filepath'] = filepath
        
        # --- Document Metadata Storage ---
        document = Document(filename=filename, filepath=filepath, user_id=user_id)
        if document.save():
            return jsonify({
                'message': 'Scan request received, credit deducted, document uploaded, metadata saved, text content extracted',
                'filename': filename,
                'filepath': filepath,
                'document_id': document.id,
                'scan_results': scan_results
            }), 200
        else:
            return jsonify({'message': 'Error saving document metadata to database'}), 500
    
    else:
        return jsonify({'message': 'Error uploading document'}), 500


@app.route('/matches/<int:doc_id>', methods=['GET'])
@role_required('user')
def get_similar_documents(doc_id):
    try:
        # Get the target document
        target_doc = Document.get_by_id(doc_id)
        if not target_doc:
            return jsonify({'message': 'Document not found'}), 404

        # Get all documents excluding the target
        all_docs = Document.get_all_documents()
        similar_docs = []
        
        # Get similarity scores from existing data (modify this based on your storage)
        target_filename = target_doc.filename
        target_vector = DOCUMENT_VECTORS.get(target_filename)
        
        if not target_vector:
            return jsonify({'message': 'Document analysis not available'}), 404

        # Calculate similarity with all documents
        for doc_filename, doc_vector in DOCUMENT_VECTORS.items():
            if doc_filename == target_filename:
                continue  # Skip self-comparison
                
            similarity = cosine_similarity(target_vector, doc_vector)
            if similarity > 0:  # Adjust threshold as needed
                similar_docs.append({
                    'document_id': Document.get_by_filename(doc_filename).id,
                    'filename': doc_filename,
                    'similarity_score': round(similarity * 100, 2)
                })

        # Sort by similarity score descending
        similar_docs.sort(key=lambda x: x['similarity_score'], reverse=True)
        
        # Limit results (optional)
        limit = request.args.get('limit', default=5, type=int)
        return jsonify({
            'target_document': target_filename,
            'matches': similar_docs[:limit]
        }), 200

    except Exception as e:
        return jsonify({'message': str(e)}), 500


@app.route('/credits/request', methods=['POST'])
@role_required('user')
def request_credits():
    # Get the logged-in user's ID from the session
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'message': 'Unauthorized'}), 401

    # Parse the request data
    data = request.get_json()
    if not data:
        return jsonify({'message': 'No data provided'}), 400

    requested_credits = data.get('requested_credits')

    # Convert requested_credits to an integer
    try:
        requested_credits = int(requested_credits)
    except (ValueError, TypeError):
        return jsonify({'message': 'Invalid credit request amount (must be a number)'}), 400

    # Validate the input
    if requested_credits <= 0:
        return jsonify({'message': 'Invalid credit request amount (must be greater than 0)'}), 400

    # Connect to the database
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Insert the credit request into the database
        cursor.execute(
            "INSERT INTO credit_requests (user_id, requested_credits, status) VALUES (?, ?, 'pending')",
            (user_id, requested_credits)
        )
        conn.commit()
        return jsonify({'message': 'Credit request submitted successfully'}), 201
    except sqlite3.Error as e:
        conn.rollback()
        return jsonify({'message': 'Failed to submit credit request', 'error': str(e)}), 500
    finally:
        conn.close()


@app.route('/admin/credit-requests', methods=['GET'])
@role_required('admin')
def get_pending_credit_requests():
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Fetch all pending credit requests
        cursor.execute("""
            SELECT cr.id, u.username, cr.requested_credits, cr.request_date
            FROM credit_requests cr
            JOIN users u ON cr.user_id = u.id
            WHERE cr.status = 'pending'
            ORDER BY cr.request_date DESC;
        """)
        pending_requests = cursor.fetchall()

        # Format results
        requests_list = []
        for row in pending_requests:
            requests_list.append({
                'id': row['id'],
                'username': row['username'],
                'requested_credits': row['requested_credits'],
                'request_date': row['request_date']
            })

        return jsonify(requests_list), 200
    except sqlite3.Error as e:
        return jsonify({'message': 'Failed to fetch pending requests', 'error': str(e)}), 500
    finally:
        conn.close()


@app.route('/admin/credit-requests/<int:request_id>/approve', methods=['POST'])
@role_required('admin')
def approve_credit_request(request_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Fetch the request
        cursor.execute("SELECT user_id, requested_credits FROM credit_requests WHERE id = ?", (request_id,))
        request_data = cursor.fetchone()

        if not request_data:
            return jsonify({'message': 'Request not found'}), 404

        user_id = request_data['user_id']
        requested_credits = request_data['requested_credits']

        # Update user's credits
        cursor.execute("UPDATE users SET credits = credits + ? WHERE id = ?", (requested_credits, user_id))

        # Update request status to 'approved'
        cursor.execute("UPDATE credit_requests SET status = 'approved' WHERE id = ?", (request_id,))

        conn.commit()
        return jsonify({'message': 'Credit request approved successfully'}), 200
    except sqlite3.Error as e:
        conn.rollback()
        return jsonify({'message': 'Failed to approve credit request', 'error': str(e)}), 500
    finally:
        conn.close()

@app.route('/admin/credit-requests/<int:request_id>/reject', methods=['POST'])
@role_required('admin')
def reject_credit_request(request_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Update request status to 'rejected'
        cursor.execute("UPDATE credit_requests SET status = 'rejected' WHERE id = ?", (request_id,))
        conn.commit()
        return jsonify({'message': 'Credit request rejected successfully'}), 200
    except sqlite3.Error as e:
        conn.rollback()
        return jsonify({'message': 'Failed to reject credit request', 'error': str(e)}), 500
    finally:
        conn.close()


@app.route('/admin/analytics', methods=['GET'])
@role_required('admin')
def get_admin_analytics():
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Scans per user per day
        cursor.execute("""
            SELECT u.username, DATE(d.scan_date) AS scan_day, COUNT(d.id) AS scan_count
            FROM documents d
            JOIN users u ON d.user_id = u.id
            GROUP BY u.username, DATE(d.scan_date)
            ORDER BY scan_day DESC, scan_count DESC;
        """)
        scans_per_user = cursor.fetchall()

        # Most common scanned document topics (assuming topics are derived from filenames)
        cursor.execute("""
            SELECT SUBSTR(filename, 1, INSTR(filename, '.') - 1) AS topic, COUNT(id) AS scan_count
            FROM documents
            GROUP BY topic
            ORDER BY scan_count DESC
            LIMIT 10;
        """)
        common_topics = cursor.fetchall()

        # Top users by scans and credit usage
        cursor.execute("""
            SELECT u.username, COUNT(d.id) AS total_scans, SUM(cr.requested_credits) AS total_credits_used
            FROM users u
            LEFT JOIN documents d ON u.id = d.user_id
            LEFT JOIN credit_requests cr ON u.id = cr.user_id AND cr.status = 'approved'
            GROUP BY u.username
            ORDER BY total_scans DESC, total_credits_used DESC
            LIMIT 10;
        """)
        top_users = cursor.fetchall()

        # Credit usage statistics
        cursor.execute("""
            SELECT 
                SUM(requested_credits) AS total_credits_used,
                AVG(requested_credits) AS avg_credits_used,
                SUM(CASE WHEN status = 'approved' THEN requested_credits ELSE 0 END) AS approved_credits,
                SUM(CASE WHEN status = 'pending' THEN requested_credits ELSE 0 END) AS pending_credits
            FROM credit_requests;
        """)
        credit_stats = cursor.fetchone()

        # Combine all analytics data
        analytics_data = {
            'scans_per_user': scans_per_user,
            'common_topics': common_topics,
            'top_users': top_users,
            'credit_stats': credit_stats
        }

        return jsonify(analytics_data), 200
    except sqlite3.Error as e:
        return jsonify({'message': 'Failed to fetch analytics data', 'error': str(e)}), 500
    finally:
        conn.close()

if __name__ == '__main__':
   app.run(debug=True)