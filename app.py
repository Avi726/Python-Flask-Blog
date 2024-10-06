from flask import Flask, render_template
app=Flask(__name__)

@app.route("/")
def start():
    name="Abhi"
    return render_template("index.html",name=name)

@app.route("/bootstrap")
def bootstrap():
    return render_template("bootstrap.html")

app.run(debug=True)