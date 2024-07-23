from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_swagger_ui import get_swaggerui_blueprint
from datetime import datetime
import json
import os

app = Flask(__name__)
CORS(app)


def read_posts():
    """
    Read posts from the JSON file.
    """
    if not os.path.exists('posts.json'):
        return []
    with open('posts.json', 'r') as file:
        try:
            return json.load(file)
        except json.JSONDecodeError:
            return []


def write_posts(posts):
    """
    Write posts to the JSON file.
    """
    with open('posts.json', 'w') as file:
        json.dump(posts, file, indent=4)


def generate_id():
    """
    Generate a unique ID for a new blog post.
    The ID is the increment of the last post's ID, or 1 if the list is empty.
    """
    posts = read_posts()
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
        missing_fields = [field for field in ['title', 'content', 'author', 'date'] if field not in data]
        return jsonify({'error': f'Missing fields: {", ".join(missing_fields)}'}), 400

    try:
        datetime.strptime(data['date'], '%Y-%m-%d')
    except ValueError:
        return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD.'}), 400

    posts = read_posts()
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
    posts.append(new_post)
    write_posts(posts)
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

    valid_sort_fields = {'title', 'content', 'author', 'date'}
    valid_directions = {'asc', 'desc'}

    if sort and sort not in valid_sort_fields:
        return jsonify({'error': 'Invalid sort field. Valid fields are title, content, author, date.'}), 400

    if direction not in valid_directions:
        return jsonify({'error': 'Invalid sort direction. Valid directions are asc or desc.'}), 400

    posts = read_posts()

    if sort:
        reverse = (direction == 'desc')
        if sort == 'date':
            posts = sorted(posts, key=lambda x: datetime.strptime(x['date'], '%Y-%m-%d'), reverse=reverse)
        else:
            posts = sorted(posts, key=lambda x: x[sort].lower(), reverse=reverse)

    start = (page - 1) * limit
    end = start + limit
    paginated_posts = posts[start:end]

    return jsonify(paginated_posts)


@app.route('/api/posts/<int:id>', methods=['DELETE'])
def delete_post(id):
    """
    API endpoint to delete a blog post by its ID.
    """
    posts = read_posts()
    post_to_delete = next((post for post in posts if post['id'] == id), None)
    if post_to_delete is None:
        return jsonify({'error': 'Post not found'}), 404

    posts.remove(post_to_delete)
    write_posts(posts)
    return jsonify({'message': f'Post with id {id} has been deleted successfully.'}), 200


@app.route('/api/posts/<int:id>', methods=['PUT'])
def update_post(id):
    """
    API endpoint to update a blog post by its ID.
    """
    data = request.get_json()
    posts = read_posts()
    post_to_update = next((post for post in posts if post['id'] == id), None)
    if post_to_update is None:
        return jsonify({'error': 'Post not found'}), 404

    if 'title' in data:
        post_to_update['title'] = data['title']
    if 'content' in data:
        post_to_update['content'] = data['content']
    if 'author' in data:
        post_to_update['author'] = data['author']
    if 'date' in data:
        try:
            datetime.strptime(data['date'], '%Y-%m-%d')
            post_to_update['date'] = data['date']
        except ValueError:
            return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD.'}), 400
    if 'categories' in data:
        post_to_update['categories'] = data['categories']
    if 'tags' in data:
        post_to_update['tags'] = data['tags']

    write_posts(posts)
    return jsonify(post_to_update), 200


@app.route('/api/posts/search', methods=['GET'])
def search_posts():
    """
    API endpoint to search for blog posts by title, content, author, or date.
    """
    title_query = request.args.get('title', '').lower()
    content_query = request.args.get('content', '').lower()
    author_query = request.args.get('author', '').lower()
    date_query = request.args.get('date', '')

    posts = read_posts()
    filtered_posts = [
        post for post in posts
        if (title_query in post['title'].lower() if title_query else True) and
           (content_query in post['content'].lower() if content_query else True) and
           (author_query in post['author'].lower() if author_query else True) and
           (date_query == post['date'] if date_query else True)
    ]

    return jsonify(filtered_posts)


@app.route('/api/posts/<int:post_id>/comments', methods=['POST'])
def add_comment(post_id):
    """
    API endpoint to add a comment to a blog post by its ID.
    """
    data = request.get_json()
    if not data or 'author' not in data or 'text' not in data:
        return jsonify({'error': 'Missing fields: author, text'}), 400

    posts = read_posts()
    post = next((post for post in posts if post['id'] == post_id), None)
    if post is None:
        return jsonify({'error': 'Post not found'}), 404

    new_comment = {
        'author': data['author'],
        'text': data['text']
    }
    post['comments'].append(new_comment)
    write_posts(posts)
    return jsonify(post), 201


@app.route('/api/posts/<int:post_id>/comments', methods=['GET'])
def get_comments(post_id):
    """
    API endpoint to retrieve all comments for a blog post by its ID.
    """
    posts = read_posts()
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
