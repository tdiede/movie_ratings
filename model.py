"""Models and database functions for Ratings project."""

from correlation import pearson

from flask_sqlalchemy import SQLAlchemy

# This is the connection to the PostgreSQL database; we're getting this through
# the Flask-SQLAlchemy helper library. On this, we can find the `session`
# object, where we do most of our interactions (like committing).

db = SQLAlchemy()


##############################################################################
# Model definitions

class User(db.Model):
    """User of ratings website."""

    __tablename__ = "users"

    user_id = db.Column(db.Integer,
                        autoincrement=True,
                        primary_key=True)

    email = db.Column(db.String(64), nullable=True, unique=True)
    password = db.Column(db.String(64), nullable=True)
    age = db.Column(db.Integer, nullable=True)
    zipcode = db.Column(db.String(15), nullable=True)

    def __repr__(self):
        """Provides helpful representation when printed."""

        return "<User user_id=%s email=%s>" % (self.user_id, self.email)

    def predict_rating(self, movie):
        """Predict user's rating of a movie."""

        other_ratings = movie.ratings

        similarities = [
            (self.similarity(r.user), r)
            for r in other_ratings
        ]

        similarities.sort(reverse=True)

        similarities = [(sim, r) for sim, r in similarities
                        if sim > 0]

        if not similarities:
            return None

        numerator = sum([r.score * sim for sim, r in similarities])
        denominator = sum([sim for sim, r in similarities])

        return numerator/denominator

    def similarity(self, other):
        """Return Pearson rating for user compared to other user."""

        u_ratings = {}
        paired_ratings = []

        for r in self.ratings:
            u_ratings[r.movie_id] = r

        for r in other.ratings:
            u_r = u_ratings.get(r.movie_id)
            if u_r:
                paired_ratings.append((u_r.score, r.score))

        if paired_ratings:
            return pearson(paired_ratings)

        else:
            return 0.0


class Movie(db.Model):
    """Movie to be rated."""

    __tablename__ = "movies"

    movie_id = db.Column(db.Integer,
                         autoincrement=True,
                         primary_key=True)

    title = db.Column(db.String(128))
    release_date = db.Column(db.DateTime)
    avg_rating = db.Column(db.String(4))
    imdb_url = db.Column(db.String(256))
    imdb_rating = db.Column(db.String(4))
    tomatoes = db.Column(db.String(4))
    poster_url = db.Column(db.String(256))
    year = db.Column(db.Integer)
    plot = db.Column(db.String(1000))
    genre = db.Column(db.String(64))
    awards = db.Column(db.String(256))
    actors = db.Column(db.String(256))
    director = db.Column(db.String(256))
    writer = db.Column(db.String(256))
    language = db.Column(db.String(64))
    country = db.Column(db.String(64))
    runtime = db.Column(db.String(64))

    sequel_of_id = db.Column(db.Integer, db.ForeignKey('movies.movie_id'))

    sequel_of = db.relationship("Movie")

    def __repr__(self):
        """Provide helpful representation when printed."""

        return "<Movie movie_id=%s title=%s>" % (self.movie_id, self.title)


class Rating(db.Model):
    """Rating of a movie given by user."""

    __tablename__ = "ratings"

    rating_id = db.Column(db.Integer,
                          autoincrement=True,
                          primary_key=True)

    movie_id = db.Column(db.Integer,
                         db.ForeignKey('movies.movie_id'))
    user_id = db.Column(db.Integer,
                        db.ForeignKey('users.user_id'))
    score = db.Column(db.Integer)

    # Define relationship to user.
    user = db.relationship("User",
                           backref=db.backref("ratings",
                                              order_by=rating_id))

    # Define relationship to movie.
    movie = db.relationship("Movie",
                            backref=db.backref("ratings",
                                               order_by=rating_id))

    def __repr__(self):
        """Provide helpful representation when printed."""

        s = "<Rating rating_id=%s movie_id=%s user_id=%s score=%s>"
        return s % (self.rating_id, self.movie_id, self.user_id, self.score)


##############################################################################
# Helper functions

def connect_to_db(app, db_uri=None):
    """Connect the database to our Flask app."""

    # Configure to use our PstgreSQL database
    app.config['SQLALCHEMY_DATABASE_URI'] = db_uri or 'postgresql:///ratings'
    # app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.app = app
    db.init_app(app)


if __name__ == "__main__":
    # As a convenience, if we run this module interactively, it will leave
    # you in a state of being able to work with the database directly.

    from server import app
    connect_to_db(app)
    print "Connected to DB."
