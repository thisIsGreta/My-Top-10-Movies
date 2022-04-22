from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
import requests

app = Flask(__name__)
app.config['SECRET_KEY'] = 'xxxxxxxxxxYYYYYYYYYYYzZzZ'
Bootstrap(app)

TMDB_SEARCH = "https://api.themoviedb.org/3/search/movie"
api_key = "see-website"

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///movie-collections.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


class Movie(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(80), unique=True, nullable=False)
    year = db.Column(db.Integer, unique=False, nullable=False)
    description = db.Column(db.String(1000), unique=False, nullable=False)
    rating = db.Column(db.Float, unique=False)
    ranking = db.Column(db.Integer, unique=False)
    review = db.Column(db.String(1000), unique=False, nullable=True)
    img_url = db.Column(db.String(1000), unique=True, nullable=False)

    def __repr__(self):
        return '<User %r>' % self.title

db.create_all()


class RateMovieForm(FlaskForm):
    your_rating = StringField('Your Rating Out of 10 e.g. 7.5', validators=[DataRequired()])
    your_review = StringField("Your Review:", validators=[DataRequired()])
    done = SubmitField("Done")


class AddMovieForm(FlaskForm):
    title = StringField("Movie Title", validators=[DataRequired()])
    submit = SubmitField("Add Movie")


@app.route("/")
def home():
    movies = Movie.query.order_by(Movie.rating).all()
    movies = movies[::-1]
    # print(movies)
    for movie in movies:
        movie.ranking = movies.index(movie) + 1
        db.session.commit()
        # print(movie.rating)
    return render_template("index.html", movies=movies)


@app.route("/delete")
def delete_movie():
    movie_id = request.args.get("id")
    movie = Movie.query.get(movie_id)
    db.session.delete(movie)
    db.session.commit()
    return redirect(url_for("home"))


@app.route('/add', methods=["GET", "POST"])
def add():
    new_form = AddMovieForm(request.form)
    if request.method == "POST" and new_form.validate():
        params = {
            'api_key': api_key,
            'query': request.form['title'],
        }
        response = requests.get(url=TMDB_SEARCH, params=params)
        data_list = response.json()['results']
        return render_template('select.html', movies=data_list)
    return render_template('add.html', form=new_form)


@app.route('/select')
def add_movie():
    movie_id = request.args.get('id')
    TMDB_GET = f"https://api.themoviedb.org/3/movie/{movie_id}"
    params_too = {
        'api_key': api_key,
    }
    response = requests.get(TMDB_GET, params=params_too)
    specific_movie = response.json()
    # print(specific_movie)
    url = f"https://image.tmdb.org/t/p/w500{specific_movie['backdrop_path']}"
    new_movie = Movie(title=specific_movie['original_title'],
                      year=specific_movie['release_date'].split("-")[0],
                      img_url=url,
                      description=specific_movie['overview'],
                      rating=10,
                      review=specific_movie['original_title'],
                      ranking=1,
                      )
    db.session.add(new_movie)
    db.session.commit()
    return redirect(url_for('edit', id=new_movie.id))


@app.route('/edit', methods=["POST", "GET"])
def edit():
    form = RateMovieForm(request.form)
    id = request.args.get("id")
    if request.method == "POST" and form.validate():
        movie_to_update = Movie.query.get(id)
        movie_to_update.rating = form.your_rating.data
        movie_to_update.review = form.your_review.data
        db.session.commit()
        return redirect(url_for('home'))
    return render_template("edit.html", form=form)


if __name__ == '__main__':
    app.run(debug=True)
