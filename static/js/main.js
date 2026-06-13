// ===== Mobile Menu Toggle =====
const hamburger = document.getElementById('hamburger');
const navLinks = document.getElementById('navLinks');

hamburger.addEventListener('click', () => {
  navLinks.classList.toggle('open');
  hamburger.classList.toggle('active');
});

navLinks.querySelectorAll('a').forEach(link => {
  link.addEventListener('click', () => {
    navLinks.classList.remove('open');
  });
});

// ===== Scroll Reveal Animation =====
const revealEls = document.querySelectorAll('.reveal, .reveal-left, .reveal-right');

const revealObserver = new IntersectionObserver((entries) => {
  entries.forEach(entry => {
    if (entry.isIntersecting) {
      entry.target.classList.add('in');
      revealObserver.unobserve(entry.target);
    }
  });
}, { threshold: 0.15 });

revealEls.forEach(el => revealObserver.observe(el));

// ===== Animated Counter Stats =====
const statNumbers = document.querySelectorAll('.stat-number');

function animateCounter(el) {
  const target = parseFloat(el.dataset.target);
  const suffix = el.dataset.suffix || '';
  const isDecimal = target % 1 !== 0;
  const duration = 1600;
  const start = performance.now();

  function update(now) {
    const progress = Math.min((now - start) / duration, 1);
    const eased = 1 - Math.pow(1 - progress, 3);
    const value = target * eased;
    el.textContent = (isDecimal ? value.toFixed(1) : Math.floor(value)) + suffix;
    if (progress < 1) requestAnimationFrame(update);
    else el.textContent = (isDecimal ? target.toFixed(1) : target) + suffix;
  }
  requestAnimationFrame(update);
}

const statObserver = new IntersectionObserver((entries) => {
  entries.forEach(entry => {
    if (entry.isIntersecting) {
      animateCounter(entry.target);
      statObserver.unobserve(entry.target);
    }
  });
}, { threshold: 0.4 });

statNumbers.forEach(el => statObserver.observe(el));

// ===== Hero Particles =====
const particlesContainer = document.getElementById('particles');
const PARTICLE_COUNT = 22;

for (let i = 0; i < PARTICLE_COUNT; i++) {
  const span = document.createElement('span');
  const size = 3 + Math.random() * 6;
  span.style.width = `${size}px`;
  span.style.height = `${size}px`;
  span.style.left = `${Math.random() * 100}%`;
  span.style.animationDuration = `${10 + Math.random() * 14}s`;
  span.style.animationDelay = `${Math.random() * 14}s`;
  particlesContainer.appendChild(span);
}

// ===== Testimonial Slider =====
const testiTrack = document.getElementById('testiTrack');
const testiDotsContainer = document.getElementById('testiDots');
const testiCards = testiTrack.querySelectorAll('.testimonial-card');
let currentTesti = 0;

testiCards.forEach((_, i) => {
  const dot = document.createElement('button');
  if (i === 0) dot.classList.add('active');
  dot.addEventListener('click', () => goToTesti(i));
  testiDotsContainer.appendChild(dot);
});

const dots = testiDotsContainer.querySelectorAll('button');

function goToTesti(index) {
  currentTesti = index;
  testiTrack.style.transform = `translateX(-${index * 100}%)`;
  dots.forEach((d, i) => d.classList.toggle('active', i === index));
}

function nextTesti() {
  currentTesti = (currentTesti + 1) % testiCards.length;
  goToTesti(currentTesti);
}

setInterval(nextTesti, 5000);

// ===== Contact Form =====
const contactForm = document.getElementById('contactForm');
const formSuccess = document.getElementById('formSuccess');

contactForm.addEventListener('submit', (e) => {
  e.preventDefault();
  const formData = new FormData(contactForm);
  fetch('/enquiry', { method: 'POST', body: formData })
    .then(res => res.json())
    .then(data => {
      if (data.success) {
        formSuccess.classList.add('show');
        contactForm.reset();
        setTimeout(() => formSuccess.classList.remove('show'), 5000);
      }
    })
    .catch(() => {
      formSuccess.textContent = 'Something went wrong. Please call us directly.';
      formSuccess.classList.add('show');
    });
});

// ===== Navbar shadow on scroll =====
const navbar = document.getElementById('navbar');
window.addEventListener('scroll', () => {
  if (window.scrollY > 20) {
    navbar.style.boxShadow = '0 6px 24px -8px rgba(15,31,61,0.18)';
  } else {
    navbar.style.boxShadow = 'none';
  }
});

// ===== Enquiry Popup Modal (shows 30s after page load, every visit) =====
const enquiryModal = document.getElementById('enquiryModal');
const modalClose = document.getElementById('modalClose');
const popupForm = document.getElementById('popupForm');
const popupSuccess = document.getElementById('popupSuccess');

function openEnquiryModal() {
  enquiryModal.classList.add('active');
}

function closeEnquiryModal() {
  enquiryModal.classList.remove('active');
}

if (enquiryModal) {
  setTimeout(openEnquiryModal, 30000);

  modalClose.addEventListener('click', closeEnquiryModal);

  enquiryModal.addEventListener('click', (e) => {
    if (e.target === enquiryModal) closeEnquiryModal();
  });

  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && enquiryModal.classList.contains('active')) {
      closeEnquiryModal();
    }
  });

  popupForm.addEventListener('submit', (e) => {
    e.preventDefault();
    const formData = new FormData(popupForm);
    fetch('/enquiry', { method: 'POST', body: formData })
      .then(res => res.json())
      .then(data => {
        if (data.success) {
          popupSuccess.classList.add('show');
          popupForm.reset();
          setTimeout(() => {
            popupSuccess.classList.remove('show');
            closeEnquiryModal();
          }, 2000);
        }
      })
      .catch(() => {
        popupSuccess.textContent = 'Something went wrong. Please call us directly.';
        popupSuccess.classList.add('show');
      });
  });
}
