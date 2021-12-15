import time

from django.test import TestCase
from django.utils import timezone
import pytz

from account.models import Userinfo
from . import models
from . import dsync
from . import tasks
from .models import DynamicSyncInfo, Dynamic

from subscribe.models import SubscribeMember, MemberGroup
from io import StringIO
from django.core.management import call_command

CST_TIME_ZONE = pytz.timezone("Asia/Shanghai")


class SyncBeatTest(TestCase):
    def test_command_output(self):
        """
        测试sync_beat指令
        :return:
        """
        out = StringIO()
        call_command('sync_beat', stdout=out)
        self.assertIn('成功调用', out.getvalue())


class ModelTest(TestCase):
    def test_model_and_time(self):
        sm = SubscribeMember()
        sm.mid = 1
        sm.name = "t"
        sm.face = "http://aa.www/a.png"
        sm.last_profile_update = timezone.now()
        sm.save()

        m = models.DynamicMember()
        m.mid = sm
        m.last_dynamic_update = timezone.now()
        m.save()

        d = models.Dynamic()
        d.dynamic_id = 1
        d.member = sm
        d.dynamic_type = 233
        d.timestamp = timezone.datetime.fromtimestamp(1636009208, tz=CST_TIME_ZONE)
        d.raw = {"a": 1}
        d.save()

        self.assertEqual(str(d.timestamp), "2021-11-04 15:00:08+08:00")

        d = models.Dynamic.objects.get(dynamic_id=1)
        self.assertEqual(d.member.mid, 1)

        self.assertEqual(d.timestamp.timestamp(), 1636009208)
        self.assertEqual(str(d.timestamp), "2021-11-04 07:00:08+00:00")
        self.assertEqual(str(d.timestamp.astimezone(CST_TIME_ZONE)), "2021-11-04 15:00:08+08:00")


class DsyncTest(TestCase):
    def setUp(self):
        Userinfo.objects.create_user(
            username='test_user',
            password='12345678',
            email='test@test.test')
        self.client.login(username='test_user', password='12345678')

    def test_dsync(self):
        member = SubscribeMember(mid=8401607)
        dsync.update_member_profile(member)

        member = dsync.get_subscribe_member(8401607)
        self.assertEqual(member.name, "无米酱Official")
        self.assertEqual(dsync.get_subscribe_member(1), None)

        self.assertEqual(dsync.get_saved_latest_dynamic(1), None)

    def test_raw(self):
        mid = 416622817
        member = SubscribeMember(mid=mid)
        dsync.update_member_profile(member)

        tasks.add_member.delay(mid)

        member = dsync.get_subscribe_member(mid)
        self.assertEqual(member.name, "步玎Pudding")
        self.assertNotEqual(dsync.get_saved_latest_dynamic(mid), None)
        self.assertGreater(models.Dynamic.objects.count(), 0)

    def test_task(self):
        response = self.client.get("/subscribe/group_list")
        default_group = response.json()['data'][0]['gid']
        response = self.client.post(
            "/subscribe/subscribe/",
            {
                'mid': 416622817,
                'gid': default_group
            })
        self.assertEqual(response.status_code, 200)

        response = self.client.get("/dynamic/list")
        self.assertEqual(response.status_code, 200)
        json = response.json()
        self.assertEqual(json['data']['has_more'], True)
        self.assertEqual(len(json['data']['data']), 20)
        offset = json['data']['offset']

        response = self.client.get("/dynamic/list", {'offset': offset})
        self.assertEqual(response.status_code, 200)
        json = response.json()
        self.assertEqual(json['data']['has_more'], True)
        self.assertEqual(json['data']['data'][0]['dynamic_id'], offset)

        tasks.call_full_sync(min_interval=3600)

        sync_info = DynamicSyncInfo.get_latest()
        self.assertNotEqual(sync_info, None)
        self.assertEqual(sync_info.finish(), True)
        self.assertEqual(sync_info.total_tasks.count(), 0)
        self.assertEqual(sync_info.success_tasks.count(), 0)

        time.sleep(1)
        tasks.call_full_sync(min_interval=0)

        sync_info = DynamicSyncInfo.get_latest()
        self.assertNotEqual(sync_info, None)
        self.assertEqual(sync_info.finish(), True)
        self.assertEqual(sync_info.total_tasks.count(), 1)
        self.assertEqual(sync_info.success_tasks.count(), 1)

    def test_direct_add(self):
        tasks.direct_sync_dynamic(604029782310941867)
        dy = Dynamic.objects.filter(pk=604029782310941867).first()
        self.assertNotEqual(dy, None)
        self.assertEqual(dy.raw['desc']['uid'], 1473830)

