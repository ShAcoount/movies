from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap5
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String, Float
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
import requests

app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
Bootstrap5(app)


# CREATE DB
class Base(DeclarativeBase):
    pass


app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///top-movies.db'
db = SQLAlchemy(model_class=Base)
db.init_app(app)


class Movie(db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(250), nullable=False)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    description: Mapped[str] = mapped_column(String(500), nullable=False)
    rating: Mapped[float] = mapped_column(Float, nullable=True)
    ranking: Mapped[int] = mapped_column(Integer, nullable=True)
    review: Mapped[str] = mapped_column(String(500), nullable=True)
    img_url: Mapped[str] = mapped_column(String(250), nullable=False)


# CREATE TABLE
with app.app_context():
    db.create_all()


class AddMovie(FlaskForm):
    movie_name = StringField("Movie Title", validators=[DataRequired()])
    button = SubmitField("Add Movie")


class EditForm(FlaskForm):
    rating = StringField("Your Rating Out of 10 e.g. 7.5")
    review = StringField("Your Review")
    button = SubmitField("Done")


@app.route("/")
def home():
    result = db.session.execute(db.select(Movie).order_by(Movie.ranking))
    all_movies = result.scalars().all()
    for i in range(len(all_movies)):
        all_movies[i].ranking = len(all_movies) - i
    db.session.commit()
    return render_template("index.html", movies=all_movies)


@app.route("/add", methods=["GET", "POST"])
def add():
    form = AddMovie()
    url = ("https://api.themoviedb.org/3/search/movie?"
           f"query={form.movie_name.data}&"
           "include_adult=true&"
           "language=en-US&"
           "page=1")

    headers = {
        "accept": "application/json",
        "Authorization": "Bearer eyJhbGciOiJIUzI1NiJ9.eyJhdWQiOiJiMWQxOGEyOGZiYjY3OWY4YTI4YjNkYTM1OTI5NzM5ZSIsInN1YiI6IjY2MWMwNjU3ZDdjZDA2MDE2M2EyYTg3OCIsInNjb3BlcyI6WyJhcGlfcmVhZCJdLCJ2ZXJzaW9uIjoxfQ.KK3JWAEMRZ0FJWA6TchYw5pkMdQYtP39LlT7499Wy4M"
    }

    if form.validate_on_submit():
        response = requests.get(url, headers=headers).json()["results"]
        return render_template("select.html", data=response)

    return render_template("add.html", form=form)


@app.route("/delete")
def delete():
    movie_id = request.args.get("id")
    movie_to_delete = db.get_or_404(Movie, movie_id)
    db.session.delete(movie_to_delete)
    db.session.commit()
    return redirect(url_for("home"))


@app.route("/edit", methods=["GET", "POST"])
def edit():
    form = EditForm()
    movie_id = request.args.get("id")
    movie = db.get_or_404(Movie, movie_id)
    if form.validate_on_submit():
        movie.rating = float(form.rating.data)
        movie.review = form.review.data
        db.session.commit()
        return redirect(url_for('home'))
    return render_template("edit.html", form=form, movie=movie)


@app.route("/find")
def find_movie():
    movie_id = request.args.get("id")
    headers = {
        "accept": "application/json",
        "Authorization": "Bearer eyJhbGciOiJIUzI1NiJ9.eyJhdWQiOiJiMWQxOGEyOGZiYjY3OWY4YTI4YjNkYTM1OTI5NzM5ZSIsInN1YiI6IjY2MWMwNjU3ZDdjZDA2MDE2M2EyYTg3OCIsInNjb3BlcyI6WyJhcGlfcmVhZCJdLCJ2ZXJzaW9uIjoxfQ.KK3JWAEMRZ0FJWA6TchYw5pkMdQYtP39LlT7499Wy4M"
    }
    if movie_id:
        response = requests.get(f"https://api.themoviedb.org/3/movie/{movie_id}?language=en-US", headers=headers).json()
        add_movie = Movie(
            title=response["title"],
            year=response["release_date"].split("-")[0],
            img_url=f"https://image.tmdb.org/t/p/w500{response['poster_path']}",
            description=response["overview"]
        )
        db.session.add(add_movie)
        db.session.commit()

        return redirect(url_for("edit", id=add_movie.id))


if __name__ == '__main__':
    app.run(debug=True)
