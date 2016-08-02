"""Utility file to seed ratings database from MovieLens data in seed_data/"""

from sqlalchemy import func
from model import User, Movie, Rating
import datetime

from model import connect_to_db, db
from server import app


def load_users():
    """Load users from u.user into database."""

    print "Users"

    # Delete all rows in table, so if we need to run this a second time,
    # we won't be trying to add duplicate users
    User.query.delete()

    # Read u.user file and insert data
    for row in open("seed_data/u.user"):
        row = row.rstrip()
        user_id, age, gender, occupation, zipcode = row.split("|")

        user = User(user_id=user_id,
                    age=age,
                    zipcode=zipcode)

        # We need to add to the session or it won't ever be stored
        db.session.add(user)

    # Once we're done, we should commit our work
    db.session.commit()


def load_movies():
    """Load movies from u.item into database."""

    print "Movies"

    # Delete all rows in table, so if we need to run this a second time,
    # we won't be trying to add duplicate users
    Movie.query.delete()

    # Read u.user file and insert data
    for row in open("seed_data/u.item"):
        row = row.rstrip()
        row = row.split("|")
        row = row[:5]
        movie_id, title, released_at, video_release_at, imdb_url = row

        title = title[:-7]
        # title = title.split(" (")
        # title = title[0]

        if released_at:
            released_at = datetime.datetime.strptime(released_at, "%d-%b-%Y")
        else:
            released_at = None

        movie = Movie(movie_id=movie_id,
                    title=title,
                    released_at=released_at,
                    imdb_url=imdb_url)

        # We need to add to the session or it won't ever be stored
        db.session.add(movie)

    # Once we're done, we should commit our work
    db.session.commit()


def load_ratings():
    """Load ratings from u.data into database."""

    print "Ratings"

    # Delete all rows in table, so if we need to run this a second time,
    # we won't be trying to add duplicate users
    Rating.query.delete()

    # Read u.user file and insert data
    for row in open("seed_data/u.data"):
        row = row.rstrip()
        user_id, movie_id, score, timestamp = row.split("\t")

        rating = Rating(user_id=user_id,
                    movie_id=movie_id,
                    score=score)

        # We need to add to the session or it won't ever be stored
        db.session.add(rating)

    # Once we're done, we should commit our work
    db.session.commit()


def set_val_user_id():
    """Set value for the next user_id after seeding database."""

    # Get the Max user_id in the database
    result = db.session.query(func.max(User.user_id)).one()
    max_id = int(result[0])

    # Set the value for the next user_id to be max_id + 1
    query = "SELECT setval('users_user_id_seq', :new_id)"
    db.session.execute(query, {'new_id': max_id + 1})
    db.session.commit()


def set_val_movie_id():
    """Set value for the next movie_id after seeding database."""

    # Get the Max movie_id in the database
    result = db.session.query(func.max(Movie.movie_id)).one()
    max_id = int(result[0])

    # Set the value for the next movie_id to be max_id + 1
    query = "SELECT setval('movies_movie_id_seq', :new_id)"
    db.session.execute(query, {'new_id': max_id + 1})
    db.session.commit()


def set_val_rating_id():
    """Set value for the next rating_id after seeding database."""

    # Get the Max rating_id in the database
    result = db.session.query(func.max(Rating.rating_id)).one()
    max_id = int(result[0])

    # Set the value for the next rating_id to be max_id + 1
    query = "SELECT setval('ratings_rating_id_seq', :new_id)"
    db.session.execute(query, {'new_id': max_id + 1})
    db.session.commit()


if __name__ == "__main__":
    connect_to_db(app)

    # In case tables haven't been created, create them
    db.create_all()

    # Import different types of data
    load_users()
    load_movies()
    load_ratings()
    set_val_user_id()
    set_val_movie_id()
    set_val_rating_id()