from werkzeug.utils import secure_filename
from flask_sqlalchemy import SQLAlchemy
import os
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask import render_template, Flask, request, redirect, url_for, session
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

class Reply(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True) 
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)

    user = db.relationship('User', backref=db.backref('replies', lazy=True))
    def __repr__(self):
        return f'<Reply {self.id} to Post {self.post_id}>'

class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(255), nullable=True)
    
    def __repr__(self):
        return f'<Category {self.name}>'
    
class Cart(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Integer, default=1)

    user = db.relationship('User', backref=db.backref('cart_items', lazy=True))
    product = db.relationship('Product', backref=db.backref('cart_items', lazy=True))

    def total_price(self):
        return self.quantity * self.product.price

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=False)
    
    user = db.relationship('User', backref=db.backref('posts', lazy=True))
    category = db.relationship('Category', backref=db.backref('posts', lazy=True))
    
    # Relationship to Reply: Define backref once here
    replies = db.relationship('Reply', backref='post', cascade="all, delete-orphan")

    def __repr__(self):
        return f'<Post {self.title}>'
    
class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=False)
    price = db.Column(db.Float, nullable=False)
    image_url = db.Column(db.String(255), nullable=True)

    def __repr__(self):
        return f'<Product {self.name}>'

@app.route('/market', methods=['GET', 'POST'])
def market():
    if request.method == 'POST':
        product_id = int(request.form['product_id'])
        quantity = int(request.form['quantity'])

        # Initialize the cart if it doesn't exist
        if 'cart' not in session:
            session['cart'] = []

        # Retrieve product from the database
        product = Product.query.get_or_404(product_id)

        # Add product and quantity to the cart
        session['cart'].append({'product_id': product.id, 'name': product.name, 'price': product.price, 'quantity': quantity})
        session.modified = True  # Ensure changes are saved to session

        flash(f'Added {quantity} of {product.name} to your cart!', 'success')
        return redirect(url_for('market'))

    # Fetch all products from the database to display in the market
    products = Product.query.all()
    return render_template('market.html', products=products, cart=session.get('cart', []))

@app.route('/add_product', methods=['GET', 'POST'])
def add_product():
    if request.method == 'POST':
        name = request.form['name']
        price = float(request.form['price'])
        description = request.form['description']
        image_url = request.form['image_url']

        # Create a new product and add it to the database
        new_product = Product(name=name, price=price, description=description, image_url=image_url)
        db.session.add(new_product)
        db.session.commit()

        flash('New product added successfully!', 'success')
        return redirect(url_for('market'))

    return render_template('add_product.html')



# In-memory "cart"
user_cart = []  # Renamed from cart to user_cart


@app.route('/')
def home():
    return render_template('index.html')

@app.route('/hydroponic')
def hydroponic():
    return render_template('hydroponic.html')

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


@app.route('/cart')
def cart():
    return render_template('cart.html', cart=session.get('cart', []))

@app.route('/remove_from_cart', methods=['POST'])
def remove_from_cart():
    product_id = int(request.form['product_id'])
    session['cart'] = [item for item in session['cart'] if item['product']['id'] != product_id]
    session.modified = True  # Ensure changes are saved to session
    return redirect(url_for('cart'))

@app.route('/add_to_cart', methods=['POST'])
def add_to_cart():
    product_id = request.form.get('product_id')
    quantity = request.form.get('quantity', 1)

    # Check if product_id and quantity are correctly captured
    print(f"Product ID: {product_id}, Quantity: {quantity}")
    
    if product_id and quantity:
        product = next((p for p in products if p['id'] == int(product_id)), None)
        if product:
            # Ensure cart session key exists
            if 'cart' not in session:
                session['cart'] = []
            
            # Add item to the cart
            session['cart'].append({'product': product, 'quantity': int(quantity)})
            session.modified = True
            flash("Product added to cart!", "success")
        else:
            flash("Product not found.", "error")
    else:
        flash("Invalid product or quantity.", "error")

    return redirect(url_for('market'))


@app.route('/checkout', methods=['GET', 'POST'])
def checkout():
    # Get the cart from session
    cart = session.get('cart', [])
    total_price = sum(item['product']['price'] * item['quantity'] for item in cart)

    if request.method == 'POST':
        # Get form data
        full_name = request.form.get('full_name')
        address = request.form.get('address')
        phone = request.form.get('phone')
        payment_method = request.form.get('payment_method')

        # If the payment method is Mobile Money, just check if the phone number is entered
        if payment_method == 'mobile_money':
            momo_number = request.form.get('momo_number')
            if not momo_number:
                flash("Please enter your mobile number for Mobile Money payment.", 'error')
                return redirect(url_for('checkout'))

        # If the payment method is Card, check if all card details are entered
        elif payment_method == 'card':
            card_number = request.form.get('card_number')
            card_cvv = request.form.get('card_cvv')
            expiry_date = request.form.get('expiry_date')
            if not card_number or not card_cvv or not expiry_date:
                flash("Please fill in all card details (Card Number, CVV, Expiry Date).", 'error')
                return redirect(url_for('checkout'))

        # If all fields are filled, proceed with the "order placed" process
        flash("Your order has been successfully placed!", 'success')
        # Typically, here you would process the payment, save the order in the database, etc.
        session.pop('cart', None)  # Empty the cart after checkout

        return redirect(url_for('checkout'))  # Redirect to the same page to show the success message

    return render_template('checkout.html', cart=cart, total_price=total_price)

@app.route('/forums', methods=['GET', 'POST'])
def forums():
    categories = Category.query.all()
    return render_template('forums.html', categories=categories)


def create_default_categories():
    # Check if categories already exist
    if not Category.query.first():  # If no categories exist, add default ones
        categories = [
            Category(name='General Discussion', description='A place for general, discussions or questions.'),
            Category(name='Introduction to Hydroponics', description='For beginners to learn about hydroponics.'),
            Category(name='Hydroponic Systems', description='Discussing different hydroponic systems like NFT, DWC, and aeroponics.'),
            Category(name='Nutrient Management', description='Learn how to manage nutrients in hydroponic farming.'),
            Category(name='Hydroponic Crops', description='Discuss the types of crops that thrive in hydroponics.'),
            Category(name='Technology in Hydroponics', description='Exploring technologies that aid hydroponic farming.'),
            Category(name='Sustainability in Hydroponics', description='Discussing how hydroponics contributes to sustainable farming.'),
            Category(name='Hydroponic Business Ideas', description='Discussing business opportunities in hydroponic farming.'),
        ]
        db.session.add_all(categories)
        db.session.commit()

def create_default_products():
    # Check if any products already exist in the database
    if not Product.query.first():  # If no products exist, add the default ones
        default_products = [
            Product(name="Hydroponic Kit", price=10, description="A complete kit for hydroponic farming.", image_url="kit.jpeg"),
            Product(name="LED Grow Light", price=8, description="High-quality LED lights for optimal plant growth.", image_url="led.jpg"),
            Product(name="pH Meter", price=5, description="Measure the pH levels in your hydroponic system.", image_url="ph.jpg"),
            Product(name="Nutrient Solution", price=4, description="Essential nutrients for hydroponic plants.", image_url="solution.png"),
            Product(name="Lettuce Seed", price=1, description="Very good lettuce seed.", image_url="lettuce.jpg"),
        ]
        db.session.add_all(default_products)
        db.session.commit()

@app.route('/category/<int:category_id>')
def view_category(category_id):
    category = Category.query.get(category_id)
    if category:
        posts = Post.query.filter_by(category_id=category_id).all()
        return render_template('category-post.html', category=category, posts=posts, category_id=category_id)
    else:
        flash("Category not found.", 'danger')
        return redirect(url_for('home'))


@app.route('/category/<int:category_id>/posts', methods=['GET', 'POST'])
def category_posts(category_id):
    category = Category.query.get_or_404(category_id)
    posts = Post.query.filter_by(category_id=category_id).all()

    # Handling the creation of a new post
    if request.method == 'POST' and 'title' in request.form and 'content' in request.form:
        title = request.form['title']
        content = request.form['content']

        # Handle user ID: if the user is logged in, use their ID; else, handle anonymous posts
        user_id = current_user.id if current_user.is_authenticated else None

        # Log the data for debugging
        app.logger.debug(f'Creating post with title: {title}, content: {content}, user_id: {user_id}, category_id: {category.id}')
        
        new_post = Post(title=title, content=content, category_id=category.id, user_id=user_id)
        db.session.add(new_post)
        db.session.commit()

        flash('Post created successfully!', 'success')
        return redirect(url_for('category_posts', category_id=category.id))

    return render_template('category-post.html', category=category, posts=posts)

@app.route("/view_post/<int:post_id>")
def view_post(post_id):
    # Get the post by ID
    post = Post.query.get_or_404(post_id)
    
    # Get all replies for this post
    replies = Reply.query.filter_by(post_id=post_id).all()
    
    return render_template('view_post.html', post=post, replies=replies)


@app.route("/reply_to_post", methods=["POST"])
def reply_to_post():
    content = request.form['reply_content']
    post_id = request.form['post_id']
    reply_author = request.form.get('reply_author')  # Get the value of the reply_author field

    # Check if the user wants to post anonymously or as themselves
    if current_user.is_authenticated:
        user_id = current_user.id  # Regular user posting
    else:
        user_id = None  # Anonymous if not logged in
    
    # Create the reply
    reply = Reply(content=content, created_at=datetime.utcnow(), user_id=user_id, post_id=post_id)
    db.session.add(reply)
    db.session.commit()
    
    return redirect(url_for('view_post', post_id=post_id))



@app.route('/dashboard')
def dashboard():
    return render_template("dashboard.html")

@app.route('/hydroponic-monitor')
def hydroponic_monitor():
    return render_template('hydroponics.html', title="Hydroponic")

@app.route('/expert')
def expert():
    return render_template('expert.html', title="Book an Expert")

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
        create_default_categories()
        create_default_products()


    app.run(debug=True)
