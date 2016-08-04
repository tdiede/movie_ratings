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

@app.route('/users/<int:user_id>')
def user_profile(user_id):
    """Show user profile."""

    user_ratings = {}
    user_title_score = []

    user = User.query.get(user_id)
    ratings = user.ratings
    for rating in ratings:
        title = rating.movie.title
        user_ratings[title] = rating.score
    for title in sorted(user_ratings.keys()):
        title_score = (title, user_ratings[title])
        user_title_score.append(title_score)

    # movie_information.html
    return render_template("user_information.html", user=user, user_title_score=user_title_score)


@app.route('/register', methods=['GET'])
def register_form():
    """New users can create an account."""

    return render_template("register_form.html")


@app.route('/register', methods=['POST'])
def register_process():
    """New users can create an account."""

    email_form_input = request.form['email']
    password_form_input = request.form['password']

    db_query_by_email = User.query.filter(User.email == email_form_input)
    
    # New user. Needs to register. Automatically registers.
    if db_query_by_email.first() == None:
        new_user_email = User(email=email_form_input, password=password_form_input)
        db.session.add(new_user_email)
        db.session.commit()
        flash('You have now been registered.')
        return redirect('/profile')
    # Handling login. Checking email and password match.
    elif db_query_by_email.first().email == email_form_input and db_query_by_email.first().password == password_form_input:
        session['user_login'] = db_query_by_email.first().user_id
        flash('You are already registered. You are logged in.')
        return redirect('/profile')
    # Returning user, incorrect password. Needs to login via login page.
    else:
        flash('You are a registered user but your password is incorrect. Please login with the correct password.')
        return redirect('/login')


@app.route('/login', methods=['GET'])
def login_form():
    """Registered users can log in."""

    return render_template("login_form.html")


@app.route('/login', methods=['POST'])
def login_process():
    """Registered users can log in."""

    email_form_input = request.form['email']
    password_form_input = request.form['password']

    db_query_by_email = User.query.filter(User.email == email_form_input)

    if db_query_by_email.first() == None:
        flash('You are not a current user. Please create a new account or enter your email again.')
        return redirect('/register')
    elif db_query_by_email.first().password != password_form_input:
        flash('Incorrect password. Please try again.')
        return redirect('/login')
    else:
        session['user_login'] = db_query_by_email.first().user_id
        flash('You are now logged in. You are user # %d' % (session['user_login']))
        return redirect('/profile')


@app.route('/logout', methods=['POST'])
def logout_process():
    """Registered users can log out."""

    del session['user_login']
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
