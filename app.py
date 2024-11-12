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

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(120), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    role = db.Column(db.String(50))
    address = db.Column(db.String(200))
    phone = db.Column(db.String(20))
    profile_image_url = db.Column(db.String(200), nullable=True)
    profile_complete = db.Column(db.Boolean, default=False)

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

class Expert(db.Model):
    __tablename__ = 'experts'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    profile_picture = db.Column(db.String(255), nullable=True)  # URL to profile picture
    specialization = db.Column(db.String(100), nullable=False)
    bio = db.Column(db.Text, nullable=True)
    
    bookings = db.relationship("Booking", back_populates="expert", overlaps="expert_ref")

    def __repr__(self):
        return f'<Expert {self.name}>'

class Booking(db.Model):
    __tablename__ = 'bookings'
    
    id = db.Column(db.Integer, primary_key=True)
    session_datetime = db.Column(db.DateTime, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    expert_id = db.Column(db.Integer, db.ForeignKey('experts.id'), nullable=False)
    status = db.Column(db.String(50), default='Pending')  # Added for managing status
    
    user = db.relationship('User', backref='user_bookings')  # Unique backref for User
    expert = db.relationship("Expert", back_populates="bookings", overlaps="expert_ref")

    def __repr__(self):
        return f'<Booking {self.session_datetime} with Expert {self.expert_id}>'

class Message(db.Model):
    __tablename__ = 'messages'

    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    reply = db.Column(db.Text, nullable=True)  # New field for replies
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    expert_id = db.Column(db.Integer, db.ForeignKey('experts.id'), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    expert = db.relationship('Expert', backref=db.backref('messages', lazy=True))
    user = db.relationship('User', backref=db.backref('messages', lazy=True))

    def __repr__(self):
        return f'<Message from User {self.user_id} to Expert {self.expert_id}>'

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
def create_default_experts():
    # Check if any experts already exist in the database
    if not Expert.query.first():  # If no experts exist, add the default ones
        default_experts = [
            Expert(
                name="Jane Umuhoza",
                profile_picture='/static/img/jane.jpg',
                specialization="Sustainable Agriculture",
                bio="Jane specializes in sustainable farming practices and has been helping farmers for over a decade."
            ),
            Expert(
                name="Mark Muhire",
                profile_picture='/static/img/mark.jpg',
                specialization="Hydroponics",
                bio="Mark is an expert in hydroponic farming systems, focusing on improving water use efficiency in agriculture."
            ),
            Expert(
                name="Emily Keza",
                profile_picture='/static/img/emily.jpg',
                specialization="Horticulture",
                bio="Emily is a horticulturist with expertise in plant cultivation and advanced growing techniques."
            )
        ]
        # Add experts to the session and commit
        db.session.add_all(default_experts)
        db.session.commit()

def create_default_expert_users():
    # Define the default expert users
    default_experts = [
        {"username": "Jane Umuhoza", "email": "jane@gmail.com", "password": "password123", "role": "expert"},
        {"username": "Mark Muhire", "email": "mark@gmail.com", "password": "password123", "role": "expert"},
        {"username": "Emily keza", "email": "emily@gmail.com", "password": "password123", "role": "expert"},
    ]

    # Add each expert to the database if they don't already exist
    for expert in default_experts:
        user = User.query.filter_by(username=expert["username"]).first()
        if user is None:
            user = User(
                username=expert["username"],
                email=expert["email"],
                role=expert["role"]
            )
            user.set_password(expert["password"])  # Hash and set the password
            db.session.add(user)
    
    # Commit the new users to the database
    db.session.commit()


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

@app.route('/add_to_cart', methods=['POST'])
def add_to_cart():
    # Retrieve the product ID and quantity from the form
    product_id = request.form.get('product_id')
    quantity = request.form.get('quantity', 1)

    # Convert quantity to an integer and check for valid values
    try:
        quantity = int(quantity)
        if quantity <= 0:
            raise ValueError("Quantity must be positive")
    except ValueError:
        flash("Invalid quantity provided.", "error")
        return redirect(url_for('market'))  # Redirect to market page if there's an issue

    # Check if the product ID is valid and exists in the database
    product = Product.query.get(product_id)
    if product:
        # Ensure the 'cart' key exists in the session
        if 'cart' not in session:
            session['cart'] = []
        
        # Check if the product is already in the cart
        existing_product = next((item for item in session['cart'] if item['product_id'] == product.id), None)
        if existing_product:
            # If the product is already in the cart, just update the quantity
            existing_product['quantity'] += quantity
        else:
            # If the product is not in the cart, add it
            session['cart'].append({
            'product_id': product.id,
            'name': product.name,
            'price': product.price,
            'quantity': quantity,
            'total_price': product.price * quantity  # Adding total price directly to the cart
        })
        
        session.modified = True  # Mark the session as modified
        flash("Product added to cart!", "success")
    else:
        flash("Product not found.", "error")

    return redirect(url_for('market'))  # Redirect to market page after adding to cart


@app.route('/remove_from_cart', methods=['POST'])
def remove_from_cart():
    product_id = int(request.form['product_id'])
    
    # Remove the product from the cart by filtering out the item with the matching product_id
    session['cart'] = [item for item in session.get('cart', []) if item['product_id'] != product_id]
    
    # Ensure changes are saved to the session
    session.modified = True
    
    flash("Product removed from cart!", "success")
    return redirect(url_for('cart'))

@app.route('/cart')
def cart():
    # Retrieve cart items from the session
    cart_items = session.get('cart', [])
    updated_cart = []

    # Retrieve product details for each item in the cart from the database
    total_price = 0
    for item in cart_items:
        product = Product.query.get(item['product_id'])
        if product:
            item_total = product.price * item['quantity']
            total_price += item_total
            updated_cart.append({
                'product_id': product.id,
                'name': product.name,
                'price': product.price,
                'quantity': item['quantity'],
                'total_price': item_total
            })

    # Pass the updated cart and total price to the template
    return render_template('cart.html', cart=updated_cart, total_price=total_price)

@app.route('/checkout', methods=['GET', 'POST'])
def checkout():
    # Retrieve cart items from session
    cart = session.get('cart', [])
    total_price = sum(item['price'] * item['quantity'] for item in cart)

    if request.method == 'POST':
        # Get form data
        full_name = request.form.get('full_name')
        address = request.form.get('address')
        phone = request.form.get('phone')
        payment_method = request.form.get('payment_method')

        # Validate Mobile Money payment
        if payment_method == 'mobile_money':
            momo_number = request.form.get('momo_number')
            if not momo_number:
                flash("Please enter your mobile number for Mobile Money payment.", 'error')
                return redirect(url_for('checkout'))

        # Validate Card payment
        elif payment_method == 'card':
            card_number = request.form.get('card_number')
            card_cvv = request.form.get('card_cvv')
            expiry_date = request.form.get('expiry_date')
            if not card_number or not card_cvv or not expiry_date:
                flash("Please fill in all card details (Card Number, CVV, Expiry Date).", 'error')
                return redirect(url_for('checkout'))

        # If payment details are valid, process the order
        flash("Your order has been successfully placed!", 'success')

        # Save order details in a temporary dictionary
        order_details = {
            'full_name': full_name,
            'address': address,
            'phone': phone,
            'payment_method': payment_method,
            'cart_items': cart,
            'total_price': total_price,
        }

        # Clear the cart after successful checkout
        session.pop('cart', None)

        # Redirect to the order confirmation page
        return redirect(url_for('order_confirmation'))

    # Render the checkout page with the cart items and total price
    return render_template('checkout.html', cart=cart, total_price=total_price)

@app.route('/order_confirmation', methods=['GET'])
def order_confirmation():
    return render_template('order_confirmation.html')

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
        # Handle registration
        if request.form.get('form_type') == 'register':
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

        elif request.form.get('form_type') == 'login':
            user = User.query.filter_by(email=request.form['email']).first()
            if user and user.check_password(request.form['password']):
                login_user(user)

                # Redirect based on the user's role and profile completion status
                if not user.profile_complete:
                    if user.role == 'farmer':
                        return redirect(url_for('profile'))
                    elif user.role == 'expert':
                        return redirect(url_for('expert_profile'))

                # Check role and redirect accordingly
                if user.role == 'farmer':
                    return redirect(url_for('dashboard'))
                elif user.role == 'expert':
                    return redirect(url_for('expert_dashboard'))  # Redirect to expert_booking

            flash("Invalid credentials", "error")
            return redirect(url_for('login'))

    # For GET request, simply render the login page
    return render_template('login.html')

@app.route('/expert-profile', methods=['GET', 'POST'])
@login_required
def expert_profile():
    if request.method == 'POST':
        # Get form data
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
                os.makedirs(os.path.dirname(filepath), exist_ok=True)  # Ensure directory exists
                file.save(filepath)
                current_user.profile_image_url = f"/static/uploads/{filename}"
            else:
                flash("Invalid image format. Allowed formats are png, jpg, jpeg, and gif.", "error")

        # Update user data and mark profile as complete
        current_user.username = username
        current_user.email = email
        current_user.address = address
        current_user.phone = phone
        current_user.profile_complete = True
        db.session.commit()  # Save changes to the database

        flash("Profile updated successfully!", "success")
        return redirect(url_for('expert_dashboard'))  # Redirect after update

    return render_template('expert-profile.html', user=current_user)

@app.route('/expert-reply_message/<int:message_id>', methods=['POST'])
@login_required
def expert_reply_message(message_id):
    expert_id = current_user.id
    message = Message.query.get_or_404(message_id)
    
    if message.expert_id != expert_id:
        flash('You are not authorized to reply to this message.', 'danger')
        return redirect(url_for('expert_dashboard'))

    reply_content = request.form.get('reply_content')
    
    if reply_content:
        message.reply = reply_content  # Save the reply in the message
        db.session.commit()

        flash('Your reply has been sent!', 'success')
        return redirect(url_for('expert_dashboard'))
    else:
        flash('Please enter a reply to send.', 'danger')
        return redirect(url_for('expert_dashboard'))

@app.route('/update_booking_status/<int:booking_id>/<status>', methods=['POST'])
@login_required
def update_booking_status(booking_id, status):
    expert_id = current_user.id
    booking = Booking.query.get_or_404(booking_id)

    if booking.expert_id != expert_id:
        flash('You are not authorized to modify this booking.', 'danger')
        return redirect(url_for('expert_dashboard'))

    if status not in ['Accepted', 'Denied']:
        flash('Invalid status.', 'danger')
        return redirect(url_for('expert_dashboard'))

    booking.status = status
    db.session.commit()

    flash(f'Booking has been {status.lower()}!', 'success')

    # You can add email notifications here if you want to notify the user about the status change
    return redirect(url_for('expert_dashboard'))

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        # Get form data
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
                os.makedirs(os.path.dirname(filepath), exist_ok=True)  # Ensure directory exists
                file.save(filepath)
                current_user.profile_image_url = f"/static/uploads/{filename}"
            else:
                flash("Invalid image format. Allowed formats are png, jpg, jpeg, and gif.", "error")

        # Update user data and mark profile as complete
        current_user.username = username
        current_user.email = email
        current_user.address = address
        current_user.phone = phone
        current_user.profile_complete = True
        db.session.commit()  # Save changes to the database

        flash("Profile updated successfully!", "success")
        return redirect(url_for('dashboard'))  # Redirect after update

    return render_template('profile.html', user=current_user)

@app.route('/forums', methods=['GET', 'POST'])
def forums():
    categories = Category.query.all()
    return render_template('forums.html', categories=categories)

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

@app.route('/settings', methods=['GET', 'POST'])
@login_required
def account_settings():
    if request.method == 'POST':
        # Handle the change password functionality
        if 'change_password' in request.form:
            current_password = request.form.get('current_password')
            new_password = request.form.get('new_password')
            confirm_password = request.form.get('confirm_password')

            # Verify current password
            if not current_user.check_password(current_password):
                flash('Incorrect current password.', 'error')
            elif new_password != confirm_password:
                flash('New password and confirmation do not match.', 'error')
            else:
                # Update password
                current_user.set_password(new_password)
                db.session.commit()
                flash('Password updated successfully.', 'success')

        # Handle the delete account functionality
        elif 'delete_profile' in request.form:
            db.session.delete(current_user)
            db.session.commit()
            flash('Your account has been deleted successfully.', 'success')
            return redirect(url_for('login'))  # Redirect to the login page after deletion

        return redirect(url_for('account_settings'))  # Ensure the function name matches here

    return render_template('settings.html', user=current_user)  # Template rendering
@app.route('/help')
def help():   
    return render_template('help.html', title="Help")





@app.route('/help/contact', methods=['POST'])
@login_required
def send_support():
    # Handle form data
    name = request.form.get('name')
    email = request.form.get('email')
    message = request.form.get('message')

    # Send an email or store it in the database (this is a placeholder)
    # For now, let's just flash a success message
    flash('Your message has been sent successfully. Our team will get back to you shortly.', 'success')

    # You can also add logic to send the email or store the message
    # Example: send_email(name, email, message)

    return redirect(url_for('help'))  # Redirect back to the help page


@app.route('/expert', methods=['GET', 'POST'])
def expert():
    experts = Expert.query.all()

    if request.method == 'POST':
        expert_id = request.form.get('expert_id')
        session_date = request.form.get('session_date')
        session_time = request.form.get('session_time')
        
        session_datetime = datetime.strptime(f"{session_date} {session_time}", '%Y-%m-%d %H:%M')
        
        user_id = 1  # Replace with the actual logged-in user's ID

        new_booking = Booking(user_id=user_id, expert_id=expert_id, session_datetime=session_datetime)
        db.session.add(new_booking)
        db.session.commit()
        
        flash('Your session has been successfully booked!', 'success')
        return redirect(url_for('expert'))

    return render_template('expert.html', experts=experts)

@app.route('/send_message/<int:expert_id>', methods=['POST'])
@login_required  # Assuming you're using login_required to check if the user is logged in
def send_message(expert_id):
    user_id = current_user.id  # Assuming you're using Flask-Login for user management
    message_content = request.form.get('message_content')
    
    if message_content:
        # Create a new message in the database
        message = Message(user_id=user_id, expert_id=expert_id, content=message_content)
        db.session.add(message)
        db.session.commit()

        flash('Your message has been sent!', 'success')
        return redirect(url_for('expert'))  # Redirect back to the expert list page
    else:
        flash('Please enter a message to send.', 'danger')
        return redirect(url_for('expert'))

@app.route('/expert-dashboard')
@login_required
def expert_dashboard():
    expert_id = current_user.id  # Assuming the logged-in user is the expert and using Flask-Login
    # Fetch the expert's bookings and messages
    bookings = Booking.query.filter_by(expert_id=expert_id).all()
    messages = Message.query.filter_by(expert_id=expert_id).all()
    
    return render_template('expert-bookings.html', bookings=bookings, messages=messages)

@app.route('/dashboard')
def dashboard():
    return render_template("dashboard.html")

@app.route('/logout')
def logout():   
    return render_template('login.html', title="Logout")


@app.route('/expert-settings', methods=['GET', 'POST'])
@login_required
def expert_account_settings():
    if request.method == 'POST':
        # Handle the change password functionality
        if 'change_password' in request.form:
            current_password = request.form.get('current_password')
            new_password = request.form.get('new_password')
            confirm_password = request.form.get('confirm_password')

            # Verify current password
            if not current_user.check_password(current_password):
                flash('Incorrect current password.', 'error')
            elif new_password != confirm_password:
                flash('New password and confirmation do not match.', 'error')
            else:
                # Update password
                current_user.set_password(new_password)
                db.session.commit()
                flash('Password updated successfully.', 'success')

        # Handle the delete account functionality
        elif 'delete_profile' in request.form:
            db.session.delete(current_user)
            db.session.commit()
            flash('Your account has been deleted successfully.', 'success')
            return redirect(url_for('login'))  # Redirect to the login page after deletion

        return redirect(url_for('expert_account_settings'))  # Ensure the function name matches here

    return render_template('expert-settings.html', user=current_user)  # Template rendering

@app.route('/expert-help')
def expert_help():   
    return render_template('expert-help.html', title="Help")

@app.route('/expert-help/contact', methods=['POST'])
@login_required
def expert_send_support():
    name = request.form.get('name')
    email = request.form.get('email')
    message = request.form.get('message')
    flash('Your message has been sent successfully. Our team will get back to you shortly.', 'success')
    return redirect(url_for('expert_help')) 

@app.route('/expert-forums', methods=['GET', 'POST'])
def expert_forums():
    categories = Category.query.all()
    return render_template('expert-forums.html', categories=categories)

@app.route('/expert-category/<int:category_id>')
def expert_view_category(category_id):
    category = Category.query.get(category_id)
    if category:
        posts = Post.query.filter_by(category_id=category_id).all()
        return render_template('expert-category-post.html', category=category, posts=posts, category_id=category_id)
    else:
        flash("Category not found.", 'danger')
        return redirect(url_for('bookings'))


@app.route('/expert-category/<int:category_id>/posts', methods=['GET', 'POST'])
def expert_category_posts(category_id):
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
        return redirect(url_for('expert_category_posts', category_id=category.id))

    return render_template('expert-category-post.html', category=category, posts=posts)

@app.route("/expert-view_post/<int:post_id>")
def expert_view_post(post_id):
    # Get the post by ID
    post = Post.query.get_or_404(post_id)
    
    # Get all replies for this post
    replies = Reply.query.filter_by(post_id=post_id).all()
    
    return render_template('expert-view_post.html', post=post, replies=replies)


@app.route("/expert-reply_to_post", methods=["POST"])
def expert_reply_to_post():
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
    
    return redirect(url_for('expert_view_post', post_id=post_id))


if __name__ == '__main__':
    # Initialize database
    with app.app_context():
        db.create_all()  # This will create tables if they don't exist
        create_default_categories()
        create_default_products()
        create_default_experts()
        create_default_expert_users()

    app.run(debug=True)
