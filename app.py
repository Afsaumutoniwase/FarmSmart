from werkzeug.utils import secure_filename
from flask_sqlalchemy import SQLAlchemy
import os
from werkzeug.security import generate_password_hash, check_password_hash
from flask import render_template, Flask, request, redirect, url_for
from flask_login import login_user, LoginManager, UserMixin, current_user, login_required
from flask import flash

app = Flask(__name__)
app.config['SECRET_KEY'] = 'farm smart'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    role = db.Column(db.String(255))
    password_hash = db.Column(db.String(255))
    address = db.Column(db.String(255))
    phone = db.Column(db.String(20))
    profile_image_url = db.Column(db.String(255))
    profile_complete = db.Column(db.Boolean, default=False)  # New field to track profile completion

    # This is optional but recommended for setting a hashed password
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=False)
    price = db.Column(db.Float, nullable=False)
    image_url = db.Column(db.String(255), nullable=True)

    def __repr__(self):
        return f'<Product {self.name}>'
class Cart(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Integer, default=1)

    user = db.relationship('User', backref=db.backref('cart_items', lazy=True))
    product = db.relationship('Product', backref=db.backref('cart_items', lazy=True))

    def total_price(self):
        return self.quantity * self.product.price

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form.get('form_type') == 'register':  # Registration form
            username = request.form.get('username')
            email = request.form.get('email')
            password = request.form.get('password')
            role = request.form.get('role')

            # Check if user already exists
            if User.query.filter_by(username=username).first():
                flash('Username already taken')
                return redirect(url_for('login') + '#register-form')
            if User.query.filter_by(email=email).first():
                flash('Email already in use')
                return redirect(url_for('login') + '#register-form')

            # Register new user
            new_user = User(username=username, email=email, role=role)
            new_user.set_password(password)
            db.session.add(new_user)
            db.session.commit()
            flash('Registration successful! Please log in.')
            return redirect(url_for('login'))

        elif request.form.get('form_type') == 'login':  # Login form
            # Login logic (authenticate user)
            user = User.query.filter_by(username=request.form['username']).first()
            if user and user.check_password(request.form['password']):
                login_user(user)
                # Check if the profile is complete
                if not user.profile_complete:
                    flash("Please complete your profile information.", "info")
                    return redirect(url_for('profile'))
                return redirect(url_for('dashboard'))  # Redirect to main dashboard if profile is complete
            flash("Invalid credentials", "error")
            return redirect(url_for('login'))

    # For GET request, simply render the login page
    return render_template('login.html')


@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        # Get the form data
        username = request.form.get('username', current_user.username)
        email = request.form.get('email', current_user.email)
        role = request.form.get('role', current_user.role)
        address = request.form.get('address', current_user.address)
        phone = request.form.get('phone', current_user.phone)

        # Handle profile image upload
        if 'profileImageInput' in request.files:
            file = request.files['profileImageInput']
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                filepath = os.path.join('static/uploads', filename)
                file.save(filepath)
                current_user.profile_image_url = f"/static/uploads/{filename}"
            else:
                flash("Invalid image format. Allowed formats are png, jpg, jpeg, and gif.", "error")

        # Update user data and mark profile as complete
        current_user.username = username
        current_user.email = email
        current_user.address = address
        current_user.phone = phone
        current_user.profile_complete = True  # Mark profile as complete
        db.session.commit()

        flash("Profile updated successfully!", "success")
        return redirect(url_for('dashboard'))  # Redirect to main dashboard after completion

    return render_template('profile.html', user=current_user)
# Example list of products (this would typically come from a database)
products = [
    {"id": 1, "name": "Hydroponic Kit", "price": 50, "description": "A complete kit for hydroponic farming.", "image_url": "path/to/image1.jpg"},
    {"id": 2, "name": "LED Grow Light", "price": 30, "description": "High-quality LED lights for optimal plant growth.", "image_url": "path/to/image2.jpg"},
    {"id": 3, "name": "pH Meter", "price": 20, "description": "Measure the pH levels in your hydroponic system.", "image_url": "path/to/image3.jpg"},
    {"id": 4, "name": "Nutrient Solution", "price": 15, "description": "Essential nutrients for hydroponic plants.", "image_url": "path/to/image4.jpg"}
]

# In-memory "cart"
user_cart = []  # Renamed from cart to user_cart

@app.route('/market', methods=['GET', 'POST'])
def market():
    global products, user_cart  # Make sure to use the correct cart variable name

    # Handle adding products to the cart
    if request.method == 'POST':
        product_id = int(request.form['product_id'])
        quantity = int(request.form['quantity'])
        # Find the product based on the product_id
        product = next((prod for prod in products if prod['id'] == product_id), None)
        if product:
            user_cart.append({'product': product, 'quantity': quantity})

    return render_template('market.html', products=products, cart=user_cart)

@app.route('/add_product', methods=['GET', 'POST'])
def add_product():
    if request.method == 'POST':
        name = request.form['name']
        price = float(request.form['price'])
        description = request.form['description']
        image_url = request.form['image_url']

        new_product = {
            "id": len(products) + 1,
            "name": name,
            "price": price,
            "description": description,
            "image_url": image_url
        }
        products.append(new_product)
        return redirect(url_for('market'))

    return render_template('add_product.html')
@app.route('/cart')
@login_required
def cart():
    cart_items = Cart.query.filter_by(user_id=current_user.id).all()
    return render_template('cart.html', cart_items=cart_items)

    return render_template('market.html', products=products)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/hydroponic')
def hydroponic():
    return render_template('hydroponic.html')

@app.route('/dashboard')
def dashboard():
    return render_template("dashboard.html")


# Other routes
@app.route('/hydroponic-monitor')
def hydroponic_monitor():
    return render_template('hydroponics.html', title="Hydroponic")

@app.route('/expert')
def expert():
    return render_template('expert.html', title="Book an Expert")

@app.route('/forums')
def forums():   
    return render_template('forums.html', title="Forums")



@app.route('/settings')
def settings():   
    return render_template('settings.html', title="Settings")

@app.route('/help')
def help():   
    return render_template('help.html', title="Help")

@app.route('/logout')
def logout():   
    return render_template('login.html', title="Logout")

if __name__ == '__main__':
    # Initialize database
    with app.app_context():
        db.create_all()  # This will create tables if they don't exist

    app.run(debug=True)
