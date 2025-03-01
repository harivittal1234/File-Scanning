document.addEventListener('DOMContentLoaded', function() {
    const logoutButton = document.getElementById('logoutButton');
    const pendingRequestsTableBody = document.querySelector('#pendingRequestsTable tbody');
    const scansPerUserChartCtx = document.getElementById('scansPerUserChart').getContext('2d');
    const commonTopicsChartCtx = document.getElementById('commonTopicsChart').getContext('2d');
    const topUsersTableBody = document.querySelector('#topUsersTable tbody');
    const creditStatsDiv = document.getElementById('creditStats');

    // Logout Button
    logoutButton.addEventListener('click', () => {
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
    });

    // Fetch and display pending credit requests
    function loadPendingRequests() {
        fetch('/admin/credit-requests', {
            credentials: 'include'
        })
        .then(response => response.json())
        .then(data => {
            pendingRequestsTableBody.innerHTML = ''; // Clear previous rows

            data.forEach(request => {
                const row = document.createElement('tr');
                row.innerHTML = `
                    <td>${request.username}</td>
                    <td>${request.requested_credits}</td>
                    <td>${new Date(request.request_date).toLocaleString()}</td>
                    <td>
                        <button class="approve" onclick="approveRequest(${request.id})">Approve</button>
                        <button class="reject" onclick="rejectRequest(${request.id})">Reject</button>
                    </td>
                `;
                pendingRequestsTableBody.appendChild(row);
            });
        })
        .catch(error => {
            console.error('Error fetching pending requests:', error);
        });
    }

    // Approve a credit request
    window.approveRequest = function(requestId) {
        fetch(`/admin/credit-requests/${requestId}/approve`, {
            method: 'POST',
            credentials: 'include'
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Failed to approve request');
            }
            return response.json();
        })
        .then(data => {
            alert(data.message);
            loadPendingRequests(); // Refresh the list
        })
        .catch(error => {
            console.error('Error approving request:', error);
            alert('Failed to approve request: ' + error.message);
        });
    };

    // Reject a credit request
    window.rejectRequest = function(requestId) {
        fetch(`/admin/credit-requests/${requestId}/reject`, {
            method: 'POST',
            credentials: 'include'
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Failed to reject request');
            }
            return response.json();
        })
        .then(data => {
            alert(data.message);
            loadPendingRequests(); // Refresh the list
        })
        .catch(error => {
            console.error('Error rejecting request:', error);
            alert('Failed to reject request: ' + error.message);
        });
    };

    // Fetch and display analytics
    function loadAnalytics() {
        fetch('/admin/analytics', {
            credentials: 'include'
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Failed to fetch analytics data');
            }
            return response.json();
        })
        .then(data => {
            // Scans Per User Per Day
            const scansLabels = data.scans_per_user.map(item => `${item.username} - ${item.scan_day}`);
            const scansData = data.scans_per_user.map(item => item.scan_count);
            new Chart(scansPerUserChartCtx, {
                type: 'bar',
                data: {
                    labels: scansLabels,
                    datasets: [{
                        label: 'Scans Per User Per Day',
                        data: scansData,
                        backgroundColor: 'rgba(54, 162, 235, 0.2)',
                        borderColor: 'rgba(54, 162, 235, 1)',
                        borderWidth: 1
                    }]
                },
                options: {
                    scales: {
                        y: {
                            beginAtZero: true
                        }
                    }
                }
            });
    
            // Most Common Scanned Document Topics
            const topicsLabels = data.common_topics.map(item => item.topic);
            const topicsData = data.common_topics.map(item => item.scan_count);
            new Chart(commonTopicsChartCtx, {
                type: 'pie',
                data: {
                    labels: topicsLabels,
                    datasets: [{
                        label: 'Most Common Topics',
                        data: topicsData,
                        backgroundColor: [
                            'rgba(255, 99, 132, 0.2)',
                            'rgba(54, 162, 235, 0.2)',
                            'rgba(255, 206, 86, 0.2)',
                            'rgba(75, 192, 192, 0.2)',
                            'rgba(153, 102, 255, 0.2)'
                        ],
                        borderColor: [
                            'rgba(255, 99, 132, 1)',
                            'rgba(54, 162, 235, 1)',
                            'rgba(255, 206, 86, 1)',
                            'rgba(75, 192, 192, 1)',
                            'rgba(153, 102, 255, 1)'
                        ],
                        borderWidth: 1
                    }]
                }
            });
    
            // Top Users by Scans and Credit Usage
            data.top_users.forEach(user => {
                const row = document.createElement('tr');
                row.innerHTML = `
                    <td>${user.username}</td>
                    <td>${user.total_scans}</td>
                    <td>${user.total_credits_used}</td>
                `;
                topUsersTableBody.appendChild(row);
            });
    
            // Credit Usage Statistics
            creditStatsDiv.innerHTML = `
                <p><strong>Total Credits Used:</strong> ${data.credit_stats.total_credits_used}</p>
                <p><strong>Average Credits Used:</strong> ${data.credit_stats.avg_credits_used.toFixed(2)}</p>
                <p><strong>Approved Credits:</strong> ${data.credit_stats.approved_credits}</p>
                <p><strong>Pending Credits:</strong> ${data.credit_stats.pending_credits}</p>
            `;
        })
        .catch(error => {
            console.error('Error fetching analytics:', error);
            creditStatsDiv.innerHTML = `<p style="color: red;">Error loading analytics: ${error.message}</p>`;
        });
    }

    // Load data when the page loads
    loadPendingRequests();
    loadAnalytics();
});