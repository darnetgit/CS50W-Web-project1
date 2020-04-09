import csv
import os

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))


def main():


# books table
# db.execute("DROP TABLE IF EXISTS books")
# db.commit()
# db.execute("CREATE TABLE books (isbn VARCHAR NOT NULL,title VARCHAR NOT NULL,author VARCHAR NOT NULL,year INTEGER NOT NULL,PRIMARY KEY(isbn));")
# db.commit()
# f = open("books.csv")
# reader = csv.reader(f)
# for isbn,title,author,year in reader:
#     if isbn!="isbn":
#         db.execute("INSERT INTO books (isbn,title,author,year) VALUES (:isbn,:title,:author,:year)",
#                 {"isbn": isbn, "title": title, "author": author, "year": int(year)})
# db.commit()

# users table
# db.execute("DROP TABLE IF EXISTS users")
# db.commit()
# db.execute("CREATE TABLE users (id SERIAL, firstname VARCHAR NOT NULL,lastname VARCHAR NOT NULL,username VARCHAR NOT NULL,password VARCHAR NOT NULL,PRIMARY KEY(id));")
# db.commit()

# reviews table
#     db.execute("DROP TABLE IF EXISTS reviews")
#     db.commit()
#     db.execute("CREATE TABLE reviews (isbn VARCHAR NOT NULL, id VARCHAR NOT NULL, reviewer_id INTEGER REFERENCES users, review VARCHAR NOT NULL);")
#     db.commit()

if __name__ == "__main__":
    main()
