// RentCheck Tanzania - Main JavaScript

document.addEventListener('DOMContentLoaded', function () {
    // Universal Password Visibility Toggle
    document.addEventListener('click', function (e) {
        var btn = e.target.closest('.toggle-password-btn');
        if (!btn) return;
        e.preventDefault();

        var targetId = btn.getAttribute('data-target');
        var input = targetId
            ? document.getElementById(targetId)
            : (btn.closest('.input-group') ? btn.closest('.input-group').querySelector('input') : null);
        if (!input) return;

        var icon = btn.querySelector('i');
        if (input.type === 'password') {
            input.type = 'text';
            if (icon) {
                icon.classList.remove('bi-eye');
                icon.classList.add('bi-eye-slash');
            }
            btn.setAttribute('aria-label', 'Hide password');
            btn.setAttribute('title', 'Hide password');
        } else {
            input.type = 'password';
            if (icon) {
                icon.classList.remove('bi-eye-slash');
                icon.classList.add('bi-eye');
            }
            btn.setAttribute('aria-label', 'Show password');
            btn.setAttribute('title', 'Show password');
        }
    });
});
