document.addEventListener('DOMContentLoaded', function () {
    document.querySelectorAll('[data-password-toggle]').forEach(function (button) {
        button.addEventListener('click', function () {
            const targetId = button.getAttribute('data-password-toggle');
            const input = document.getElementById(targetId);
            if (!input) return;

            const isPassword = input.getAttribute('type') === 'password';
            input.setAttribute('type', isPassword ? 'text' : 'password');
            button.setAttribute('aria-label', isPassword ? 'Hide password' : 'Show password');
            button.textContent = isPassword ? '🙈' : '👁';
        });
    });

    window.addEventListener('scroll', function () {
        const nav = document.querySelector('.navbar');
        if (!nav) return;
        nav.classList.toggle('scrolled', window.scrollY > 20);
    });
});
