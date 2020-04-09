import os
import untangle
from flask import Flask, session, render_template, request, url_for, flash, jsonify
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from werkzeug.utils import redirect
from lxml import html

app = Flask(__name__)

# check for good key
if not os.getenv("API_KEY"):
    raise RuntimeError("API_KEY is not set")
# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))
KEY = os.getenv("API_KEY")


@app.route("/")
def default():
    if session.get('username'):
        return redirect(url_for("search"))
    else:
        return redirect(url_for("login"))


@app.route("/logout")
def logout():
    session['logged_in'] = False
    return redirect(url_for("login"))


@app.route("/bookpage/<id>", methods=["GET", "POST"])
def display_book(id):
    def setbook(book):
        book_info = {}
        book_info['title'] = book.title.cdata
        if len(book.authors.children) == 1:
            book_info['author'] = book.authors.author.name.cdata
        else:
            book_info['author'] = book.authors.author[0].name.cdata
        book_info['publication_year'] = book.publication_year.cdata
        book_info['ISBN'] = book.isbn.cdata
        book_info['IMG'] = book.image_url.cdata
        summery = str(html.fromstring(book.description.cdata).text_content())
        book_info['summery_preview'] = summery  # [0:300]
        book_info['summery_all'] = summery[300:len(summery)]
        book_info['avg_rating'] = float(book.average_rating.cdata) / 5 * 100
        book_info['ratings'] = book.work.rating_dist.cdata
        return book_info

    def getreviews(bookid):
        return db.execute(
            "SELECT users.username, reviews.review FROM reviews JOIN users on reviews.reviewer_id=users.id WHERE reviews.id = :bookid",
            {"bookid": bookid}).fetchall()

    url = "https://www.goodreads.com/book/show.xml?key=" + KEY + "&id=" + id
    result = untangle.parse(url)
    book_info = setbook(result.GoodreadsResponse.book)
    if request.method == "POST":
        if (request.form.get('search')):
            return redirect(url_for(".search_str", str=request.form.get('search_for')))
        if (request.form.get('submit')):
            review = request.form.get('review')
            db.execute("INSERT INTO reviews (isbn, id, reviewer_id,review) VALUES (:isbn, :id, :userID, :review)",
                       {"isbn": book_info['ISBN'], "id": id, "userID": session.get('userID'), "review": review})
            db.commit()
            return render_template("bookpage.html", book=book_info, reviews=getreviews(id))
    else:
        return render_template("bookpage.html", book=book_info, reviews=getreviews(id))


@app.route("/search/<str>", methods=["GET", "POST"])
def search_str(str):
    if request.method == "POST":
        return redirect(url_for(".search_str", str=request.form.get('search_for')))
    else:
        str = str.replace(" ", "%20")
        url = "https://www.goodreads.com/search/index.xml?key=" + KEY + "&q=" + str
        result = untangle.parse(url)
        inside = result.GoodreadsResponse.search.results
        return render_template("search.html", results=inside.children)

@app.route("/search", methods=["GET", "POST"])
def search():
    logged = session.get('logged_in')
    if logged == False or logged == "none":
        return redirect(url_for("login"))
    else:
        if request.method == "POST":
            return redirect(url_for(".search_str", str=request.form.get('search_for')))
        else:
            return render_template("search.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if session.get('logged_in'):
        return redirect(url_for("search"))
    elif request.method == "POST":
        fname = request.form['firstname']
        lname = request.form['lastname']
        uname = request.form['username']
        pword = request.form['password']
        db.execute(
            "INSERT INTO users (firstname, lastname, username, password) VALUES (:fname, :lname, :uname, :pword)",
            {"fname": fname, "lname": lname, "uname": uname, "pword": pword})
        db.commit()
        session['logged_in'] = True
        session['username'] = uname
        return redirect(url_for("search"))
    else:
        return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if session.get('logged_in'):
        return redirect(url_for("search"))
    if request.method == "POST":
        uname = request.form['username']
        pword = request.form['password']
        results = db.execute("SELECT * FROM users WHERE username = :uname AND password = :pword",
                             {"uname": uname, "pword": pword}).fetchall()
        if len(results) == 0:
            flash("login failed, please try again")
            return render_template("login.html")
        else:
            session['logged_in'] = True
            session['username'] = uname
            session['userID'] = results[0]['id']
            return redirect(url_for("search"))
    else:
        return render_template("login.html")


@app.route("/api/<isbn>", methods=['GET'])
def api(isbn):
    book = db.execute("SELECT isbn FROM books WHERE books.isbn = :isbn", {"isbn": isbn})
    if book.rowcount == 0:
        return jsonify({"error": "no such book ISBN in our database"})
    result = db.execute(
        "SELECT books.isbn, COUNT(reviews.review) as num_of_reviews FROM books JOIN reviews ON books.isbn = reviews.isbn WHERE books.isbn = :isbn GROUP BY books.isbn",
        {"isbn": isbn})
    if result.rowcount == 0:
        return jsonify({"message": "no reviews yet"})
    data = result.fetchone()
    api_data = dict(data.items())
    return jsonify(api_data)
