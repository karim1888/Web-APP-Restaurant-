document.addEventListener('DOMContentLoaded', function() {
    // Mobile Menu Toggle
    const mobileMenuBtn = document.getElementById('mobileMenuBtn');
    const navMenu = document.getElementById('navMenu');
    
    if (mobileMenuBtn && navMenu) {
        mobileMenuBtn.addEventListener('click', () => {
            navMenu.classList.toggle('show');
            mobileMenuBtn.innerHTML = navMenu.classList.contains('show') ? 
                '<i class="fas fa-times"></i>' : '<i class="fas fa-bars"></i>';
        });

        document.querySelectorAll('#navMenu a').forEach(link => {
            link.addEventListener('click', () => {
                navMenu.classList.remove('show');
                mobileMenuBtn.innerHTML = '<i class="fas fa-bars"></i>';
            });
        });
    }

    // Smooth Scrolling
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            e.preventDefault();
            const targetId = this.getAttribute('href');
            const targetElement = document.querySelector(targetId);
            
            if (targetElement) {
                window.scrollTo({
                    top: targetElement.offsetTop - 80,
                    behavior: 'smooth'
                });
            }
        });
    });

    // Sticky Header
    window.addEventListener('scroll', function() {
        const header = document.querySelector('header');
        if (header) {
            header.classList.toggle('sticky', window.scrollY > 100);
        }
    });

    // Menu Filtering
    const menuButtons = document.querySelectorAll('.menu-categories button');
    const menuItems = document.querySelectorAll('.menu-item');
    
    if (menuButtons.length && menuItems.length) {
        menuButtons.forEach(button => {
            button.addEventListener('click', () => {
                menuButtons.forEach(btn => btn.classList.remove('active'));
                button.classList.add('active');
                
                const category = button.getAttribute('data-category');
                
                menuItems.forEach(item => {
                    if (category === 'all' || item.getAttribute('data-category') === category) {
                        item.style.display = 'block';
                    } else {
                        item.style.display = 'none';
                    }
                });
            });
        });
    }

    // Reservation Form
    const reservationForm = document.getElementById('reservationForm');
    if (reservationForm) {
        // Initialize date picker
        const dateInput = document.getElementById('date');
        if (dateInput) {
            const today = new Date().toISOString().split('T')[0];
            dateInput.min = today;
            dateInput.value = today;
        }

        // Time slot selection
        const timeSlots = [
            '11:00 AM', '11:30 AM', '12:00 PM', '12:30 PM', 
            '1:00 PM', '1:30 PM', '2:00 PM', '5:00 PM', 
            '5:30 PM', '6:00 PM', '6:30 PM', '7:00 PM', 
            '7:30 PM', '8:00 PM', '8:30 PM', '9:00 PM'
        ];

        const timeSelect = document.createElement('select');
        timeSelect.id = 'time';
        timeSelect.name = 'time';
        timeSelect.required = true;

        const timeLabel = document.createElement('label');
        timeLabel.textContent = 'Reservation Time';
        timeLabel.htmlFor = 'time';

        const timeGroup = document.createElement('div');
        timeGroup.className = 'form-group';
        timeGroup.appendChild(timeLabel);
        timeGroup.appendChild(timeSelect);

        if (dateInput) {
            dateInput.parentElement.after(timeGroup);
        }

        // Populate time slots
        timeSlots.forEach(time => {
            const option = document.createElement('option');
            option.value = time;
            option.textContent = time;
            timeSelect.appendChild(option);
        });

        // Form submission
        reservationForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const formData = {
                name: document.getElementById('name').value.trim(),
                email: document.getElementById('email').value.trim(),
                phone: document.getElementById('phone').value.trim(),
                date: document.getElementById('date').value,
                time: document.getElementById('time').value,
                guests: document.getElementById('guests').value,
                message: document.getElementById('message').value.trim()
            };
            
            try {
                const response = await fetch('/api/reservations', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(formData)
                });
                
                const data = await response.json();
                
                if (data.success) {
                    showAlert('Reservation request sent successfully! We will contact you shortly to confirm.', 'success');
                    reservationForm.reset();
                } else {
                    showAlert(data.message, 'error');
                }
            } catch (error) {
                showAlert('An error occurred. Please try again later.', 'error');
                console.error('Error:', error);
            }
        });

        // Availability check
        timeSelect.addEventListener('change', async function() {
            const date = dateInput.value;
            const time = this.value;
            const guests = document.getElementById('guests').value || 2;
            
            if (!date) return;
            
            const existingStatus = timeSelect.parentElement.querySelector('.availability-status');
            if (existingStatus) existingStatus.remove();
            
            const availabilityStatus = document.createElement('div');
            availabilityStatus.className = 'availability-status';
            timeSelect.parentElement.appendChild(availabilityStatus);
            
            try {
                const response = await fetch(`/api/check-availability?date=${date}&time=${time}&guests=${guests}`);
                const data = await response.json();
                
                if (data.available) {
                    availabilityStatus.innerHTML = `
                        <div class="available">
                            <i class="fas fa-check-circle"></i> Table available for ${guests} guests
                        </div>
                    `;
                } else {
                    let suggestions = '';
                    if (data.suggested_times && data.suggested_times.length) {
                        suggestions = `<p>Suggested times: ${data.suggested_times.join(', ')}</p>`;
                    }
                    availabilityStatus.innerHTML = `
                        <div class="unavailable">
                            <i class="fas fa-times-circle"></i> Fully booked at this time
                            ${suggestions}
                        </div>
                    `;
                }
                
                setTimeout(() => {
                    availabilityStatus.style.opacity = '1';
                }, 10);
            } catch (error) {
                console.error('Error checking availability:', error);
            }
        });
    }

    // Shopping Cart
    const cart = {
        items: [],
        total: 0,
        addItem: function(item) {
            this.items.push(item);
            this.total += item.price;
            this.updateCart();
            showAlert(`${item.name} added to your order!`, 'success');
        },
        removeItem: function(index) {
            this.total -= this.items[index].price;
            this.items.splice(index, 1);
            this.updateCart();
        },
        updateCart: function() {
            const cartCount = document.getElementById('cart-count');
            if (cartCount) {
                cartCount.textContent = this.items.length;
            }
        }
    };

    // Cart icon click handler
    const cartIcon = document.querySelector('.cart-icon');
    if (cartIcon) {
        cartIcon.addEventListener('click', function(e) {
            e.preventDefault();
            
            const modal = document.createElement('div');
            modal.className = 'cart-modal';
            
            let itemsHtml = '';
            if (cart.items.length === 0) {
                itemsHtml = '<p class="empty-cart">Your cart is empty</p>';
            } else {
                itemsHtml = cart.items.map((item, index) => `
                    <div class="cart-item">
                        <div class="cart-item-info">
                            <h4>${item.name}</h4>
                            <span>$${item.price.toFixed(2)}</span>
                        </div>
                        <button class="remove-item" data-index="${index}"><i class="fas fa-times"></i></button>
                    </div>
                `).join('');
            }
            
            modal.innerHTML = `
                <div class="cart-content">
                    <button class="cart-close"><i class="fas fa-times"></i></button>
                    <h3>Your Order</h3>
                    <div class="cart-items">
                        ${itemsHtml}
                    </div>
                    <div class="cart-total">
                        <span>Total:</span>
                        <span>$${cart.total.toFixed(2)}</span>
                    </div>
                    <button class="checkout-btn">Proceed to Checkout</button>
                </div>
            `;
            
            document.body.appendChild(modal);
            document.body.style.overflow = 'hidden';
            
            // Close modal
            modal.querySelector('.cart-close').addEventListener('click', () => {
                modal.remove();
                document.body.style.overflow = '';
            });
            
            // Close when clicking outside
            modal.addEventListener('click', (e) => {
                if (e.target === modal) {
                    modal.remove();
                    document.body.style.overflow = '';
                }
            });
            
            // Remove item buttons
            modal.querySelectorAll('.remove-item').forEach(button => {
                button.addEventListener('click', function() {
                    const index = parseInt(this.getAttribute('data-index'));
                    cart.removeItem(index);
                    modal.remove();
                    cartIcon.click(); // Reopen cart
                });
            });
            
            // Checkout button
            modal.querySelector('.checkout-btn').addEventListener('click', async () => {
                try {
                    const response = await fetch('/api/orders', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify({
                            items: cart.items.map(item => ({
                                id: item.id || 0,
                                price: item.price,
                                quantity: 1
                            })),
                            customer_name: prompt('Your name (optional)') || '',
                            customer_email: prompt('Your email (optional)') || '',
                            customer_phone: prompt('Your phone (optional)') || ''
                        })
                    });
                    
                    const data = await response.json();
                    
                    if (data.success) {
                        alert(`Order #${data.order_id} created successfully! Total: $${cart.total.toFixed(2)}`);
                        cart.items = [];
                        cart.total = 0;
                        cart.updateCart();
                        modal.remove();
                        document.body.style.overflow = '';
                    } else {
                        alert('Error creating order: ' + data.message);
                    }
                } catch (error) {
                    alert('Error creating order. Please try again.');
                    console.error('Error:', error);
                }
            });
        });
    }

    // Newsletter Form
    const newsletterForm = document.querySelector('.newsletter-form');
    if (newsletterForm) {
        newsletterForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const email = this.querySelector('input[type="email"]').value.trim();
            const formData = new FormData();
            formData.append('email', email);
            
            try {
                const response = await fetch('/api/subscribe', {
                    method: 'POST',
                    body: formData
                });
                
                const data = await response.json();
                showNewsletterAlert(data.message, data.success ? 'success' : 'error');
                
                if (data.success) {
                    this.reset();
                }
            } catch (error) {
                showNewsletterAlert('An error occurred. Please try again later.', 'error');
                console.error('Error:', error);
            }
        });
    }

    // Helper functions
    function showAlert(message, type) {
        const existingAlert = document.querySelector('.form-alert');
        if (existingAlert) existingAlert.remove();
        
        const alertDiv = document.createElement('div');
        alertDiv.className = `form-alert ${type}`;
        alertDiv.textContent = message;
        
        if (reservationForm) {
            reservationForm.insertBefore(alertDiv, reservationForm.firstChild);
        }
        
        setTimeout(() => {
            alertDiv.remove();
        }, 5000);
    }

    function showNewsletterAlert(message, type) {
        const existingAlert = document.querySelector('.newsletter-alert');
        if (existingAlert) existingAlert.remove();
        
        const alertDiv = document.createElement('div');
        alertDiv.className = `newsletter-alert ${type}`;
        alertDiv.textContent = message;
        
        if (newsletterForm) {
            newsletterForm.appendChild(alertDiv);
        }
        
        setTimeout(() => {
            alertDiv.remove();
        }, 5000);
    }

    // Current Year
    const currentYear = document.getElementById('current-year');
    if (currentYear) {
        currentYear.textContent = new Date().getFullYear();
    }
});