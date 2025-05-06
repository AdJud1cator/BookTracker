// Dark mode toggle script
document.addEventListener('DOMContentLoaded', () => {
    const html = document.documentElement;
    const toggleLink = document.getElementById('darkModeToggleLink');
    const status = document.getElementById('darkModeStatus');
    const savedTheme = localStorage.getItem('bsTheme') || 'light';
    html.setAttribute('data-bs-theme', savedTheme);
    status.textContent = savedTheme === 'dark' ? 'Light Mode' : 'Dark Mode';
    toggleLink.addEventListener('click', e => {
        e.preventDefault();
        const currentTheme = html.getAttribute('data-bs-theme');
        if (currentTheme === 'dark') {
            html.setAttribute('data-bs-theme', 'light');
            localStorage.setItem('bsTheme', 'light');
            status.textContent = 'Dark Mode';
        } else {
            html.setAttribute('data-bs-theme', 'dark');
            localStorage.setItem('bsTheme', 'dark');
            status.textContent = 'Light Mode';
        }
    });
});