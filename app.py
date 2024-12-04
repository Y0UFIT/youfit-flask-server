from flask import Flask, jsonify, request

app = Flask(__name__)

@app.route('/')
def home():
    return jsonify({"message": "Welcome to Flask!"})

@app.route('/echo', methods=['POST'])
def echo():
    data = request.json
    return jsonify({"echo": data})

if __name__ == '__main__':
    app.run(debug=True)