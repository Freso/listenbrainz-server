import json
import os
from collections import defaultdict
from datetime import datetime

import listenbrainz_spark.stats.user.artist as artist_stats
from listenbrainz_spark import utils
from listenbrainz_spark.path import LISTENBRAINZ_DATA_DIRECTORY
from listenbrainz_spark.tests import SparkTestCase
from pyspark.sql import Row


class ArtistTestCase(SparkTestCase):
    # use path_ as prefix for all paths in this class.
    path_ = LISTENBRAINZ_DATA_DIRECTORY

    def tearDown(self):
        path_found = utils.path_exists(self.path_)
        if path_found:
            utils.delete_dir(self.path_, recursive=True)

    def save_dataframe(self):
        now = datetime.now()

        with open(self.path_to_data_file('user_top_artists.json')) as f:
            data = json.load(f)

        df = None
        for entry in data:
            for idx in range(0, entry['count']):
                # Assign listened_at to each listen
                row = utils.create_dataframe(Row(user_name=entry['user_name'], artist_name=entry['artist_name'],
                                                 artist_msid=entry['artist_msid'], artist_mbids=entry['artist_mbids']),
                                             schema=None)
                df = df.union(row) if df else row

        utils.save_parquet(df, os.path.join(self.path_, '{}/{}.parquet'.format(now.year, now.month)))

    def test_get_artists(self):
        self.save_dataframe()
        df = utils.get_listens(datetime.now(), datetime.now(), self.path_)
        df.createOrReplaceTempView('test_view')

        expected = defaultdict(list)
        with open(self.path_to_data_file('user_top_artists.json')) as f:
            data = json.load(f)

        for entry in data:
            expected[entry['user_name']].append({
                'artist_name': entry['artist_name'],
                'artist_msid': entry['artist_msid'],
                'artist_mbids': entry['artist_mbids'],
                'listen_count': entry['count']
            })

        # Sort in descending order w.r.t to listen_count
        for user_name, user_artists in expected.items():
            user_artists.sort(key=lambda artist: artist['listen_count'], reverse=True)

        received = artist_stats.get_artists('test_view')

        self.assertDictEqual(received, expected)
