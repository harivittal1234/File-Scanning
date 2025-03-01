document.addEventListener('DOMContentLoaded', function() {
    const documentUpload = document.getElementById('documentUpload');
    const scanButton = document.getElementById('scanButton');
    const uploadStatus = document.getElementById('uploadStatus');
    const scanResultsContainer = document.getElementById('scan-results-container');
    const documentTypeResult = document.getElementById('document-type-result');
    const contentSnippetResult = document.getElementById('content-snippet-result');
    const processingStatusResult = document.getElementById('processing-status-result');
    const scanFilenameResult = document.getElementById('scan-filename-result');
    const scanFilepathResult = document.getElementById('scan-filepath-result');
    const documentIdResult = document.getElementById('document-id-result');
    const matchesContainer = document.getElementById('matches-container');
    const matchesList = document.getElementById('matches-list');
    const authButton = document.getElementById('authButton');
    const userProfileSection = document.getElementById('userProfileSection');
    const userProfileContent = document.getElementById('userProfileContent');

    // Function to fetch and display user profile
    function fetchUserProfile() {
        fetch('/user/profile', {
            method: 'GET',
            credentials: 'include'
        })
        .then(response => {
            if (response.status === 401) {
                // User is not logged in
                userProfileContent.innerHTML = `
                    <p style="color: #666;">You are not logged in. <a href="/login">Log in</a> or <a href="/register">register</a> to access your profile.</p>
                `;
                authButton.textContent = 'Login';
                authButton.onclick = () => {
                    window.location.href = '/login';
                };
                throw new Error('Unauthorized');
            }
            if (!response.ok) {
                throw new Error('Failed to fetch user profile');
            }
            return response.json();
        })
        .then(data => {
            // User is logged in
            userProfileContent.innerHTML = `
                <p><strong>Username:</strong> <span id="username">${data.username}</span></p>
                <p><strong>Credits:</strong> <span id="credits">${data.credits}</span></p>
                <p><strong>Role:</strong> <span id="role">${data.role}</span></p>
            `;
            authButton.textContent = 'Logout';
            authButton.onclick = () => {
                fetch('/auth/logout', {
                    method: 'POST',
                    credentials: 'include'
                })
                .then(response => {
                    if (response.ok) {
                        window.location.href = '/';
                    }
                })
                .catch(error => {
                    console.error('Error during logout:', error);
                });
            };
        })
        .catch(error => {
            console.error('Error fetching user profile:', error);
        });
    }

    // Fetch user profile when the page loads
    fetchUserProfile();

    // Scan Button Functionality
    scanButton.addEventListener('click', function() {
        const file = documentUpload.files[0];
        if (file) {
            uploadStatus.textContent = 'Uploading and scanning...';
            uploadStatus.style.color = 'orange';
            scanResultsContainer.style.display = 'none';
            matchesList.innerHTML = ''; // Clear previous matches

            const formData = new FormData();
            formData.append('document', file);

            fetch('/scan', {
                method: 'POST',
                body: formData,
                credentials: 'include'
            })
            .then(response => {
                if (response.status === 401) {
                    response.json().then(errorData => {
                        const errorMessage = errorData.message;
                        alert(errorMessage);
                        window.location.href = '/login';
                        uploadStatus.textContent = 'Scan request unauthorized. Redirecting to login...';
                        uploadStatus.style.color = 'red';
                        return;
                    });
                }
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                uploadStatus.textContent = 'Scan completed successfully!';
                uploadStatus.style.color = 'green';
                console.log('Scan results:', data);

                // Display Scan Results
                documentTypeResult.textContent = data.scan_results.document_type;
                contentSnippetResult.textContent = data.scan_results.content_snippet;
                processingStatusResult.textContent = data.scan_results.processing_status;
                scanFilenameResult.textContent = data.filename;
                scanFilepathResult.textContent = data.filepath;
                documentIdResult.textContent = data.document_id;

                // Display Best Match
                document.getElementById('best-match-document-id-result').textContent = data.scan_results.best_match_document_id;
                document.getElementById('best-match-similarity-score-result').textContent = data.scan_results.best_match_similarity_score;

                // Display "View All Matches" Button
                if (data.scan_results.best_match_document_id !== "No Match Found") {
                    const viewMatchesBtn = document.createElement('button');
                    viewMatchesBtn.textContent = 'View All Matches';
                    viewMatchesBtn.style.marginTop = '10px';
                    viewMatchesBtn.addEventListener('click', () => {
                        fetch(`/matches/${data.document_id}`)
                            .then(response => response.json())
                            .then(matchesData => {
                                matchesList.innerHTML = ''; // Clear previous matches
                                matchesData.matches.forEach(match => {
                                    const matchItem = document.createElement('div');
                                    matchItem.className = 'match-item';
                                    matchItem.innerHTML = `
                                        ${match.filename} 
                                        <span>${match.similarity_score}% match</span>
                                    `;
                                    matchesList.appendChild(matchItem);
                                });
                            })
                            .catch(error => {
                                console.error('Error fetching matches:', error);
                                matchesList.innerHTML = '<p style="color: red;">Error loading matches. Please try again.</p>';
                            });
                    });

                    matchesContainer.appendChild(viewMatchesBtn);
                }

                scanResultsContainer.style.display = 'block';
            })
            .catch(error => {
                uploadStatus.textContent = 'Scan failed!';
                uploadStatus.style.color = 'red';
                console.error('Error during scan:', error);
                uploadStatus.textContent = 'Error during scan: ' + error.message;
            });
        } else {
            uploadStatus.textContent = 'Please select a document to upload.';
            uploadStatus.style.color = 'red';
        }
    });

    // Credit Request Form
    document.getElementById('creditRequestForm').addEventListener('submit', function(event) {
        event.preventDefault(); // Prevent the form from submitting the traditional way

        // Get the requested credits from the form
        const requestedCredits = document.getElementById('requestedCredits').value;

        // Send the request to the backend
        fetch('/credits/request', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            credentials: 'include', // Include cookies for session management
            body: JSON.stringify({ requested_credits: requestedCredits }),
        })
        .then(response => response.json())
        .then(data => {
            // Display the response message
            const statusDiv = document.getElementById('creditRequestStatus');
            statusDiv.textContent = data.message;
            statusDiv.className = 'status-message success';
        })
        .catch(error => {
            // Handle errors
            const statusDiv = document.getElementById('creditRequestStatus');
            statusDiv.textContent = 'Failed to submit credit request: ' + error.message;
            statusDiv.className = 'status-message error';
        });
    });
});