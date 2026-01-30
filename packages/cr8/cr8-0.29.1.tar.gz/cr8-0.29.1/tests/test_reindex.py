
import tempfile
import shutil
from unittest import IsolatedAsyncioTestCase
from cr8.run_crate import CrateNode, get_crate
from cr8.reindex import areindex
from cr8.clients import client


class TestReindex(IsolatedAsyncioTestCase):

    def setUp(self):
        self._to_stop = []
        self.data_path = tempfile.mkdtemp()
        self.crate_settings = {
            'path.data': self.data_path,
            'cluster.name': 'cr8-reindex-tests',
            'http.port': '44200-44250'
        }

    def tearDown(self):
        for node in self._to_stop:
            node.stop()
        self._to_stop = []
        shutil.rmtree(self.data_path, ignore_errors=True)

    async def test_reindex(self):
        crate_v5 = CrateNode(
            crate_dir=get_crate('5.x.x'),
            keep_data=True,
            settings=self.crate_settings
        )
        self._to_stop.append(crate_v5)
        crate_v5.start()
        async with client(crate_v5.http_url) as c:
            await c.execute("create table t (x int)")
            args = (
                (1,),
                (2,),
                (3,),
            )
            await c.execute_many("insert into t (x) values (?)", args)
        crate_v5.stop()
        self._to_stop.remove(crate_v5)

        crate_v6 = CrateNode(
            crate_dir=get_crate('6.0.0'),
            keep_data=True,
            settings=self.crate_settings
        )
        self._to_stop.append(crate_v6)
        crate_v6.start()
        await areindex(hosts=crate_v6.http_url)
        async with client(crate_v6.http_url) as c:
            result = await c.execute("SELECT version FROM information_schema.tables WHERE table_name = 't'")
            version = result['rows'][0][0]
            self.assertEqual(version, {'upgraded': None, 'created': '6.0.0'})

            result = await c.execute('SELECT count(*) FROM t')
            cnt = result['rows'][0][0]
            self.assertEqual(cnt, 3)
