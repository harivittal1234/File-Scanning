document.addEventListener('DOMContentLoaded', function() {
    const loginForm = document.getElementById('loginForm');
    const loginStatus = document.getElementById('loginStatus');

    loginForm.addEventListener('submit', function(event) {
        event.preventDefault(); // Prevent default form submission

        const username = document.getElementById('username').value;
        const password = document.getElementById('password').value;

        loginStatus.textContent = 'Logging in...';
        loginStatus.className = 'status-message'; // Reset to default style

        const formData = new URLSearchParams(); // Or FormData, depends on backend expectation
        formData.append('username', username);
        formData.append('password', password);

        fetch('/auth/login', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json', // Or 'application/json' if backend expects JSON
            },
            body: JSON.stringify({username: username, password: password}) // Or JSON.stringify({username: username, password: password}) if backend expects JSON
        })
        .then(response => {
            if (response.ok) {
                loginStatus.textContent = 'Login successful! Redirecting...';
                loginStatus.className = 'status-message success';
                // Redirect to the main document scanner page after successful login
                window.location.href = '/'; // Or '/scan' or wherever your main page is
            } else {
                return response.json().then(errorData => { // Try to parse JSON error response
                    loginStatus.textContent = 'Login failed: ' + (errorData.message || 'Invalid username or password.');
                    loginStatus.className = 'status-message error';
                });
            }
        })
        .catch(error => {
            loginStatus.textContent = 'Login failed: Network error.';
            loginStatus.className = 'status-message error';
            console.error('Login error:', error);
        });
    });
});