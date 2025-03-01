from flask import Flask, request, jsonify, session, render_template #We are adding session from Flask because we'll use Flask's built-in session management to keep users logged in after successful login. We are also adding render_template because we will need to serve the login.html file later.
import sqlite3
from werkzeug.utils import secure_filename
from models import User, Document
from db import get_db_connection 
from functools import wraps # Import wraps for decorator best practices
import re

app = Flask(__name__)
app.config['SECRET_KEY'] = 'qwerty1234'  # this should be a long random string

###FRONTEND ROUTES
@app.route('/')
def home():
    return render_template("index.html")

@app.route('/login')
def login_page():
    return render_template('login.html') # Serve login.html template


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
        return jsonify({'message': 'Invalid username'}), 401 # 401 Unauthorized

    if not user.check_password(password):
        return jsonify({'message': 'Invalid password'}), 401 # 401 Unauthorized

    session['user_id'] = user.id  # Store user ID in session
    session['user_role'] = user.role # Store user role in session - NEW LINE!
    return jsonify({'message': 'Login successful'}), 200 # 200 OK

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



#Preprocessing Text
def preprocess_text(text):
    """
    Preprocesses text by converting to lowercase, removing punctuation, and splitting into words.

    Args:
        text: The input text string.

    Returns:
        A list of preprocessed words.
    """
    text = text.lower() # Convert text to lowercase
    text = re.sub(r'[^\w\s]', '', text) # Remove punctuation using regular expressions - keep only alphanumeric and whitespace
    words = text.split() # Split text into words (by whitespace)
    return words

#Word Frequency Calculation
def calculate_word_frequencies(word_list):
    """
    Calculates word frequencies from a list of words.

    Args:
        word_list: A list of words (strings).

    Returns:
        A dictionary where keys are unique words and values are their frequencies (counts).
    """
    word_counts = {} # Initialize an empty dictionary to store word counts
    for word in word_list: # Iterate through each word in the input list
        if word in word_counts: # Check if the word is already in the dictionary
            word_counts[word] += 1 # If yes, increment the count
        else:
            word_counts[word] = 1 # If no, add the word to the dictionary with a count of 1
    return word_counts


#Scan endpoint
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg'} # Or similar set of allowed extensions

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# Example Stored Documents (for testing)
STORED_DOCUMENTS = [
    "This is the first stored document about topic A. It discusses topic A in detail.",
    "The second document is also about topic A, but it has a different perspective.",
    "Document number three is on topic B and is unrelated to topic A.",
    "This fourth document is again about topic A, providing more examples."
]

# Preprocess STORED_DOCUMENTS and calculate word frequencies
STORED_DOCUMENT_FREQUENCIES = {}
for i, doc_text in enumerate(STORED_DOCUMENTS):
    preprocessed_doc = preprocess_text(doc_text) # Preprocess stored document text
    frequencies = calculate_word_frequencies(preprocessed_doc) # Calculate word frequencies
    STORED_DOCUMENT_FREQUENCIES[f"doc_{i+1}"] = frequencies # Store frequencies in dictionary, key like "doc_1", "doc_2", etc.


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



@app.route('/scan', methods=['POST']) # expects requests with Content-Type: multipart/form-data
@role_required('user')
def scan_document():

        # --- Credit Deduction Logic will go here ---
        user_id = session.get('user_id')  # User ID is already retrieved
        user = User.get_user_by_id(user_id)  # Fetch user object

        if not user:
            return jsonify({'message': 'User not found'}), 404  # Safety check - should not happen

        if user.total_credits <= 0:
            return jsonify({'message': 'Insufficient credits'}), 402  # 402 Payment Required - Insufficient credits

        User.decrement_credits(user_id)  # Call new method to decrement credits by 1

        
        # --- Document Upload Handling will go here ---
        if 'document' not in request.files:
            return jsonify({'message': 'No document part'}), 400  # 400 Bad Request if no file part

        file = request.files['document']  # Get the uploaded file

        if file.filename == '':
            return jsonify({'message': 'No selected file'}), 400  # 400 Bad Request if no file selected

        if file and allowed_file(file.filename):  # If file is present and has a filename
            filename = secure_filename(file.filename)  # Get original filename (for now, we'll just use it)
            # --- "Scan" Processing (Placeholder) will go here ---
            # For now, just save the uploaded file to a temporary location (for testing)
            upload_folder = 'uploads'  # Define a folder to save uploads
            import os  # Import os module for file system operations
            os.makedirs(upload_folder, exist_ok=True)  # Create the folder if it doesn't exist
            filepath = os.path.join(upload_folder, filename)  # Construct file path
            file.save(filepath)  # Save the uploaded file to the server

            # --- "Scan" Processing (Replace Placeholder with File Content Reading) ---
            scan_results = {}  # Initialize an empty dictionary to store scan results
            file_extension = filename.rsplit('.', 1)[1].lower()
            if file_extension == 'txt':
                document_type = "Text Document"
                try:
                    with open(filepath, 'r') as f:
                        uploaded_document_content = f.read()
                    preprocessed_words = preprocess_text(uploaded_document_content)

                    word_frequency_counts = calculate_word_frequencies(preprocessed_words)  # Calculate word frequencies
                    content_snippet = uploaded_document_content[:200] + "..." if len(uploaded_document_content) > 200 else uploaded_document_content

                    # --- Document Similarity Calculation ---
                    document_similarities = {}  # Dictionary to store similarity scores for each stored document
                    for doc_id, stored_doc_frequencies in STORED_DOCUMENT_FREQUENCIES.items():  # Iterate through stored documents and their frequencies
                        similarity_score = calculate_word_overlap_similarity(word_frequency_counts, stored_doc_frequencies)  # Calculate similarity
                        document_similarities[doc_id] = similarity_score  # Store score

                    best_match_doc_id = "No Match Found"  # Default if no match
                    max_similarity_score = 0
                    for doc_id, score in document_similarities.items():  # Find document with highest similarity score
                        if score > max_similarity_score:
                            max_similarity_score = score
                            best_match_doc_id = doc_id

                    processing_status = "Text Content Extracted, Preprocessed, and Word Frequencies calculated, Similarity Matched (Word Overlap)"  # Update processing status message

                    scan_results['document_type'] = document_type
                    scan_results['content_snippet'] = content_snippet
                    scan_results['processing_status'] = processing_status
                    scan_results['uploaded_document_content'] = uploaded_document_content
                    scan_results['preprocessed_words'] = preprocessed_words
                    scan_results['word_frequency_counts'] = word_frequency_counts
                    scan_results['document_similarities'] = document_similarities
                    scan_results['best_match_document_id'] = best_match_doc_id
                    scan_results['best_match_similarity_score'] = max_similarity_score



                except Exception as e:
                    document_type = "Text Document (Error Reading Content)"
                    content_snippet = "Error reading document content."
                    processing_status = f"Error: {str(e)}"
                    uploaded_document_content = "Error reading file content"
                    preprocessed_words = []  # Initialize preprocessed_words to empty list in case of error
                    word_frequency_counts = {}
                    document_similarities = {}  # Initialize for error case
                    best_match_doc_id = "N/A" # Initialize for error case
                    max_similarity_score = 0 # Initialize for error case


            else:  # For non-text files (binary files)
                document_type = "Binary Document (Content Preview Unavailable)"
                content_snippet = "N/A - Binary file, cannot preview text content"
                processing_status = "Binary File - Content Extraction Skipped"
                uploaded_document_content = "Binary File - Content N/A"  # Or handle differently
                preprocessed_words = [] # Initialize preprocessed_words to empty list for non-text files
                word_frequency_counts = {}
                document_similarities = {}  # Initialize for non-text files
                best_match_doc_id = "N/A"  # Initialize for non-text files
                max_similarity_score = 0  # Initialize for non-text files

                scan_results['document_type'] = "Binary Document (Content Preview Unavailable)"
                scan_results['content_snippet'] = content_snippet
                scan_results['processing_status'] = processing_status
                scan_results['uploaded_document_content'] = uploaded_document_content
                scan_results['preprocessed_words'] = preprocessed_words
                scan_results['word_frequency_counts'] = word_frequency_counts
                scan_results['document_similarities'] = document_similarities
                scan_results['best_match_document_id'] = best_match_doc_id
                scan_results['best_match_similarity_score'] = max_similarity_score



            scan_results['filename'] = filename  # Add filename to scan results
            scan_results['filepath'] = filepath  # Add filepath to scan results (can be useful for debugging/logging)
            # scan_results['processing_status'] = 'Placeholder Scan Processing Simulated' # REMOVED - using real status now

        # --- Document Metadata Storage ---
            document = Document(filename=filename, filepath=filepath, user_id=user_id)  # Create Document object
            if document.save():  # Save document metadata to database
                return jsonify({
                    'message': 'Scan request received, credit deducted, document uploaded, metadata saved, text content extracted',  # Updated message
                    'filename': filename,
                    'filepath': filepath,
                    'document_id': document.id,  # Include the database-generated document ID in the response
                    'scan_results': scan_results  # Include the  scan results in the response
                }), 200
            else:
                return jsonify({'message': 'Error saving document metadata to database'}), 500  # 500 error if metadata save fails

        else:
            return jsonify({'message': 'Error uploading document'}), 500

if __name__ == '__main__':
    app.run(debug=True) #debug=True for development, remove in production