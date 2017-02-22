"""Movie Ratings."""

import os

from jinja2 import StrictUndefined

from flask import (Flask, render_template, request, flash, redirect, session, jsonify, Response)

from model import connect_to_db, db
from model import (User, Movie, Rating)

import requests
import json
import csv
import pandas

import time


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


@app.route('/process', methods=['POST'])
def process():
    """Figures out whether this is a login or register route."""

    if request.form['submit'] == 'signin':

        # Get form variables.
        email = request.form['email']
        password = request.form['password']

        user = User.query.filter_by(email=email).first()

        if not user:
            flash("You are not a registered user, %s. Please register." % email)
            return redirect("/")

        if user.password != password:
            flash("Incorrect password. Please try again.")
            return redirect("/")

        session['user_id'] = user.user_id

        flash("Logged in.")
        return redirect("/users/%s" % user.user_id)

    elif request.form['submit'] == 'register':

        # Get form variables.
        email = request.form['email']
        password = request.form['password']

        user = User.query.filter_by(email=email).first()

        if user:
            flash("Email address already registered.")
            return redirect("/")

        new_user = User(email=email, password=password)

        db.session.add(new_user)
        db.session.commit()

        flash("User %s added. Please sign in." % email)
        return redirect("/")


@app.route('/logout', methods=['POST'])
def logout_process():
    """Process user logout."""

    del session['user_id']
    flash('You are now logged out.')
    return redirect("/")


@app.route('/users')
def user_list():
    """Show list of users."""

    users = User.query.all()
    num_users = len(users)
    return render_template("user_list.html", users=users, num_users=num_users)


@app.route('/users/<int:user_id>')
def user_profile(user_id):
    """Show user profile and information."""

    current_user = session.get('user_id')
    user = User.query.get(user_id)
    return render_template("user.html", user=user, current_user=current_user)


@app.route('/profile')
def current_profile():
    """Show your user profile and information."""

    user_id = session.get('user_id')
    return redirect("/users/%s" % user_id)


@app.route('/correlation', methods=['GET'])
def select_correlation():
    """Select users to show correlation."""

    return render_template("correlation.html")


#   def generate():
#         yield 'waiting 5 seconds\n'

#         for i in range(1, 101):
#             time.sleep(0.05)

#             if i % 10 == 0:
#                 yield '{}%\n'.format(i)

#         yield 'done\n'

#     return Response(generate(), mimetype='text/plain')

# @app.route('/correlationD3', methods=['POST'])
# def correlationD3():
#     """Show D3 correlogram of selected range of users."""

#     movie_limit = int(request.form['movielimit'])

#     all_users = User.query.all()
#     users = segment_users(all_users,movie_limit)

#     data = make_correlogram(users)
#     return render_template("correlation.html", users=users, data=data, correlation=None)


@app.route('/correlation', methods=['POST'])
def compare_ratings():
    """Show how your ratings compare to another user's."""

    # Get form variables.
    userid1 = request.form['userid1']
    userid2 = request.form['userid2']

    user1 = User.query.get(userid1)
    user2 = User.query.get(userid2)

    correlation = user1.similarity(user2)

    users = User.query.all()

    return render_template("correlation.html", users=users, user1=user1, user2=user2, correlation=correlation)


@app.route('/movies')
def movie_list():
    """Show list of movies."""

    movies = Movie.query.order_by('title').all()
    num_movies = len(movies)

    average_ratings = {}
    for movie in movies:
        # Get average rating of movie.
        rating_scores = [r.score for r in movie.ratings]
        avg_rating = float(sum(rating_scores)) / len(rating_scores)
        average_ratings[movie.movie_id] = round(avg_rating,2)

    return render_template("movie_list.html", movies=movies, num_movies=num_movies, average_ratings=average_ratings)


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
    average = float(sum(rating_scores)) / len(rating_scores)

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
    data = json.loads(response.data)

    return render_template("movie.html",
                           movie=movie,
                           user_rating=user_rating,
                           average=average,
                           prediction=prediction,
                           eye_rating=eye_rating,
                           difference=difference,
                           beratement=beratement,
                           data=data)


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


@app.route('/graph.json/<int:movie_limit>')
def make_graph(movie_limit):
    """Produces a graph data file with nodes and links."""

    all_users = User.query.all()
    users = segment_users(all_users,movie_limit)

    graph = {}
    nodes = []
    links = []
    graph['nodes'] = nodes
    graph['links'] = links

    for user in users:
        node = {}
        node['user'] = user.user_id
        # node['group'] = user.avg_rating
        nodes.append(node)
        print node
        for other in users:
            if other != user:
                link = {}
                link['source'] = user.user_id
                link['target'] = other.user_id
                link['weight'] = user.similarity(other)
                links.append(link)
                print link

    return jsonify(graph)


def segment_users(users,movie_limit=500):
    """Return a portion of all users based on how many movies user has rated."""

    segmented_users = []
    for user in users:
        if len(user.ratings) > movie_limit:
            segmented_users.append(user)
    return segmented_users


@app.route("/data")
def csv_data():
    csv_data = make_correlogram()
    return csv_data


# @app.route('/correlogram.csv', methods=['POST'])
def make_correlogram():
    """Produces a table of all users and their correlations to other users."""

    # movie_limit = request.form['movielimit']

    all_users = User.query.all()
    users = segment_users(all_users)

    matrix = []
    first_row = []
    first_row.append("")
    matrix.append(first_row)

    for user in users:
        # creates column labels by user_id
        first_row.append('User No. '+str(user.user_id))
        subsequent_row = []
        subsequent_row.append('User No. '+str(user.user_id))
        for other in users:
            correlation_value = float(user.similarity(other))
            subsequent_row.append(correlation_value)
        matrix.append(subsequent_row)

    df = pandas.DataFrame(matrix)
    return df.to_csv()

    # # to interactively save a csv file
    # def generate_csv():
    #     for user in users:
    #         yield ','.join(user) + '\n'
    # return Response(generate_csv(), mimetype='text/csv')

    # write to csv file
    # with open("static/data/correlogram.csv", "wb") as f:
    #     writer = csv.writer(f)
    #     writer.writerows(matrix)


################################################################################

if __name__ == "__main__":

    # from flask_debugtoolbar import DebugToolbarExtension
    # DebugToolbarExtension(app)

    # import doctest
    # result = doctest.testmod()
    # if not result.failed:
    #     print "ALL TESTS PASSED. GOOD WORK!"

    connect_to_db(app, os.environ.get("DATABASE_URL"))
    db.create_all()

    DEBUG = "NO_DEBUG" not in os.environ
    PORT = int(os.environ.get("PORT", 5000))

    app.run(host="0.0.0.0", port=PORT, debug=DEBUG)
