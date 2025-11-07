function showScreen(screenId, clickedButton) {
    if (!screenId || !clickedButton) return;

    document.querySelector('.screen.active').classList.remove('active');
    document.getElementById(screenId).classList.add('active');

    document.querySelector('.header-buttons .button.active').classList.remove('active');
    clickedButton.classList.add('active');
}

//авторасширение для textarea
document.querySelectorAll('.auto-expand').forEach(function(textarea) {
    textarea.addEventListener('input', function() {
        this.style.height = 'auto';
        this.style.height = Math.min(this.scrollHeight, 200) + 'px'; //this.scrollHeight - реальная высота всех строк
    });
});


