document.addEventListener('DOMContentLoaded', function() {
    const registerForm = document.getElementById('registerForm');
    const registerStatus = document.getElementById('registerStatus');

    registerForm.addEventListener('submit', function(event) {
        event.preventDefault();

        const username = document.getElementById('username').value;
        const password = document.getElementById('password').value;

        fetch('/auth/register', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ username, password }),
        })
        .then(response => {
            if (response.ok) {
                return response.json();
            } else {
                return response.json().then(errorData => {
                    throw new Error(errorData.message || 'Registration failed');
                });
            }
        })
        .then(data => {
            registerStatus.textContent = 'Registration successful! Redirecting to login...';
            registerStatus.className = 'status-message success';
            setTimeout(() => {
                window.location.href = '/login';
            }, 2000);
        })
        .catch(error => {
            registerStatus.textContent = error.message;
            registerStatus.className = 'status-message error';
        });
    });
});