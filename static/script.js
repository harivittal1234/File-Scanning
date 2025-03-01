document.addEventListener('DOMContentLoaded', function() {
    const documentUpload = document.getElementById('documentUpload');
    const scanButton = document.getElementById('scanButton');
    const uploadStatus = document.getElementById('uploadStatus');
    const scanResultsContainer = document.getElementById('scan-results-container');
    const documentTypeResult = document.getElementById('document-type-result'); // Get references to result display elements
    const contentSnippetResult = document.getElementById('content-snippet-result');
    const processingStatusResult = document.getElementById('processing-status-result');
    const scanFilenameResult = document.getElementById('scan-filename-result');
    const scanFilepathResult = document.getElementById('scan-filepath-result');
    const documentIdResult = document.getElementById('document-id-result');


    scanButton.addEventListener('click', function() {
        const file = documentUpload.files[0];
        if (file) {
            uploadStatus.textContent = 'Uploading and scanning...';
            uploadStatus.style.color = 'orange';
            scanResultsContainer.style.display = 'none'; // Hide previous results

            const formData = new FormData(); // Create FormData object to send file
            formData.append('document', file); // Append the file to FormData

            fetch('/scan', { // Send POST request to /scan endpoint
                method: 'POST',
                body: formData, // Set FormData as the request body
                credentials: 'include' // Include cookies in the request
            })
            .then(response => {
                if (response.status === 401) {
                    response.json().then(errorData => {
                        const errorMessage = errorData.message;
                        alert(errorMessage);
                        window.location.href = '/login'; // *** ADD THIS LINE: Redirect to /login ***
                        uploadStatus.textContent = 'Scan request unauthorized. Redirecting to login...'; // Optional status update
                        uploadStatus.style.color = 'red';
                        return;
                    });
                }        
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                return response.json(); // Parse response as JSON
            })
            .then(data => { // Handle successful JSON response
                uploadStatus.textContent = 'Scan completed successfully!';
    uploadStatus.style.color = 'green';
    console.log('Scan results:', data); // Log the response data to browser console (for debugging)

    // Display Scan Results on webpage
    documentTypeResult.textContent = data.scan_results.document_type;
    contentSnippetResult.textContent = data.scan_results.content_snippet;
    processingStatusResult.textContent = data.scan_results.processing_status;
    scanFilenameResult.textContent = data.filename; // Display original filename from response
    scanFilepathResult.textContent = data.filepath; // Display server filepath from response
    documentIdResult.textContent = data.document_id; // Display document ID from response

    // --- INSERT THESE NEW LINES HERE to display similarity results ---
    document.getElementById('best-match-document-id-result').textContent = data.scan_results.best_match_document_id;
    document.getElementById('best-match-similarity-score-result').textContent = data.scan_results.best_match_similarity_score;
    // --- END OF NEW LINES ---

    scanResultsContainer.style.display = 'block';

            })
            .catch(error => { // Handle errors during fetch or processing
                uploadStatus.textContent = 'Scan failed!';
                uploadStatus.style.color = 'red';
                console.error('Error during scan:', error);
                uploadStatus.textContent = 'Error during scan: ' + error.message; // Show error message to user
            });

        } else {
            uploadStatus.textContent = 'Please select a document to upload.';
            uploadStatus.style.color = 'red';
        }
    });
});