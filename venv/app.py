from flask import Flask, render_template, jsonify, request, redirect, url_for
import json
import os
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

# Database setup
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'  # SQLite database
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(80), nullable=False)
    secret_question = db.Column(db.String(120), nullable=False)
    secret_answer = db.Column(db.String(120), nullable=False)

# Use app.app_context() to create an application context
with app.app_context():
# Create the database tables
    db.create_all()


# register user
    
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        secret_question = request.form['secret_question']
        secret_answer = request.form['secret_answer']

        # Validate username and password
        if len(password) < 6:
            return render_template('register.html', error="Password should be at least 6 characters long.")

        if User.query.filter_by(username=username).first():
            return render_template('register.html', error="Username already exists.")

        new_user = User(username=username, password=password, secret_question=secret_question, secret_answer=secret_answer)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('login'))

    return render_template('register.html', error=None)

# login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Validate username and password
        if len(password) < 6:
            return render_template('register.html', error="Password should be at least 6 characters long.")
        # Verify username and password
        user = User.query.filter_by(username=username, password=password).first()
        if user:
            return redirect(url_for('index', username=username, welcome_message=f"Welcome {username}!"))
        else:
            return render_template('login.html', error="Invalid username or password.")

    return render_template('login.html', error=None)

# forgot password 
@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        username = request.form['username']
        secret_question = request.form['secret_question']
        secret_answer = request.form['secret_answer']

        user = User.query.filter_by(username=username, secret_question=secret_question, secret_answer=secret_answer).first()
        if user:
        # Redirect the user to the password reset page
            return redirect(url_for('reset_password', username=username))
        else:
            return render_template('reset_password.html', error="Invalid credentials.")

    return render_template('forgot_password.html', error=None)

# reset password
@app.route('/reset_password/<username>', methods=['GET', 'POST'])
def reset_password(username):
    if request.method == 'POST':
        username = request.form['username']
        new_password = request.form['new_password']

        # Update the user's password here
        user = User.query.filter_by(username=username).first()
        user.password = new_password
        db.session.commit()

        return redirect(url_for('login'))

    return render_template('reset_password.html', error=None, username=username)

# Load data from JSON file
with open('weather_data.json', 'r') as f:
    data = json.load(f)

@app.route('/')
def index():
    return render_template('index.html', data=data)

@app.route('/all_reports/')
def all_reports():
    return render_template('all_reports.html')

@app.route('/reports/<station_name>')
def station_report(station_name):
    for item in data:
        if item['Station'] == station_name:
            if 'generated_report' in item:
                report = item['generated_report']
                return render_template('report.html',station_name= station_name, report=report)
            else:
                return f"No report found for {station_name}"
    return f"No data found for {station_name}"


@app.route('/graph/')
def graph():
    return render_template('graph.html')

@app.route('/data')
def get_data():
    with open('weather_data.json', 'r') as f:
        data = json.load(f)
    return jsonify(data)

if __name__ == '__main__':
    app.run(debug=True)
