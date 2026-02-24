// ===================================================
//  VALLI TRADING LIMITED — Main JS
// ===================================================

/* --- Navbar scroll behaviour --- */
const navbar = document.getElementById('navbar');
window.addEventListener('scroll', () => {
  if (window.scrollY > 60) {
    navbar.classList.add('scrolled');
  } else {
    navbar.classList.remove('scrolled');
  }
}, { passive: true });

/* --- Hamburger menu --- */
const hamburger = document.getElementById('hamburger');
const navLinks  = document.querySelector('.nav-links');

hamburger.addEventListener('click', () => {
  hamburger.classList.toggle('open');
  navLinks.classList.toggle('open');
});

// Close menu on link click
navLinks.querySelectorAll('a').forEach(link => {
  link.addEventListener('click', () => {
    hamburger.classList.remove('open');
    navLinks.classList.remove('open');
  });
});

/* --- Smooth active link highlighting --- */
const sections = document.querySelectorAll('section[id]');
window.addEventListener('scroll', () => {
  const scrollPos = window.scrollY + 120;
  sections.forEach(section => {
    if (
      scrollPos >= section.offsetTop &&
      scrollPos < section.offsetTop + section.offsetHeight
    ) {
      navLinks.querySelectorAll('a').forEach(a => a.classList.remove('active'));
      const active = navLinks.querySelector(`a[href="#${section.id}"]`);
      if (active) active.classList.add('active');
    }
  });
}, { passive: true });

/* --- Intersection Observer: fade-in on scroll --- */
const observer = new IntersectionObserver(
  (entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.classList.add('visible');
        observer.unobserve(entry.target);
      }
    });
  },
  { threshold: 0.1, rootMargin: '0px 0px -40px 0px' }
);

document.querySelectorAll(
  '.service-card, .project-card, .gallery-item, .associate-card, .highlight, .stat'
).forEach(el => {
  el.classList.add('fade-in');
  observer.observe(el);
});

/* Inject fade-in CSS dynamically */
const fadeStyle = document.createElement('style');
fadeStyle.textContent = `
  .fade-in {
    opacity: 0;
    transform: translateY(24px);
    transition: opacity 0.55s ease, transform 0.55s ease;
  }
  .fade-in.visible {
    opacity: 1;
    transform: none;
  }
  .nav-links a.active {
    color: #c9a84c !important;
  }
`;
document.head.appendChild(fadeStyle);

/* --- Contact form --- */
function handleFormSubmit(e) {
  e.preventDefault();
  const btn = e.target.querySelector('button[type="submit"]');
  const success = document.getElementById('form-success');
  btn.disabled = true;
  btn.textContent = 'Sending…';
  setTimeout(() => {
    e.target.reset();
    btn.textContent = 'Send Enquiry →';
    btn.disabled = false;
    success.style.display = 'block';
    setTimeout(() => { success.style.display = 'none'; }, 5000);
  }, 900);
}

/* --- Gallery lightbox (simple) --- */
const galleryItems = document.querySelectorAll('.gallery-item img');
galleryItems.forEach(img => {
  img.style.cursor = 'pointer';
  img.addEventListener('click', () => {
    const overlay = document.createElement('div');
    overlay.style.cssText = `
      position:fixed;inset:0;background:rgba(5,13,26,.95);
      z-index:9999;display:flex;align-items:center;justify-content:center;
      cursor:pointer;animation:fadeInOverlay .2s ease;
    `;
    const bigImg = document.createElement('img');
    bigImg.src = img.src.replace('-370x350', '').replace('-370x350', '');
    bigImg.style.cssText = `
      max-width:90vw;max-height:88vh;object-fit:contain;
      border-radius:8px;box-shadow:0 24px 80px rgba(0,0,0,.6);
    `;
    overlay.appendChild(bigImg);
    overlay.addEventListener('click', () => overlay.remove());
    document.body.appendChild(overlay);
  });
});

const lightboxStyle = document.createElement('style');
lightboxStyle.textContent = `@keyframes fadeInOverlay { from { opacity:0 } to { opacity:1 } }`;
document.head.appendChild(lightboxStyle);
