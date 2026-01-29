from flask import Flask

app = Flask(__name__)

@app.route("/")
def hello():
    return "Hello World"

@app.route("/api/users", methods=["GET", "POST"])
def users():
    return "Users"

if __name__ == "__main__":
    app.run()
