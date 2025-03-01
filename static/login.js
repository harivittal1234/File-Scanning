document.addEventListener('DOMContentLoaded', function() {
    const loginForm = document.getElementById('loginForm');
    const loginStatus = document.getElementById('loginStatus');

    loginForm.addEventListener('submit', function(event) {
        event.preventDefault(); // Prevent default form submission

        const username = document.getElementById('username').value;
        const password = document.getElementById('password').value;

        loginStatus.textContent = 'Logging in...';
        loginStatus.className = 'status-message'; // Reset to default style

        fetch('/auth/login', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ username, password }),
        })
        .then(response => {
            if (!response.ok) {
                return response.json().then(errorData => {
                    throw new Error(errorData.message || 'Login failed');
                });
            }
            return response.json();
        })
        .then(data => {
            loginStatus.textContent = 'Login successful! Redirecting...';
            loginStatus.className = 'status-message success';

            // Check the user's role and redirect accordingly
            if (data.role === 'admin') {
                window.location.href = '/admin/dashboard'; // Redirect to Admin Dashboard
            } else {
                window.location.href = '/'; // Redirect to regular user interface
            }
        })
        .catch(error => {
            loginStatus.textContent = 'Login failed: ' + error.message;
            loginStatus.className = 'status-message error';
            console.error('Login error:', error);
        });
    });
});