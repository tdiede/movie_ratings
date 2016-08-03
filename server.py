"""Movie Ratings."""

from jinja2 import StrictUndefined

from flask import (Flask, render_template, redirect, request, make_response, flash, session)
from flask_debugtoolbar import DebugToolbarExtension

from model import User, Rating, Movie, connect_to_db, db


app = Flask(__name__)

# Required to use Flask sessions and the debug toolbar
app.secret_key = "ABC"

# Normally, if you use an undefined variable in Jinja2, it fails
# silently. This is horrible. Fix this so that, instead, it raises an
# error.
app.jinja_env.undefined = StrictUndefined


@app.route('/')
def index():
    """Homepage."""

    return render_template("homepage.html")


@app.route('/users')
def user_list():
    """Show list of users."""

    users = User.query.all()
    return render_template("user_list.html", users=users)


@app.route('/register', methods=['GET'])
def register_form():
    """New users can create an account."""

    return render_template("register_form.html")


@app.route('/register', methods=['POST'])
def register_process():
    """New users can create an account."""

    email_form_input = request.form['email']
    password_form_input = request.form['password']

    db_email_query = User.query.filter(User.email == email_form_input)
    
    # New user. Needs to register. Automatically registers.
    if db_email_query.first() == None:
        new_user_email = User(email=email_form_input, password=password_form_input)
        db.session.add(new_user_email)
        db.session.commit()
        flash('You have now been registered.')
        return redirect('/')
    # Returning user. Needs to login and enter homepage.
    else:
        # Handling login.
        loggedin_user = db_email_query.one()
        session['user_login'] = loggedin_user.user_id
        flash('You are already registered. You are logged.')
        return redirect('/')


@app.route('/login', methods=['GET'])
def login_form():
    """Registered users can log in."""

    return render_template("login_form.html")


@app.route('/login', methods=['POST'])
def login_process():
    """Registered users can log in."""

    login_email_form = request.form['email']
    login_password_form = request.form['password']

    db_login_query = User.query.filter(User.email == login_email_form)

    if db_login_query.first() == None:
        flash('You are not a current user. Please create a new account or enter your email again.')
        return redirect('/register')
    elif db_login_query.one().password != login_password_form:
        flash('Incorrect password. Please try again.')
        return redirect('/login')
    else:
        loggedin_user = db_login_query.one()
        session['user_login'] = loggedin_user.user_id
        flash('You are now logged in. You are user # %d' % (session['user_login']))
        return redirect('/')


@app.route('/logout', methods=['POST'])
def logout_process():
    """Registered users can log out."""

    session.clear()
    flash('You are now logged out.')
    return redirect('/')


if __name__ == "__main__":
    # We have to set debug=True here, since it has to be True at the
    # point that we invoke the DebugToolbarExtension
    app.debug = True

    connect_to_db(app)

    # Use the DebugToolbar
    DebugToolbarExtension(app)

    app.run()
