# Yatube
### Description
Community for publications. Blog with the possibility of publishing posts, subscribing to groups and authors, as well as commenting on posts.

### Technologies
- Python 3.7
- Django 2.2.19
- Pillow 8.3.1

### How to run the project:
Clone repository and go to it's derictory on your computer:
```
git clone https://github.com/IliartKersam/hw05_final.git
```
```
cd hw05_final
```

Create and activate virtual environment:

```
python -m venv venv
```
```
source venv/bin/activate
```
```
python -m pip install --upgrade pip
```

Install the requirements from requirements.txt:
```
pip install -r requirements.txt
```

Migrate:
```
python manage.py migrate
```

Run the project:
```
python manage.py runserver
```
### What users can do:
#### Logged in users can:

- View, publish, delete and edit your publications;
- View information about communities;
- View and publish comments on your behalf to the publications of other users (including yourself), delete and edit your comments;
- Subscribe to other users and view your subscriptions.
**Note**: Access to all write, update and delete operations is available only after authentication and obtaining a token.

### Anonymous users can:

- View publications;
- View information about communities;
- View comments;
### Available endpoints:
`posts/` - Display posts and publications (GET, POST);

`posts/{id}` - Getting, changing, deleting a post with the corresponding id (GET, PUT, PATCH, DELETE);

`posts/{post_id}/comments/` - Get comments on a post with the corresponding post_id and publish new comments (GET, POST);

`posts/{post_id}/comments/{id}` - Getting, editing, deleting a comment with the corresponding id to a post with the corresponding post_id (GET, PUT, PATCH, DELETE);

`posts/groups/` - Getting a description of registered communities (GET);

`posts/groups/{id}/` - Getting a community description with the corresponding id (GET);

`posts/follow/` - Getting information about the current user's subscriptions, creating a new subscription for the user (GET, POST).

### Author
Kashtanov Nikolay
Kazan, 2022
