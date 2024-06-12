
import eventlet
eventlet.monkey_patch()
from flask import Flask, render_template, url_for, redirect, request, jsonify

from flask_socketio import SocketIO, emit
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os
from flask_wtf import FlaskForm
from flask_login import login_user, current_user, logout_user, login_required
from flask_login import LoginManager, UserMixin, login_user, current_user, logout_user, login_required
from wtforms import StringField, PasswordField, SubmitField, BooleanField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError
from dotenv import load_dotenv
from oauth2client.service_account import ServiceAccountCredentials
from werkzeug.security import generate_password_hash, check_password_hash
import gspread
from flask_bcrypt import Bcrypt

load_dotenv()
app = Flask(__name__)
socketio = SocketIO(app)
socketio = SocketIO(app, cors_allowed_origins="*",logger=True, engineio_logger=True)

@app.route('/')
def home():
    if current_user.is_authenticated:
        return render_template('index.html')
    else:
        return render_template('about.html')

@app.route('/about')
def about():
    return render_template('about.html')


@app.route('/submit', methods=['POST'])
def submit():
    name = request.form.get('name')
    flash('Thank you for contacting us, Your message is being delivered')
    return redirect(url_for('home'))



@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = generate_password_hash(form.password.data, method='pbkdf2:sha256')
        user = User(username=form.username.data, email=form.email.data, password=hashed_password)
        db.session.add(user)
        db.session.commit()
        flash('Your account has been created! You are now able to log in', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)

@app.route("/login", methods=['GET', 'POST'])
def login():
  #  if current_user.is_authenticated:
   #     return redirect(url_for('home'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            return redirect(url_for('home'))
        else:
            flash('Login Unsuccessful. Please check email and password', 'danger')
    return render_template('login.html', title='Login', form=form)

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))

@app.route("/profile")
@login_required
def profile():
    return render_template('profile.html')

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        # Collect form data
        name = request.form['name']
        email = request.form['email']
        message = request.form['message']
        
       # Generate current timestamp
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # Append data to Google Sheet, including the timestamp
        row = [timestamp, name, email, message]
        sheet.append_row(row)

        flash('Your message has been sent!', 'success')
        return redirect(url_for('home'))
    
    return render_template('about.html')

@app.before_request
def create_tables():
    db.create_all()





@app.route('/gps_data', methods=['GET'])
def get_gps_data():
    return jsonify(gps_data)

@socketio.on('connect')
def handle_connect():
    print('Client connected')

@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')

@socketio.on('gps_data')
def handle_gps_data(json_data):
    global gps_data
    gps_data = json_data
    print('Received GPS data:', gps_data)  # Log received GPS data
    emit('update_map', gps_data, broadcast=True)

if __name__ == '__main__':
    socketio.run(app, debug=True, host='0.0.0.0', port=5000,cors_allowed_origins='*',async_mode='eventlet')
