from flask import Flask, render_template, request, redirect, url_for, session, flash
import uuid
import os
from decimal import Decimal
import boto3
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# ----------------- AWS Setup -----------------
AWS_REGION = 'us-east-1'
dynamodb = boto3.resource('dynamodb', region_name=AWS_REGION)
sns_client = boto3.client('sns', region_name=AWS_REGION)

# DynamoDB Tables
users_table = dynamodb.Table('Users')
orders_table = dynamodb.Table('Orders')

# Replace this with your actual SNS Topic ARN
SNS_TOPIC_ARN = 'arn:aws:sns:us-east-1:796973488755:Homemade_pickles_and_snacks'

# ----------------- Gmail SMTP Setup -----------------
EMAIL_ADDRESS = 'galampriya9743@gmail.com'           # Your Gmail address
EMAIL_PASSWORD = 'ftsqhopqosluadyc'             # Gmail app password (NOT your login password)

# ----------------- Flask App -----------------
app = Flask(__name__)
app.secret_key = os.urandom(24)

# Sample product data
veg_pickles = [
    {'name': 'Tomato Pickle', 'price': 150, 'image': 'static/images/tomato.jpg'},
    {'name': 'Mango Pickle', 'price': 130, 'image': 'static/images/mango.jpg'},
    {'name': 'Lemon Pickle', 'price': 120, 'image': 'static/images/lemon.jpg'}
]

non_veg_pickles = [
    {'name': 'Chicken Pickle', 'price': 250, 'image': 'static/images/chicken.jpg'},
    {'name': 'Mutton Pickle', 'price': 300, 'image': 'static/images/mutton.jpg'}
]

snacks = [
    {'name': 'Mixture', 'price': 60, 'image': 'static/images/mixture.jpg'},
    {'name': 'Murukku', 'price': 50, 'image': 'static/images/murukku.jpg'}
]

# ------------------ Routes ------------------

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/veg_pickles')
def veg_pickles_page():
    return render_template('veg_pickles.html', items=veg_pickles)

@app.route('/non_veg_pickles')
def non_veg_pickles_page():
    return render_template('non_veg_pickles.html', items=non_veg_pickles)

@app.route('/snacks')
def snacks_page():
    return render_template('snacks.html', items=snacks)

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/contactus')
def contactus():
    return render_template('contactus.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        full_name = request.form['full_name']
        email = request.form['email'].lower()
        password = request.form['password']

        resp = users_table.get_item(Key={'email': email})
        if 'Item' in resp:
            flash('Email already registered.', 'danger')
            return redirect(url_for('signup'))

        user_id = str(uuid.uuid4())
        users_table.put_item(Item={
            'email': email,
            'full_name': full_name,
            'password': password,
            'user_id': user_id
        })

        flash('Signup successful. Please log in.', 'success')
        return redirect(url_for('login'))

    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email'].lower()
        password = request.form['password']

        resp = users_table.get_item(Key={'email': email})
        user = resp.get('Item')

        if user and user['password'] == password:
            session['user'] = {
                'email': user['email'],
                'full_name': user['full_name'],
                'user_id': user['user_id']
            }
            flash(f'Welcome back, {user["full_name"]}!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Invalid email or password.', 'danger')
            return redirect(url_for('login'))

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user', None)
    flash('Logged out successfully.', 'info')
    return redirect(url_for('index'))

@app.route('/cart')
def cart():
    if 'cart' not in session:
        session['cart'] = []
    total = sum(item['price'] * item['quantity'] for item in session['cart'])
    return render_template('cart.html', cart=session['cart'], total=total)

@app.route('/add_to_cart', methods=['POST'])
def add_to_cart():
    item_name = request.form.get('item_name')
    price = float(request.form.get('price'))
    image = request.form.get('image')
    quantity = int(request.form.get('quantity'))

    if 'cart' not in session:
        session['cart'] = []

    session['cart'].append({
        'item': item_name,
        'price': price,
        'image': image,
        'quantity': quantity
    })
    session.modified = True
    return redirect(url_for('cart'))

@app.route('/remove_from_cart', methods=['POST'])
def remove_from_cart():
    index = request.form.get('index')
    if index is not None:
        index = int(index)
        if 'cart' in session and 0 <= index < len(session['cart']):
            session['cart'].pop(index)
            session.modified = True
    return redirect(url_for('cart'))

@app.route('/checkout', methods=['GET', 'POST'])
def checkout():
    if 'cart' not in session or not session['cart']:
        flash('Your cart is empty. Add items before checkout.', 'warning')
        return redirect(url_for('cart'))

    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email').lower()
        phone = request.form.get('phone')
        address = request.form.get('address')
        order_id = str(uuid.uuid4())

        cart_items = []
        for item in session['cart']:
            cart_items.append({
                'item': item['item'],
                'price': Decimal(str(item['price'])),
                'image': item['image'],
                'quantity': item['quantity']
            })

        orders_table.put_item(Item={
            'order_id': order_id,
            'email': email,
            'name': name,
            'phone': phone,
            'address': address,
            'items': cart_items
        })

        message_text = f"Thank you {name} for your order! Your order ID is {order_id}."

        # Always send both SNS and Gmail
        send_sns_email(subject="Order Confirmation", body=message_text)
        send_gmail_email(to_email=email, subject="Order Confirmation", body=message_text)

        session.pop('cart', None)
        flash('Order placed successfully!', 'success')
        return redirect(url_for('success'))

    return render_template('checkout.html')

@app.route('/success')
def success():
    return render_template('success.html')

@app.route('/search', methods=['GET'])
def search():
    query = request.args.get('query', '').strip().lower()
    results = []
    for item in veg_pickles + non_veg_pickles + snacks:
        if query in item['name'].lower():
            results.append(item)
    return render_template('search_results.html', query=query, results=results)

# ---------------- Email Sending Functions ----------------
def send_sns_email(subject, body):
    sns_client.publish(
        TopicArn=SNS_TOPIC_ARN,
        Message=body,
        Subject=subject
    )

def send_gmail_email(to_email, subject, body):
    msg = MIMEMultipart()
    msg['From'] = EMAIL_ADDRESS
    msg['To'] = to_email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    with smtplib.SMTP('smtp.gmail.com', 587) as smtp:
        smtp.starttls()
        smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        smtp.send_message(msg)

# ---------------- Run the App ----------------
if __name__ == '__main__':
    print(f"✅ Flask app running with SNS + Gmail SMTP in region: {AWS_REGION}")
    app.run(debug=True, host='0.0.0.0', port=5000)
