from flask import Flask, render_template, redirect, url_for, request, session, flash
from flask_pymongo import PyMongo
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os
import json
import requests
from flask_pymongo import ObjectId
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user

ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])
app = Flask(__name__)
app.config['SECRET_KEY'] = 'Thehobby'
app.config['MONGO_URI'] = 'mongodb+srv://durgesh:Thehobby@cluster0.cieshmm.mongodb.net/<aboot>'
app.config['UPLOAD_FOLDER'] = os.path.join('static/profiles')
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
mongo = PyMongo(app)

login_manager = LoginManager(app)
login_manager.login_view = 'login'

class User(UserMixin):
    def __init__(self, user_data):
        self.id = str(user_data['_id'])
        self.username = user_data['username']


@login_manager.user_loader
def load_user(user_id):
    user_data = mongo.db.users.find_one({'_id': ObjectId(user_id)})
    if user_data:
        return User(user_data)
    return None

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS



@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form.get('username')      
        password = request.form.get('password')
        email = request.form.get('email')
        contact = request.form.get('contact')
        address = request.form.get('address')
        profile_pic = request.files.get('profile_pic')
        

        if None in [username, password, email,contact, address,profile_pic]:
            flash('Please fill in all required fields.', 'danger')
        elif mongo.db.users.find_one({'username': username}):
            flash('Username already exists. Please choose another one.', 'danger')
        else:
            hashed_password = generate_password_hash(password)

            if profile_pic:
                filename = secure_filename(profile_pic.filename)
                save_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                profile_pic.save(save_path)

            user_data = {
                'username': username,
                'password': hashed_password,
                'email': email,
                'contact':contact,
                'address':address,
                'profile_pic': filename,    
                'upload_folder': app.config['UPLOAD_FOLDER']
            }

            mongo.db.users.insert_one(user_data)
            flash('Account created successfully. You can now log in.', 'success')
            return redirect(url_for('login'))

    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = mongo.db.users.find_one({'username': username})

        if user and check_password_hash(user['password'], password):
            login_user(User(user))
            flash('Logged in successfully!', 'success')
            return redirect(url_for('get_books'))
        else:
            flash('Invalid username or password. Please try again.', 'danger')

    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out successfully!', 'success')
    return redirect(url_for('login'))



json_url = "https://raw.githubusercontent.com/ozlerhakan/mongodb-json-files/master/datasets/books.json"
@app.route('/', methods=['GET'])
@login_required
def get_books():
    user_data = mongo.db.users.find_one({'username': current_user.username})
         
    response = requests.get(json_url)
    if response.status_code == 200:
        data = response.text
        json_objects = data.strip().split('\n')
        books = [json.loads(obj) for obj in json_objects[26:81]]
        return render_template('books.html', books=books, user=user_data) 
    else:
        return f"Failed to fetch books. Status code: {response.status_code}"

import time
RAZORPAY_API_KEY = 'rzp_test_Juy90wtG6xMCDX' 
@login_required
@app.route('/checkout')
def buy():
    user_data = None  # Default to None if the user is not authenticated

    if current_user.is_authenticated:
        user_data = mongo.db.users.find_one({'username': current_user.username})

        if user_data:
            image_path = os.path.join('profiles', user_data.get('profile_pic', 'default.jpg')).replace('\\', '/')
            return render_template('checkout.html', user=user_data, image_path=image_path)


    book_title = request.args.get('book')
    book_price = request.args.get('price')
    book_thumbnail = request.args.get('thumbnail')

 
    order_payload = {
        'amount': int(float(book_price) * 100), 
        'currency': 'INR',  
        'receipt': 'order_receipt_' + str(int(time.time())),
        'payment_capture': 1
    }

    order_response = requests.post('https://api.razorpay.com/v1/orders', json=order_payload, auth=(RAZORPAY_API_KEY, ''))

    if order_response.status_code == 200:
        order_data = order_response.json()
        return render_template('checkout.html', user=user_data, image_path=image_path,
                               book_title=book_title, book_price=book_price,
                               book_thumbnail=book_thumbnail, razorpay_order_id=order_data['id'],
                               razorpay_key=RAZORPAY_API_KEY)

    return render_template('checkout.html', user=user_data)


@app.route('/about')
def about():
 user_data = None 
 
 if current_user.is_authenticated:
        user_data = mongo.db.users.find_one({'username': current_user.username})

        if user_data:
            image_path = os.path.join('profiles', user_data.get('profile_pic', 'default.jpg')).replace('\\', '/')
            return render_template('about.html', user=user_data, image_path=image_path)

 return render_template('about.html')

if __name__ == '__main__':
    app.run(debug=True) 
