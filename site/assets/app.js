// Filtrage par catégorie
document.querySelectorAll('.filter-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    const cat = btn.dataset.cat;

    // Toggle actif
    document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');

    // Affiche / masque les cartes
    document.querySelectorAll('.bento-card').forEach(card => {
      if (cat === 'all' || card.dataset.cat === cat) {
        card.style.display = '';
        card.style.animation = 'fadeInUp 0.3s ease both';
      } else {
        card.style.display = 'none';
      }
    });
  });
});
