// Universal Menu & Navigation Script

document.addEventListener('DOMContentLoaded', function() {
  // Burger Menu Toggle
  const burgerBtn = document.querySelector('.burger-menu');
  
  // Пробуем найти меню по разным селекторам
  let navMenu = document.querySelector('.nav-links');
  if (!navMenu) navMenu = document.querySelector('.nav-menu');
  if (!navMenu) navMenu = document.querySelector('.menu');
  if (!navMenu) navMenu = document.querySelector('nav ul');
  
  if (burgerBtn) {
    burgerBtn.addEventListener('click', function(e) {
      e.stopPropagation();
      
      // Если есть portfolioMenu (на странице калькулятора), открываем его
      if (typeof portfolioMenu !== 'undefined' && portfolioMenu) {
        portfolioMenu.open();
        return;
      }
      
      // Иначе обычное меню
      this.classList.toggle('active');
      
      if (navMenu) {
        navMenu.classList.toggle('active');
      }
    });
  }
  
  // Close menu when clicking outside
  document.addEventListener('click', function(e) {
    if (burgerBtn && navMenu) {
      if (!burgerBtn.contains(e.target) && !navMenu.contains(e.target)) {
        burgerBtn.classList.remove('active');
        navMenu.classList.remove('active');
      }
    }
  });
  
  // Close menu when clicking on a link
  if (navMenu) {
    const navLinks = navMenu.querySelectorAll('a');
    navLinks.forEach(link => {
      link.addEventListener('click', function() {
        if (burgerBtn) burgerBtn.classList.remove('active');
        navMenu.classList.remove('active');
      });
    });
  }
  
  // Smooth scroll for anchor links
  document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
      const href = this.getAttribute('href');
      if (href !== '#' && href !== '') {
        const target = document.querySelector(href);
        if (target) {
          e.preventDefault();
          target.scrollIntoView({
            behavior: 'smooth',
            block: 'start'
          });
        }
      }
    });
  });
});
