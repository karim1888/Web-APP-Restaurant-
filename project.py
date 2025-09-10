'''
from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import timedelta
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'merje'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///toomburgg.db'
app.permanent_session_lifetime = timedelta(minutes=5)
db = SQLAlchemy(app)

# ------------------------ MODELS ----------------------------
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    password = db.Column(db.String(60), nullable=False)
    reservations = db.relationship('Reservation', backref='user', lazy=True)
    orders = db.relationship('Order', back_populates='user', lazy=True)

    def __init__(self, **kwargs):
        kwargs['email'] = kwargs['email'].lower()
        super().__init__(**kwargs)

class Reservation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    date = db.Column(db.String(50))
    time = db.Column(db.String(50))
    guests = db.Column(db.Integer)

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    item = db.Column(db.String(100))

    # Explicit relationship with User
    user = db.relationship('User', back_populates='orders')  # Add this line

with app.app_context():
    db.create_all()

# ------------------------ ROUTES ----------------------------
@app.route('/', methods=['GET', 'POST'])
def login():
    admin_credentials = {'abdekrahmankarim@gmail.com': generate_password_hash('#Admin123')}  # Store hashed password

    if request.method == 'POST':
        email = request.form['email'].strip().lower()  # Normalize email
        password = request.form['password']

        # Admin login check
        if email in admin_credentials:
            if check_password_hash(admin_credentials[email], password):  # Secure comparison
                session['user_first_name'] = 'Admin'
                session['user_id'] = 0
                session['discount'] = False
                return redirect(url_for('home'))
            else:
                flash("Incorrect admin password.", "error")
                return redirect(url_for('login'))

        # Regular user check
        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password, password):
            has_reservations = Reservation.query.filter_by(user_id=user.id).first() is not None
            has_orders = Order.query.filter_by(user_id=user.id).first() is not None
            session['user_id'] = user.id
            session['user_first_name'] = user.first_name
            session['discount'] = has_reservations or has_orders
            return redirect(url_for('home'))
        elif user:
            flash("Incorrect password.", "error")
            return redirect(url_for('login'))  # Add redirect here
        else:
            flash("Email not found. Please register.", "error")
            return redirect(url_for('register'))

    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email'].strip().lower()  # Add this line
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        password = request.form['password']
        confirm = request.form['confirm']

        if password != confirm:
            flash("Passwords do not match.", "error")
            return redirect(url_for('register'))

        if User.query.filter_by(email=email).first():
            flash("Email already exists. Please log in.", "error")
            return redirect(url_for('login'))

        hashed_pw = generate_password_hash(password, method='pbkdf2:sha256')
        new_user = User(email=email, first_name=first_name, last_name=last_name, password=hashed_pw)
        db.session.add(new_user)
        db.session.commit()

        session['user_id'] = new_user.id
        session['user_first_name'] = first_name
        session['discount'] = False  # New users start without discount
        return redirect(url_for('home'))

    return render_template('register.html')

@app.route('/order', methods=['GET', 'POST'])
def order():
    if request.method == 'POST':
        return redirect(url_for('confirm_order'))  # Redirect to confirmation

    return render_template('order.html', discount=session.get('discount', False))

@app.route('/confirm_order', methods=['POST'])
def confirm_order():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    items = request.form.getlist('items')
    if not items:
        flash("No items selected!", "error")
        return redirect(url_for('order'))

    total_price = 0
    item_list = []

    for item in items:
        name, price = item.split(',')
        price = float(price)
        total_price += price
        item_list.append({'name': name, 'price': price})

    # Apply discount
    if session.get('discount'):
        total_price *= 0.9

    # Store in session for payment step
    session['pending_order'] = {
        'items': item_list,
        'total': round(total_price, 2)
    }

    return render_template('confirm_order.html', total=session['pending_order']['total'])

@app.route('/process_payment', methods=['POST'])
def process_payment():
    if 'pending_order' not in session:
        flash("No order to process.", "error")
        return redirect(url_for('home'))

    # Simulated payment validation
    card_number = request.form.get('card_number', '').strip().replace(' ', '')
    if len(card_number) != 16 or not card_number.isdigit():
        flash("Invalid card number (must be 16 digits).", "error")
        return redirect(url_for('confirm_order'))

    # Save to database
    for item in session['pending_order']['items']:
        new_order = Order(
            user_id=session['user_id'],
            item=item['name']
        )
        db.session.add(new_order)
    db.session.commit()

    # Update discount eligibility
    session['discount'] = True  # Now has order history
    session.pop('pending_order')

    flash("Thank you for your trust! Your order is confirmed.", "success")
    return redirect(url_for('home'))

@app.route('/reserve', methods=['GET', 'POST'])
def reserve():
    if request.method == 'POST':
        reservation = Reservation(
            user_id=session['user_id'],
            date=request.form['date'],
            time=request.form['time'],
            guests=request.form['guests']
        )
        db.session.add(reservation)
        db.session.commit()
        flash("Reservation successful!", "success")
        return redirect(url_for('home'))

    return render_template('reserve.html', discount=session.get('discount', False))

@app.route('/home')
def home():
    is_admin = session.get('user_first_name') == 'Admin'
    return render_template('home.html', is_admin=is_admin)


@app.route('/admin_dashboard')
def admin_panel():
    if session.get('user_first_name') == 'Admin':
        reservations = Reservation.query.options(db.joinedload(Reservation.user)).all()
        orders = Order.query.options(db.joinedload(Order.user)).all()
        users = User.query.all()
        return render_template('admin_dashboard.html', 
                             reservations=reservations, 
                             orders=orders, 
                             users=users)
    
    flash("Access denied.", "error")
    return redirect(url_for('home'))



@app.route('/logout', methods=['POST'])
def logout():
    session.clear()
    return redirect(url_for('login'))


if __name__ == '__main__':
    app.run(debug=False)
'''


from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from datetime import timedelta
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'merje'  # Required for session
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///toomburgg.db'
app.permanent_session_lifetime = timedelta(minutes=5)
db = SQLAlchemy(app)

# ------------------------ MODELS (Same as before) ----------------------------
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    password = db.Column(db.String(60), nullable=False)
    reservations = db.relationship('Reservation', backref='user', lazy=True)
    orders = db.relationship('Order', back_populates='user', lazy=True)

    def __init__(self, **kwargs):
        kwargs['email'] = kwargs['email'].lower()
        super().__init__(**kwargs)

class Reservation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    date = db.Column(db.String(50))
    time = db.Column(db.String(50))
    guests = db.Column(db.Integer)

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    item = db.Column(db.String(100))
    user = db.relationship('User', back_populates='orders')

with app.app_context():
    db.create_all()

# ------------------------ MODIFIED ROUTES WITH SESSION MESSAGES ----------------------------
@app.route('/', methods=['GET', 'POST'])
def login():
    admin_credentials = {'abdekrahmankarim@gmail.com': generate_password_hash('#Admin123')}

    if request.method == 'POST':
        email = request.form['email'].strip().lower()
        password = request.form['password']

        # Admin check
        if email in admin_credentials:
            if check_password_hash(admin_credentials[email], password):
                session['user_first_name'] = 'Admin'
                session['user_id'] = 0
                session['discount'] = False
                return redirect(url_for('home'))
            else:
                session['error'] = "Incorrect admin password"
                return redirect(url_for('login'))

        # Regular user check
        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password, password):
            has_reservations = Reservation.query.filter_by(user_id=user.id).first() is not None
            has_orders = Order.query.filter_by(user_id=user.id).first() is not None
            session['user_id'] = user.id
            session['user_first_name'] = user.first_name
            session['discount'] = has_reservations or has_orders
            return redirect(url_for('home'))
        elif user:
            session['error'] = "Incorrect password"
            return redirect(url_for('login'))
        else:
            session['error'] = "Email not found. Please register"
            return redirect(url_for('register'))

    error = session.pop('error', None)
    return render_template('login.html', error=error)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email'].strip().lower()
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        password = request.form['password']
        confirm = request.form['confirm']

        if password != confirm:
            session['error'] = "Passwords do not match"
            return redirect(url_for('register'))

        if User.query.filter_by(email=email).first():
            session['error'] = "Email already exists. Please log in"
            return redirect(url_for('login'))

        hashed_pw = generate_password_hash(password, method='pbkdf2:sha256')
        new_user = User(email=email, first_name=first_name, last_name=last_name, password=hashed_pw)
        db.session.add(new_user)
        db.session.commit()

        session['user_id'] = new_user.id
        session['user_first_name'] = first_name
        session['discount'] = False
        session['success'] = "Registration successful!"
        return redirect(url_for('home'))

    error = session.pop('error', None)
    return render_template('register.html', error=error)

@app.route('/order', methods=['GET', 'POST'])
def order():
    if request.method == 'POST':
        return redirect(url_for('confirm_order'))
    
    error = session.pop('error', None)
    return render_template('order.html', 
                         discount=session.get('discount', False),
                         error=error)

@app.route('/confirm_order', methods=['POST'])
def confirm_order():
    if 'user_id' not in session:
        session['error'] = "Please login first"
        return redirect(url_for('login'))

    items = request.form.getlist('items')
    if not items:
        session['error'] = "No items selected!"
        return redirect(url_for('order'))

    total_price = 0
    item_list = []

    for item in items:
        name, price = item.split(',')
        price = float(price)
        total_price += price
        item_list.append({'name': name, 'price': price})

    if session.get('discount'):
        total_price *= 0.9

    session['pending_order'] = {
        'items': item_list,
        'total': round(total_price, 2)
    }

    return render_template('confirm_order.html', total=session['pending_order']['total'])

@app.route('/process_payment', methods=['POST'])
def process_payment():
    if 'pending_order' not in session:
        session['error'] = "No order to process"
        return redirect(url_for('home'))

    card_number = request.form.get('card_number', '').strip().replace(' ', '')
    if len(card_number) != 16 or not card_number.isdigit():
        session['error'] = "Invalid card number (must be 16 digits)"
        return redirect(url_for('confirm_order'))

    for item in session['pending_order']['items']:
        new_order = Order(
            user_id=session['user_id'],
            item=item['name']
        )
        db.session.add(new_order)
    db.session.commit()

    session['discount'] = True
    session.pop('pending_order')
    session['success'] = "Thank you for your trust! Your order is confirmed."
    return redirect(url_for('home'))

@app.route('/reserve', methods=['GET', 'POST'])
def reserve():
    if request.method == 'POST':
        reservation = Reservation(
            user_id=session['user_id'],
            date=request.form['date'],
            time=request.form['time'],
            guests=request.form['guests']
        )
        db.session.add(reservation)
        db.session.commit()
        session['success'] = "Reservation successful!"
        return redirect(url_for('home'))

    error = session.pop('error', None)
    return render_template('reserve.html', 
                         discount=session.get('discount', False),
                         error=error)

@app.route('/home')
def home():
    is_admin = session.get('user_first_name') == 'Admin'
    success = session.pop('success', None)
    error = session.pop('error', None)
    return render_template('home.html', 
                         is_admin=is_admin,
                         success=success,
                         error=error)

@app.route('/admin_dashboard')
def admin_panel():
    if session.get('user_first_name') == 'Admin':
        reservations = Reservation.query.options(db.joinedload(Reservation.user)).all()
        orders = Order.query.options(db.joinedload(Order.user)).all()
        users = User.query.all()
        return render_template('admin_dashboard.html', 
                             reservations=reservations, 
                             orders=orders, 
                             users=users)
    
    session['error'] = "Access denied"
    return redirect(url_for('home'))

@app.route('/logout', methods=['POST'])
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=False)
    
