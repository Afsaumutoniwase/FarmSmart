window.addEventListener('load', function() {
    const loader = document.getElementById('loader');
    const content = document.querySelector('.content');
    const navbar = document.querySelector('.navbar');
    
    loader.style.display = 'none';
    content.style.display = 'block';
    
    window.addEventListener('scroll', function() {
        if (window.scrollY > 0) {
            navbar.classList.add('shadow');
        } else {
            navbar.classList.remove('shadow');
        }
    });
});

//Mobile media queries
// Get the mobile menu button, the mobile navigation menu, and the close icon
const mobileMenuButton = document.getElementById('mobile_menu');
const mobileNavMenu = document.querySelector('.mobile_nav_menu');
const mobileMenuClose = document.getElementById('mobile_menu_close');

// Add click event listener to the mobile menu button
mobileMenuButton.addEventListener('click', function() {
    // Toggle the 'active' class on the mobile navigation menu
    mobileNavMenu.classList.toggle('active');
});

// Add click event listener to the close icon
mobileMenuClose.addEventListener('click', function() {
    // Hide the mobile navigation menu
    mobileNavMenu.classList.remove('active');
});

document.addEventListener('DOMContentLoaded', () => {
  const destinationsCount = new countUp.CountUp('collections-count', 236);
  const toursCount = new countUp.CountUp('recycling-count', 1700);
  const customersCount = new countUp.CountUp('users-count', 5890);
  const guidesCount = new countUp.CountUp('impact-count', 120);
  
  destinationsCount.start();
  toursCount.start();
  customersCount.start();
  guidesCount.start();
});


const items = document.querySelectorAll(".accordion button");

function toggleAccordion() {
  const itemToggle = this.getAttribute('aria-expanded');
  
  for (i = 0; i < items.length; i++) {
    items[i].setAttribute('aria-expanded', 'false');
  }
  
  if (itemToggle == 'false') {
    this.setAttribute('aria-expanded', 'true');
  }
}

items.forEach(item => item.addEventListener('click', toggleAccordion));

