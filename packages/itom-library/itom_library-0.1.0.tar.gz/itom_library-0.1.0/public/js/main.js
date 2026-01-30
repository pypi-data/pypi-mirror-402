// Main JavaScript file for ITOM Library documentation site

document.addEventListener('DOMContentLoaded', function() {
    console.log('ITOM Library documentation loaded');

    // Copy button functionality
    const copyButtons = document.querySelectorAll('.copy-btn');
    copyButtons.forEach(button => {
        button.addEventListener('click', function() {
            // Get the code content
            const codeBlock = this.nextElementSibling.querySelector('code');
            const textToCopy = codeBlock.textContent;

            // Copy to clipboard
            navigator.clipboard.writeText(textToCopy).then(() => {
                // Visual feedback
                const originalHTML = this.innerHTML;
                this.classList.add('copied');
                this.innerHTML = '<i class="bi bi-check2"></i>';
                
                // Reset after 2 seconds
                setTimeout(() => {
                    this.classList.remove('copied');
                    this.innerHTML = originalHTML;
                }, 2000);
            }).catch(err => {
                console.error('Failed to copy text: ', err);
                alert('Failed to copy code. Please try again.');
            });
        });
    });

    // Smooth scroll with active nav link highlighting
    const sections = document.querySelectorAll('section[id], header[id]');
    const navLinks = document.querySelectorAll('.navbar-nav .nav-link');

    function setActiveNavLink() {
        let current = '';
        sections.forEach(section => {
            const sectionTop = section.offsetTop;
            const sectionHeight = section.clientHeight;
            if (pageYOffset >= sectionTop - 100) {
                current = section.getAttribute('id');
            }
        });

        navLinks.forEach(link => {
            link.classList.remove('active');
            if (link.getAttribute('href') === '#' + current) {
                link.classList.add('active');
            }
        });
    }

    window.addEventListener('scroll', setActiveNavLink);
    setActiveNavLink(); // Call on load

    // Show success message and clear URL parameter after form submission
    if (window.location.search.includes('success=true')) {
        // Create and show success alert
        const alertDiv = document.createElement('div');
        alertDiv.className = 'alert alert-success alert-dismissible fade show position-fixed top-0 start-50 translate-middle-x mt-3';
        alertDiv.style.zIndex = '9999';
        alertDiv.innerHTML = `
            <strong><i class="bi bi-check-circle"></i> Success!</strong> Your message has been sent. We'll get back to you soon.
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        document.body.appendChild(alertDiv);

        // Auto-dismiss after 5 seconds
        setTimeout(() => {
            alertDiv.remove();
        }, 5000);

        // Clear URL parameter
        const url = new URL(window.location);
        url.searchParams.delete('success');
        window.history.replaceState({}, '', url);
    }

    // Form submission handling - clear fields after submit
    const feedbackForm = document.querySelector('.feedback-form');
    if (feedbackForm) {
        feedbackForm.addEventListener('submit', function() {
            // Form will submit to FormSubmit.co, fields will be cleared on redirect
            // This just ensures any cached data is cleared
            setTimeout(() => {
                this.reset();
            }, 100);
        });
    }

    const contactForm = document.querySelector('.contact-form');
    if (contactForm) {
        contactForm.addEventListener('submit', function() {
            // Form will submit to FormSubmit.co, fields will be cleared on redirect
            setTimeout(() => {
                this.reset();
            }, 100);
        });
    }
});
