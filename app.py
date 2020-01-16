from flask import Flask, request, render_template
from config import Config
import PostHandler
import PoolWatcher

app = Flask(__name__)

added_posts = []
added_pools = []
watchlist = PoolWatcher.Watcher()


@app.route('/')
@app.route('/index')
def index():
    return render_template('index.html', posts=added_posts, pools=added_pools)


@app.route('/add_post', methods=['POST'])
def add_post():
    post = request.form.get("add_post", None)
    if post is not None:
        try:
            post_id = int(post)
            if post_id not in added_posts:
                added_posts.append(post_id)
        except ValueError:
            return "Invalid data!"
    return index()


@app.route('/add_pool', methods=['POST'])
def add_pool():
    pool = request.form.get("add_pool", None)
    if pool is not None:
        try:
            pool_id = int(pool)
            if pool_id not in added_pools:
                added_pools.append(pool_id)
        except ValueError:
            return "Invalid data!"
    return index()


@app.route('/del_post', methods=['POST'])
def del_post():
    post = request.form.get("post_select", None)
    if post is not None:
        try:
            post_id = int(post)
            if post_id in added_posts:
                added_posts.remove(post_id)
        except ValueError:
            return "Invalid data!"
    return index()


@app.route('/del_pool', methods=['POST'])
def del_pool():
    pool = request.form.get("pool_select", None)
    if pool is not None:
        try:
            pool_id = int(pool)
            if pool_id in added_pools:
                added_pools.remove(pool_id)
        except ValueError:
            return "Invalid data!"
    return index()


@app.route('/upload', methods=["POST"])
def upload():
    password = request.form.get("password", None)
    if password == Config.PASSWORD:
        PostHandler.download_posts(added_posts)
        added_posts.clear()
        watchlist.add_pools(added_pools)
        watchlist.update()
        watchlist.save()
        added_pools.clear()
        return index()
    else:
        print("invalid password")
        return "Invalid password!"


if __name__ == '__main__':
    app.run()
