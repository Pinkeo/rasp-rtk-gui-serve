import eventlet
eventlet.monkey_patch()

from flask import Flask, render_template, flash, url_for, redirect, request, jsonify
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
socketio = SocketIO(app, cors_allowed_origins="*",logger=True, engineio_logger=True)


#MAPBOX for satellite view
MAPBOX_ACCESS_TOKEN = os.getenv('MAPBOX_ACCESS_TOKEN') 
@app.route('/mapbox_token')
def mapbox_token():
    return jsonify({'token': MAPBOX_ACCESS_TOKEN})






# Google Sheets API credentials
#GOOGLE_SHEET_CREDS = os.getenv('GOOGLE_SHEET_CREDS')
#GOOGLE_SHEET_NAME = os.getenv('GOOGLE_SHEET_NAME') 


# Initialize Google Sheets API
#scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
#creds = ServiceAccountCredentials.from_json_keyfile_name(GOOGLE_SHEET_CREDS, scope)
#client = gspread.authorize(creds)
#sheet = client.open(GOOGLE_SHEET_NAME).sheet1


app.secret_key = os.getenv('KEY')
secret_key = os.getenv('KEY')
app.config['SQLALCHEMY_DATABASE_URI'] = (
    f"mysql+pymysql://{os.getenv('DB_USERNAME')}:{os.getenv('DB_PASSWORD')}"
    f"@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False


# Initialize SQLAlchemy
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'


# user model
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


    def __repr__(self):
        return f"User('{self.username}', '{self.email}', '{self.image_file}')"


# Registration form
class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Sign Up')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('That username is taken. Please choose a different one.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('That email is taken. Please choose a different one.')

# Login form
class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Login')



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


gps_data = {}
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
