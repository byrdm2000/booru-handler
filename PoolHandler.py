from urllib import request
from time import sleep, strptime, time
from calendar import timegm
import xml.etree.ElementTree as ET
from config import Config
from PostHandler import json_request, download_posts

base_url = Config.BASE_URL
user_agent = "ePoolGet/1.0 (by OnlyForBlacklist)"  # REQUIRED
time_format = Config.TIME_FORMAT_STRING


def xml_request(api_call):
    """
    Makes an XML request with specified API call and arguments
    """
    http_request = request.Request(base_url + api_call, data=None, headers={'User-Agent': user_agent})
    with request.urlopen(http_request) as response:
        encoded_xml = response.read().decode("utf-8")
    return ET.fromstring(encoded_xml)


def convert_time(time_string):
    """
    Converts time given from API to Unix time for easier comparisons
    """
    return timegm(strptime(time_string, time_format))


class Pool(object):
    def __init__(self, id, last_id=None):
        """
        Initialize Pool object with pool id. Last_id can be specified if migrating from another system.
        """
        self.id = id
        self.last_updated = None
        self.last_id = last_id
        self.last_checked = None
        self.posts = []
        self.name = None
        self.done = False

    def get_info(self):
        """
        Gets all info for pool, excluding posts
        """
        pool_info = xml_request("/pool/show.xml?id=" + str(self.id))
        sleep(1)
        self.name = pool_info.attrib['name']
        self.last_updated = convert_time(pool_info.attrib['updated_at'])

    def get_posts(self):
        """
        Gets all posts for pool
        """
        pool_post_info = json_request("/post/index.json?tags=pool:" + str(self.id))  # works as long as <= 320 pool posts
        sleep(1)
        for post in pool_post_info:
            self.posts.append(post.get('id'))

    def set_update_info(self, id_added, check_time):
        """
        Updates last id added and last check time, and checking if pool is done
        """
        self.last_id = id_added
        self.last_checked = check_time
        if time() - self.last_updated >= 15811200 and not self.done:  # set as done if not updated in 6 months
            self.done = True

    def update(self, last_id=None):
        """
        Gets list of new posts, downloads them, updates pool info
        """
        if self.name is None or self.last_updated is None:  # fresh pool, needs added
            self.get_info()
        if not self.posts:
            self.get_posts()
        if last_id is None:
            if self.last_id is None:
                last_id = 0
            else:
                last_id = int(self.last_id)
        # print("Last ID:", last_id)
        if last_id == 0:  # new pool, download all
            new_posts = self.posts
        elif max(self.posts) > last_id:  # means there are updates and list needs to be split
            new_index = len(self.posts)  # if something goes wrong with finding index, default is to download all
            for i in range(len(self.posts)):
                if self.posts[i] <= last_id:
                    new_index = i
                    break
            new_posts = self.posts[:new_index]
        elif max(self.posts) == last_id:  # does not have updates
            new_posts = []
        # print("New posts:", new_posts)
        # Create filename map based on pool_id and index
        name_map = {}
        for i in range(len(new_posts)):
            name_map[new_posts[i]] = str(self.id) + "_" + str(i)
        # Update and download
        self.set_update_info(max(self.posts), int(time()))
        download_posts(new_posts, filename_map=name_map)

    def serialize(self):
        """
        Returns a JSON-encodeable representation of this pool for saving
        """
        pool_dict = {"id": self.id, "last_updated": self.last_updated, "last_id": self.last_id,
                     "last_checked": self.last_checked, "name": self.name, "done": self.done}
        return pool_dict

    def __str__(self):
        return str({"id": self.id, "last_updated": self.last_updated, "last_id": self.last_id,
                     "last_checked": self.last_checked, "name": self.name, "done": self.done})


class PoolFactory:
    def __init__(self, pool_dict):
        """
        Stores pool_dict for this pool
        """
        self.pool_dict = pool_dict

    def get_pool(self):
        """
        Builds Pool object from given pool_dict, containing saved info about the pool, and returns it
        """
        pool = Pool(self.pool_dict.get('id'))
        pool.last_updated = self.pool_dict.get('last_updated')
        pool.last_id = self.pool_dict.get('last_id')
        pool.last_checked = self.pool_dict.get('last_checked')
        pool.name = self.pool_dict.get('name')
        pool.done = self.pool_dict.get('done')
        return pool