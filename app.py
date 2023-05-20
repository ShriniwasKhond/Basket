from flask import Flask, render_template
from analysis import plot1


app=Flask(__name__)

@app.route("/")
def visual1():
     graph1=plot1()
     return render_template('index.html', graph_1=graph1)

if __name__ == '__main__':
    app.run(debug=True)