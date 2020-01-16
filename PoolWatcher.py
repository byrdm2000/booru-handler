import json
from time import time
import PoolHandler


class Watcher(object):
    def __init__(self):
        """
        Loads and prepares pools
        """
        try:
            with open("pools.json", "r") as watchlist:
                pools_json = watchlist.read()
        except FileNotFoundError:
            with open("pools.json", "w") as watchlist:
                watchlist.write("[]")
                pools_json = watchlist.read()

        # Deserialize JSON into Pool objects
        pool_infos = json.loads(pools_json)
        self.pools = []
        for pool_info in pool_infos:
            pool = PoolHandler.PoolFactory(pool_info).get_pool()
            self.pools.append(pool)

    def update(self):
        """
        Checks on status of pools, updates those which need checked again
        """
        # Check which ones need checked or are finished
        pools_to_update = []
        for pool in self.pools:
            if pool.last_checked is not None:  # not fresh, needs actually checked
                if time() - pool.last_checked >= 86400 and not pool.done:
                    pools_to_update.append(pool)
            else:  # Pool is NEW, need to get it
                pools_to_update.append(pool)

        # Update those that need checking
        # progress = 1
        for pool in pools_to_update:
            # progress_string = "[" + str(progress) + "/" + str(len(pools_to_update)) + "]"
            # print("updating pool w/ ID", pool.id, progress_string)
            pool.update()
            # progress += 1

    def add_pool(self, pool_id):
        """
        Adds pool to watchlist
        """
        pool_ids = {pool.id for pool in self.pools}
        if pool_id not in pool_ids:  # prevents duplicates
            pool = PoolHandler.Pool(pool_id)
            self.pools.append(pool)

    def save(self):
        """
        Saves JSON representation of watchlist to file
        """
        pools_json = [pool.serialize() for pool in self.pools]
        with open("pools.json", "w") as watchlist:
            json.dump(pools_json, watchlist)

    def add_pools(self, pool_ids):
        """
            Adds pools in batch to watchlist
        """
        for pool_id in pool_ids:
            self.add_pool(pool_id)

    def remove_duplicates(self):
        unique_ids = {pool.id for pool in self.pools}
        for pool in self.pools:
            if pool.id in unique_ids:
                unique_ids.remove(pool.id)
            else:
                print("removing", pool.id)
                self.pools.remove(pool)


if __name__ == "__main__":
    # Updater for if ran as a service or part of a script
    new_watchlist = Watcher()
    new_watchlist.update()
    new_watchlist.save()
