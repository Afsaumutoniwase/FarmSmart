from flask import render_template, Flask


app = Flask(__name__)
app.config['SECRET_KEY'] = 'farm smart'

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/hydroponic')
def hydroponic():
    return render_template('hydroponic.html')

@app.route('/login')
def login():
    return render_template('login.html')
if __name__ == '__main__':
    app.run(debug=True)
