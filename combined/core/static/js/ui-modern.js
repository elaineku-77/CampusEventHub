document.addEventListener('DOMContentLoaded', function () {
    const navbar = document.querySelector('.ceh-navbar');
    if (navbar) {
        const onScroll = () => navbar.classList.toggle('ceh-scrolled', window.scrollY > 8);
        onScroll();
        window.addEventListener('scroll', onScroll);
    }

    document.querySelectorAll('.ceh-auto-dismiss').forEach((el) => {
        setTimeout(() => {
            if (window.bootstrap) {
                const alert = bootstrap.Alert.getOrCreateInstance(el);
                alert.close();
            }
        }, 4500);
    });

    document.querySelectorAll('.ceh-card-hover').forEach((card) => {
        card.addEventListener('mousemove', (e) => {
            const rect = card.getBoundingClientRect();
            const x = e.clientX - rect.left;
            const y = e.clientY - rect.top;
            card.style.setProperty('--mx', `${x}px`);
            card.style.setProperty('--my', `${y}px`);
        });
    });
});
