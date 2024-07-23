from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_swagger_ui import get_swaggerui_blueprint

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
    if not data or 'title' not in data or 'content' not in data or 'author' not in data or 'date' not in data:
        # Identify missing fields and return a 400 Bad Request error
        missing_fields = []
        if 'title' not in data:
            missing_fields.append('title')
        if 'content' not in data:
            missing_fields.append('content')
        if 'author' not in data:
            missing_fields.append('author')
        if 'date' not in data:
            missing_fields.append('date')
        return jsonify({'error': f'Missing fields: {", ".join(missing_fields)}'}), 400

    new_post = {
        'id': generate_id(),
        'title': data['title'],
        'content': data['content'],
        'author': data['author'],
        'date': data['date'],
        'categories': data.get('categories', []),
        'tags': data.get('tags', []),
        'comments': []
    }
    # Add the new post to the list of posts
    posts.append(new_post)
    # Return the new post with a 201 Created status
    return jsonify(new_post), 201

@app.route('/api/posts', methods=['GET'])
def get_posts():
    """
    API endpoint to retrieve all blog posts.
    """
    sort = request.args.get('sort')
    direction = request.args.get('direction', 'asc')
    page = int(request.args.get('page', 1))
    limit = int(request.args.get('limit', 10))

    valid_sort_fields = {'title', 'content'}
    valid_directions = {'asc', 'desc'}

    if sort and sort not in valid_sort_fields:
        return jsonify({'error': 'Invalid sort field. Valid fields are title or content.'}), 400

    if direction not in valid_directions:
        return jsonify({'error': 'Invalid sort direction. Valid directions are asc or desc.'}), 400

    sorted_posts = posts[:]

    if sort:
        reverse = (direction == 'desc')
        sorted_posts = sorted(posts, key=lambda x: x[sort].lower(), reverse=reverse)

    start = (page - 1) * limit
    end = start + limit
    paginated_posts = sorted_posts[start:end]

    return jsonify(paginated_posts)


@app.route('/api/posts/<int:id>', methods=['DELETE'])
def delete_post(id):
    """
    API endpoint to delete a blog post by its ID.
    """
    # Find the post with the given ID
    post_to_delete = next((post for post in posts if post['id'] == id), None)
    if post_to_delete is None:
        return jsonify({'error': 'Post not found'}), 404

    # Remove the post from the list of posts
    posts.remove(post_to_delete)
    return jsonify({'message': f'Post with id {id} has been deleted successfully.'}), 200


@app.route('/api/posts/<int:id>', methods=['PUT'])
def update_post(id):
    """
    API endpoint to update a blog post by its ID.
    """
    data = request.get_json()
    # Find the post with the given ID
    post_to_update = next((post for post in posts if post['id'] == id), None)
    if post_to_update is None:
        return jsonify({'error': 'Post not found'}), 404

    # Update the post's fields if provided
    if 'title' in data:
        post_to_update['title'] = data['title']
    if 'content' in data:
        post_to_update['content'] = data['content']
    if 'author' in data:
        post_to_update['author'] = data['author']
    if 'date' in data:
        post_to_update['date'] = data['date']
    if 'categories' in data:
        post_to_update['categories'] = data['categories']
    if 'tags' in data:
        post_to_update['tags'] = data['tags']

    return jsonify(post_to_update), 200


@app.route('/api/posts/search', methods=['GET'])
def search_posts():
    """
    API endpoint to search for blog posts by title or content.
    """
    title_query = request.args.get('title', '').lower()
    content_query = request.args.get('content', '').lower()

    # Only filter posts if at least one query parameter is provided
    if title_query or content_query:
        filtered_posts = [
            post for post in posts
            if (title_query in post['title'].lower() if title_query else True) and
               (content_query in post['content'].lower() if content_query else True)
        ]
    else:
        filtered_posts = []

    return jsonify(filtered_posts)


@app.route('/api/posts/<int:post_id>/comments', methods=['POST'])
def add_comment(post_id):
    """
    API endpoint to add a comment to a blog post by its ID.
    """
    data = request.get_json()
    if not data or 'author' not in data or 'text' not in data:
        return jsonify({'error': 'Missing fields: author, text'}), 400

    post = next((post for post in posts if post['id'] == post_id), None)
    if post is None:
        return jsonify({'error': 'Post not found'}), 404

    new_comment = {
        'author': data['author'],
        'text': data['text']
    }
    post['comments'].append(new_comment)
    return jsonify(post), 201


@app.route('/api/posts/<int:post_id>/comments', methods=['GET'])
def get_comments(post_id):
    """
    API endpoint to retrieve all comments for a blog post by its ID.
    """
    post = next((post for post in posts if post['id'] == post_id), None)
    if post is None:
        return jsonify({'error': 'Post not found'}), 404

    return jsonify(post['comments'])


# Swagger configuration
SWAGGER_URL = "/api/docs"
API_URL = "/static/masterblog.json"
swagger_ui_blueprint = get_swaggerui_blueprint(
    SWAGGER_URL,
    API_URL,
    config={'app_name': 'Masterblog API'}
)
app.register_blueprint(swagger_ui_blueprint, url_prefix=SWAGGER_URL)

if __name__ == '__main__':
    # Run the Flask application on port 5002
    app.run(host="0.0.0.0", port=5002, debug=True)
