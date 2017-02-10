"""Utility file to seed ratings database from MovieLens data in seed_data/"""

import datetime
from sqlalchemy import func

from model import connect_to_db, db
from model import (User, Movie, Rating)

import omdb
import json

from server import app

import os

# Whenever seeding,
# drop existing database and create a new database.
os.system("dropdb strangerratings")
print "dropdb ratings"
os.system("createdb strangerratings")
print "createdb ratings"


def load_users():
    """Load users from u.user into database."""

    print "Users"

    # Delete all rows in table, so if we need to run this a second time,
    # we won't be trying to add duplicate users.
    User.query.delete()

    # Read u.user file and insert data.
    for i, row in enumerate(open("seed_data/u.user")):
        row = row.rstrip()
        user_id, age, gender, occupation, zipcode = row.split("|")

        user = User(age=age,
                    zipcode=zipcode)

        # We need to add to the session or it won't ever be stored.
        db.session.add(user)

    # Once we're done, we should commit our work.
    db.session.commit()


def load_movies():
    """Load movies from u.item into database."""

    print "Movies"

    # Delete all rows in table, so if we need to run this a second time,
    # we won't be trying to add duplicate users.
    Movie.query.delete()

    # Read u.user file and insert data
    for i, row in enumerate(open("seed_data/u.item")):
        row = row.rstrip()
        # Only unpack part of the row!
        movie_id, title, released_at, video_release_at, imdb_url = row.split("|")[:5]

        title = title[:-7]

        # if title == '':
        #     continue
        # elif Movie.query.filter_by(title=title).count() == 1:
        #     continue

        if released_at:
            release_date = datetime.datetime.strptime(released_at, "%d-%b-%Y")
        else:
            release_date = None

        # to be calculated later...
        avg_rating = None

        # # call to OMDB API
        # r = omdb.get_movie_info(title,release_date)
        # if r.status_code != 200:
        #     continue

        # # Content of Response object as dict.
        # data = r.json()
        data = {}

        imdb_rating = data.get('imdbRating') or None
        tomatoes = data.get('tomatoRating') or None
        poster_url = data.get('Poster') or None
        year = data.get('Year') or None
        plot = data.get('Plot') or None
        genre = data.get('Genre') or None
        awards = data.get('Awards') or None
        actors = data.get('Actors') or None
        director = data.get('Director') or None
        writer = data.get('Writer') or None
        language = data.get('Language') or None
        country = data.get('Country') or None
        runtime = data.get('Runtime') or None

        movie = Movie(title=title,
                      release_date=release_date,
                      avg_rating=avg_rating,
                      imdb_url=imdb_url,
                      imdb_rating=imdb_rating,
                      tomatoes=tomatoes,
                      poster_url=poster_url,
                      year=year,
                      plot=plot,
                      genre=genre,
                      awards=awards,
                      actors=actors,
                      director=director,
                      writer=writer,
                      language=language,
                      country=country,
                      runtime=runtime)

        # We need to add to the session or it won't ever be stored
        db.session.add(movie)

        # After each movie is added, flush the session to be able to
        # perform Movie.query.filter_by() above.
        db.session.flush()

        # Provide a progress tracker as each row in data is being seeded.
        if i % 1000 == 0:
            print i

            # An optimization: if we commit after every add, the database
            # will do a lot of work committing each record. However, if we
            # wait until the end, on computers with smaller amounts of
            # memory, it might thrash around. By committing every 1,000th
            # add, we'll strike a good balance.
            db.session.commit()

    # Once we're done, we should commit our work
    db.session.commit()


def load_ratings():
    """Load ratings from u.data into database."""

    print "Ratings"

    # Delete all rows in table, so if we need to run this a second time,
    # we won't be trying to add duplicate users
    Rating.query.delete()

    # Read u.user file and insert data
    for i, row in enumerate(open("seed_data/u.data")):
        row = row.rstrip()
        user_id, movie_id, score, timestamp = row.split("\t")

        user_id = int(user_id)
        movie_id = int(movie_id)
        score = int(score)

        db_movies = Movie.query.all()
        if movie_id > max(db_movies):
            print "Movie not found."
            continue

        rating = Rating(user_id=user_id,
                        movie_id=movie_id,
                        score=score)

        # We need to add to the session or it won't ever be stored
        db.session.add(rating)

        # Provide a progress tracker as each row in data is being seeded.
        if i % 1000 == 0:
            print i
            db.session.commit()

    # Once we're done, we should commit all our work.
    db.session.commit()


def set_val_user_id():
    """Set value for the next user_id after seeding database."""

    # Get the Max user_id in the database.
    result = db.session.query(func.max(User.user_id)).one()
    max_id = int(result[0])

    # Set the value for the next user_id to be max_id + 1
    query = "SELECT setval('users_user_id_seq', :new_id)"
    db.session.execute(query, {'new_id': max_id})
    db.session.commit()


if __name__ == "__main__":
    connect_to_db(app)

    # In case tables haven't been created, create them.
    db.drop_all()
    db.create_all()

    # Import data tables and set val user_id as next possible number.
    load_users()
    load_movies()
    load_ratings()
    set_val_user_id()

    # Mimic what we did in the interpreter, and add the Eye and some ratings.
    eye = User(email="the-eye@judge.com", password="judge")
    db.session.add(eye)
    db.session.commit()

    # Toy Story
    r = Rating(user_id=eye.user_id, movie_id=1, score=1)
    db.session.add(r)

    # Robocop 3
    r = Rating(user_id=eye.user_id, movie_id=1274, score=5)
    db.session.add(r)

    # Judge Dredd
    r = Rating(user_id=eye.user_id, movie_id=373, score=5)
    db.session.add(r)

    # 3 Ninjas
    r = Rating(user_id=eye.user_id, movie_id=314, score=5)
    db.session.add(r)

    # Aladdin
    r = Rating(user_id=eye.user_id, movie_id=95, score=1)
    db.session.add(r)

    # The Lion King
    r = Rating(user_id=eye.user_id, movie_id=71, score=1)
    db.session.add(r)

    db.session.commit()

    # Add a sample user.
    sample = User(email="sample@gmail.com",
                  password="sample",
                  age=0,
                  zipcode="000000")
    db.session.add(sample)
    db.session.commit()

    # Toy Story
    r = Rating(user_id=sample.user_id, movie_id=1, score=5)
    db.session.add(r)

    # Robocop 3
    r = Rating(user_id=sample.user_id, movie_id=1274, score=1)
    db.session.add(r)

    # Judge Dredd
    r = Rating(user_id=sample.user_id, movie_id=373, score=1)
    db.session.add(r)

    # 3 Ninjas
    r = Rating(user_id=sample.user_id, movie_id=314, score=1)
    db.session.add(r)

    # Aladdin
    r = Rating(user_id=sample.user_id, movie_id=95, score=5)
    db.session.add(r)

    # The Lion King
    r = Rating(user_id=sample.user_id, movie_id=71, score=5)
    db.session.add(r)

    db.session.commit()
