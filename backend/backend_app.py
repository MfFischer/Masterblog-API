from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# A list to store the blog posts
posts = []

# Function to generate a new unique ID
def generate_id():
    """
    Generate a unique ID for a new blog post.
    The ID is the increment of the last post's ID, or 1 if the list is empty.
    """
    if posts:
        return posts[-1]['id'] + 1
    else:
        return 1

@app.route('/')
def index():
    """
    Root URL route that returns a welcome message.
    This prevents 404 errors when accessing the root URL.
    """
    return "Welcome to the Blog API. Use /api/posts to interact with the posts."

@app.route('/api/posts', methods=['POST'])
def add_post():
    """
    API endpoint to add a new blog post.
    """
    data = request.get_json()
    if not data or 'title' not in data or 'content' not in data:
        # Identify missing fields and return a 400 Bad Request error
        missing_fields = []
        if 'title' not in data:
            missing_fields.append('title')
        if 'content' not in data:
            missing_fields.append('content')
        return jsonify({'error': f'Missing fields: {", ".join(missing_fields)}'}), 400

    # Create a new post
    new_post = {
        'id': generate_id(),
        'title': data['title'],
        'content': data['content']
    }
    # Add the new post to the list of posts
    posts.append(new_post)
    # Return the new post with a 201 Created status
    return jsonify(new_post), 201

@app.route('/api/posts', methods=['GET'])
def get_posts():
    """
    API endpoint to retrieve all blog posts.
    Returns a JSON list of all posts.
    """
    return jsonify(posts)

if __name__ == '__main__':
    # Run the Flask application on port 5002
    app.run(host="0.0.0.0", port=5002, debug=True)
