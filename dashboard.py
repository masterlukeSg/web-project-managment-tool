from flask import Flask
from flask import render_template

app = Flask(__name__)

@app.route("/dashboard")
def home():
    return render_template('test.html')


if __name__ == "__main__":
    app.run(debug=True)