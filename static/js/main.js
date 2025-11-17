// ==================== CREDIT SCORE SLIDER ====================
function updateCreditValue(value) {
    const creditValueElement = document.getElementById('creditValue');
    if (creditValueElement) {
        creditValueElement.textContent = value;
        
        // Update color based on score
        const score = parseInt(value);
        if (score >= 800) {
            creditValueElement.style.background = 'linear-gradient(135deg, #10b981, #059669)';
        } else if (score >= 650) {
            creditValueElement.style.background = 'linear-gradient(135deg, #f59e0b, #d97706)';
        } else {
            creditValueElement.style.background = 'linear-gradient(135deg, #ef4444, #dc2626)';
        }
    }
}

function convertCreditValue() {
    const creditSlider = document.getElementById('creditSlider');
    const creditInput = document.getElementById('credit');
    
    if (creditSlider && creditInput) {
        const creditScore = parseInt(creditSlider.value);
        const creditBinary = (creditScore >= 800 && creditScore <= 1000) ? 1 : 0;
        creditInput.value = creditBinary;
    }
}

// ==================== FORM VALIDATION ====================
function validateForm(formId) {
    const form = document.getElementById(formId);
    if (!form) return true;
    
    const inputs = form.querySelectorAll('input[required], select[required]');
    let isValid = true;
    
    inputs.forEach(input => {
        if (!input.value.trim()) {
            input.style.borderColor = '#ef4444';
            isValid = false;
        } else {
            input.style.borderColor = '#e2e8f0';
        }
    });
    
    return isValid;
}

// ==================== PASSWORD STRENGTH CHECKER ====================
function checkPasswordStrength(password) {
    let strength = 0;
    if (password.length >= 8) strength++;
    if (password.match(/[a-z]+/)) strength++;
    if (password.match(/[A-Z]+/)) strength++;
    if (password.match(/[0-9]+/)) strength++;
    if (password.match(/[$@#&!]+/)) strength++;
    
    return strength;
}

function updatePasswordStrength(inputId, indicatorId) {
    const input = document.getElementById(inputId);
    const indicator = document.getElementById(indicatorId);
    
    if (input && indicator) {
        input.addEventListener('input', function() {
            const strength = checkPasswordStrength(this.value);
            const strengthText = ['Very Weak', 'Weak', 'Fair', 'Good', 'Strong'];
            const strengthColors = ['#ef4444', '#f59e0b', '#eab308', '#84cc16', '#10b981'];
            
            indicator.textContent = strengthText[strength - 1] || 'Very Weak';
            indicator.style.color = strengthColors[strength - 1] || '#ef4444';
        });
    }
}

// ==================== AUTO-HIDE ALERTS ====================
setTimeout(() => {
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        alert.style.animation = 'fadeOut 0.5s ease';
        setTimeout(() => alert.remove(), 500);
    });
}, 5000);

// ==================== SMOOTH SCROLL ====================
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        e.preventDefault();
        const target = document.querySelector(this.getAttribute('href'));
        if (target) {
            target.scrollIntoView({
                behavior: 'smooth',
                block: 'start'
            });
        }
    });
});


// ==================== PROFILE PAGE - SHOW DETAILS ====================
function showDetails(index) {
    var details = document.getElementById('details' + index);
    if (details) {
        if (details.style.display === 'none' || details.style.display === '') {
            details.style.display = 'table-row';
        } else {
            details.style.display = 'none';
        }
    }
}
