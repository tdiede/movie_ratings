"""Movie Ratings."""

from jinja2 import StrictUndefined

from flask import (Flask, render_template, request, flash, redirect, session, jsonify)
from flask_debugtoolbar import DebugToolbarExtension

from model import connect_to_db, db
from model import (User, Movie, Rating)

import requests
import json


app = Flask(__name__)

# Required to use Flask sessions and the debug toolbar
app.secret_key = "ABC"

# Normally, if you use an undefined variable in Jinja2, it fails silently.
# This is horrible. Fix this so that, instead, it raises an error.
app.jinja_env.undefined = StrictUndefined


@app.route('/')
def index():
    """Homepage."""

    return render_template("homepage.html")


@app.route('/register', methods=['GET'])
def register_form():
    """New users can create an account through this form."""

    return render_template("register_form.html")


@app.route('/register', methods=['POST'])
def register_process():
    """Process new user account registration."""

    # Get form variables.
    email = request.form['email']
    password = request.form['password']
    age = int(request.form['age'])
    zipcode = request.form['zipcode']

    new_user = User(email=email, password=password, age=age, zipcode=zipcode)

    db.session.add(new_user)
    db.session.commit()

    flash("User %s added." % email)
    return redirect("/")


@app.route('/login', methods=['GET'])
def login_form():
    """Registered users can log in through this form."""

    return render_template("login_form.html")


@app.route('/login', methods=['POST'])
def login_process():
    """Process user login."""

    # Get form variables.
    email = request.form['email']
    password = request.form['password']

    user = User.query.filter_by(email=email).first()

    if not user:
        flash("You are not a registered user, %s. Please register." % email)
        return redirect("/register")

    if user.password != password:
        flash("Incorrect password. Please try again.")
        return redirect("/login")

    session['user_id'] = user.user_id

    flash("Logged in.")
    return redirect("/users/%s" % user.user_id)


@app.route('/logout', methods=['POST'])
def logout_process():
    """Process user logout."""

    del session['user_login']
    flash('You are now logged out.')
    return redirect("/")


@app.route('/users')
def user_list():
    """Show list of users."""

    users = User.query.all()

    return render_template("user_list.html", users=users)


@app.route('/users/<int:user_id>')
def user_profile(user_id):
    """Show user profile and information."""

    user = User.query.get(user_id)
    return render_template("user.html", user=user)


@app.route('/movies')
def movie_list():
    """Show list of movies."""

    movies = Movie.query.order_by('title').all()
    return render_template("movie_list.html", movies=movies)


@app.route('/movies/<int:movie_id>', methods=['GET'])
def movie_detail(movie_id):

    movie = Movie.query.get(movie_id)

    user_id = session.get('user_id')

    if user_id:
        user_rating = Rating.query.filter_by(movie_id=movie_id, user_id=user_id).first()

    else:
        user_rating = None

    # Get average rating of movie.
    rating_scores = [r.score for r in movie.ratings]
    avg_rating = float(sum(rating_scores)) / len(rating_scores)

    prediction = None

    # Prediction code: Only predict if the user hasn't rated the movie.
    if (user_id) and (not user_rating):  # if user_id found in session
        user = User.query.get(user_id)
        if user:  # if user found in database
            prediction = user.predict_rating(movie)

    # Either use the prediction or user rating.
    if prediction:
        # User has not rated the movie; show the prediction, if generated.
        effective_rating = prediction

    elif user_rating:
        # User has already rated the movie.
        effective_rating = user_rating.score

    else:
        # User has not rated the movie, and prediction has not been generated.
        effective_rating = None

    # Get the rating: Either predict or show user rating.
    the_eye = User.query.filter_by(email='the-eye@judge.com').one()
    eye_rating = Rating.query.filter_by(user_id=the_eye.user_id, movie_id=movie.movie_id).first()

    if not eye_rating:
        eye_rating = the_eye.predict_rating(movie)

    else:
        eye_rating = eye_rating.score

    if eye_rating and effective_rating:
        difference = abs(eye_rating - effective_rating)

    else:
        # An eye rating could not be generated, so pass on difference.
        difference = None

    # MESSAGES DEPENDING ON LEVEL OF DIFFERENCE
    BERATEMENT_MESSAGES = [
        "Good taste!",
        "Mediocre taste.",
        "Your taste has failed you.",
        "Why should I listen to your opinion??",
        "Words cannot express..."
    ]

    if difference:
        beratement = BERATEMENT_MESSAGES[int(difference)]

    else:
        beratement = None

    # visual display (call to OMDB API)
    response = get_movie_info(movie_id)
    visuals = json.loads(response.data)

    return render_template("movie.html",
                           movie=movie,
                           user_rating=user_rating,
                           average=avg_rating,
                           prediction=prediction,
                           eye_rating=eye_rating,
                           difference=difference,
                           beratement=beratement,
                           visuals=visuals)


@app.route('/movies/<int:movie_id>', methods=['POST'])
def rate_movie(movie_id):
    """Add (or edit) a movie rating."""

    # Get form variables.
    score = int(request.form['score'])

    user_id = session.get('user_id')
    if not user_id:
        raise Exception("No user logged in.")

    rating = Rating.query.filter_by(user_id=user_id, movie_id=movie_id).first()

    if rating:
        rating.score = score
        flash("Rating updated.")

    else:
        rating = Rating(user_id=user_id, movie_id=movie_id, score=score)
        flash("Rating added.")
        db.session.add(rating)

    db.session.commit()

    return redirect("/movies/%s" % movie_id)


# HELPER FUNCTION # JSON ROUTE #
@app.route('/movie_info.json/<int:movie_id>')
def get_movie_info(movie_id):
    """Uses the API (KEY=http://img.omdbapi.com/?i=tt2294629&apikey=7c9afab3) to fetch movie data."""

    movie = Movie.query.filter_by(movie_id=movie_id).first()

    data = {}
    data['t'] = movie.title
    data['y'] = str(movie.release_date.year)
    data['plot'] = 'short'
    data['r'] = 'json'

    payload = 't='+data['t']+'&y='+data['y']+'&plot=full&r=json'
    url = 'http://www.omdbapi.com/?'

    # Response object.
    r = requests.get(url+payload)

    # Content of Response object as dict.
    movie_info = r.json()

    # Send as json/dict.
    return jsonify(movie_info)


################################################################################

if __name__ == "__main__":
    # We have to set debug=True here, since it has to be True at the
    # point that we invoke the DebugToolbarExtension
    app.debug = True

    app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False

    connect_to_db(app)

    # Use the DebugToolbar
    DebugToolbarExtension(app)

    app.run(host='0.0.0.0')
