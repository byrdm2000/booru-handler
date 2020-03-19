from urllib import request
import requests
from time import sleep
import json
from config import Config

base_url = Config.BASE_URL
user_agent = "ePostGet/2.0 (by OnlyForBlacklist)"  # REQUIRED


def json_request(api_call):
    """
    Makes a json request with the specified API call and arguments
    """
    http_req = request.Request(base_url + api_call, data=None, headers={'User-Agent': user_agent})
    with request.urlopen(http_req) as response:
        json_req = response.read().decode("utf-8")
    return json.JSONDecoder().decode(json_req)


class Post(object):
    def __init__(self, id, tags=None, url=None, ext=None, md5=None, filename=None):
        """
        Parameters id, tags, url, ext, md5 can be supplied from the API request for the id
        filename is user-specified, WITHOUT EXTENSION
        """
        self.id = str(id)
        if tags is None:
            self.tags = set()
        else:
            self.tags = tags
        self.url = url
        self.ext = ext
        self.md5 = md5
        self.filename = filename

    def get_info(self):
        """
        Gets file info, such as url, ext, and md5, and post tags
        """
        file_info = json_request("/posts.json?tags=id:" + self.id).get('posts')[0]
        # Get request
        post_info = file_info.get('file')
        # Update attributes
        self.url = post_info.get('url')
        self.ext = post_info.get('ext')
        self.md5 = post_info.get('md5')
        # Process tags
        tag_info = file_info.get('tags')
        for prefix, tags in tag_info.items():
            for tag in tags:
                if prefix != "general":
                    self.tags.add(prefix + ":" + tag)
                else:
                    self.tags.add(tag)

    def save(self):
        """
        Saves file and tags
        """
        if not self.url:  # minimum needed for saving posts
            self.get_info()
            sleep(1)
        if not self.filename:
            filename = self.md5 + "." + self.ext
        else:
            filename = self.filename + "." + self.ext
        post_data = requests.get(self.url)
        open(filename, 'wb').write(post_data.content)  # not on git, needs updated... eventually
        with open(filename + ".txt", "w") as tag_file:
            for tag in self.tags:
                tag_file.write(tag + "\n")


def download_posts(ids, filename_map=None):
    """
    Downloads post in iterable ids, looking up filenames in optional filename_map
    """
    for id in ids:
        if not filename_map:
            Post(id).save()
        else:
            save_name = filename_map.get(id)
            if save_name is not None:
                Post(id, filename=save_name).save()
            else:
                Post(id).save()
