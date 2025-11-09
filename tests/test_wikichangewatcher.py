import time
import json
from unittest import mock, TestCase
from queue import Queue

from wikichangewatcher import (
    WikiChangeWatcher, FilterCollection, IpV4Filter, IpV6Filter, UsernameRegexSearchFilter,
    PageUrlRegexSearchFilter, FieldRegexSearchFilter, MatchType
)


class FakeEvent(object):
    def __init__(self, event_type='message', event_data={}):
        self.event = event_type
        self.data = event_data


class FakeSSEClient(object):
    def __init__(self, events=[]):
        self.events = Queue()
        for e in events:
            self.events.put(e)

    def __next__(self):
        return self.events.get() if self.events.qsize() > 0 else make_event(event_type='nothing')

    def __iter__(self):
        return self


def make_event(user="test-user", event_type='message', log_event=False, invalid_event=False,
               title_url="https://fake-url.com", **kwargs):
    ret = {"namespace": -1 if log_event else 0, "user": user, "title_url": title_url}
    ret.update(**kwargs)

    if invalid_event:
        del ret['title_url']

    return FakeEvent(event_type, json.dumps(ret))


class TestWikiChangeWatcher(TestCase):
    @mock.patch('wikichangewatcher.wikichangewatcher.SSEClient')
    def test_ipv4_filter_multi_fixed(self, mock_sseclient):
        filtered_events = Queue()

        def handle_event(event):
            filtered_events.put(event)

        addr = "192.168.33.44"
        fltr = IpV4Filter(addr).on_match(handle_event)

        mock_client = FakeSSEClient([
            make_event(user="test-user", title_url="url_user"),
            make_event(user="192.44.44.44", title_url="url_a"),
            make_event(user="192.44.55.44", title_url="url_b"),
            make_event(user=addr, title_url="url_c"),
            make_event(user=addr, title_url="url_d")
        ])

        mock_sseclient.return_value = mock_client

        wc = WikiChangeWatcher(None, fltr)
        wc.run()
        time.sleep(0.1)
        wc.stop()

        self.assertEqual(filtered_events.qsize(), 2)

        url_c_event = filtered_events.get()
        url_d_event = filtered_events.get()
        self.assertEqual(url_c_event['title_url'], 'url_c')
        self.assertEqual(url_d_event['title_url'], 'url_d')

    @mock.patch('wikichangewatcher.wikichangewatcher.SSEClient')
    def test_ipv4_filter_multi_range(self, mock_sseclient):
        filtered_events = Queue()

        def handle_event(event):
            filtered_events.put(event)

        addr = "192.168.33.0-5"
        fltr = IpV4Filter(addr).on_match(handle_event)

        mock_client = FakeSSEClient([
            make_event(user="test-user", title_url="url_user"),
            make_event(user="192.44.44.44", title_url="url_a"),
            make_event(user="192.44.55.44", title_url="url_b"),
            make_event(user="192.168.33.0", title_url="url_c"),
            make_event(user="192.168.33.1", title_url="url_d"),
            make_event(user="192.168.33.2", title_url="url_e"),
            make_event(user="192.168.33.3", title_url="url_f"),
            make_event(user="192.168.33.4", title_url="url_g"),
            make_event(user="192.168.33.5", title_url="url_h"),
            make_event(user="192.168.33.6", title_url="url_i"),
        ])

        mock_sseclient.return_value = mock_client

        wc = WikiChangeWatcher(None, fltr)
        wc.run()
        time.sleep(0.1)
        wc.stop()

        self.assertEqual(filtered_events.qsize(), 6)

        url_c_event = filtered_events.get()
        url_d_event = filtered_events.get()
        url_e_event = filtered_events.get()
        url_f_event = filtered_events.get()
        url_g_event = filtered_events.get()
        url_h_event = filtered_events.get()

        self.assertEqual(url_c_event['title_url'], 'url_c')
        self.assertEqual(url_d_event['title_url'], 'url_d')
        self.assertEqual(url_e_event['title_url'], 'url_e')
        self.assertEqual(url_f_event['title_url'], 'url_f')
        self.assertEqual(url_g_event['title_url'], 'url_g')
        self.assertEqual(url_h_event['title_url'], 'url_h')

    @mock.patch('wikichangewatcher.wikichangewatcher.SSEClient')
    def test_ipv4_filter_multi_range_wildcard(self, mock_sseclient):
        filtered_events = Queue()

        def handle_event(event):
            filtered_events.put(event)

        addr = "192.168.*.0-5"
        fltr = IpV4Filter(addr).on_match(handle_event)

        mock_client = FakeSSEClient([
            make_event(user="test-user", title_url="url_user"),
            make_event(user="192.44.44.44", title_url="url_a"),
            make_event(user="192.44.55.44", title_url="url_b"),
            make_event(user="192.168.0.0", title_url="url_c"),
            make_event(user="192.168.0.1", title_url="url_d"),
            make_event(user="192.168.0.2", title_url="url_e"),
            make_event(user="192.168.0.3", title_url="url_f"),
            make_event(user="192.168.0.4", title_url="url_g"),
            make_event(user="192.168.0.5", title_url="url_h"),
            make_event(user="192.168.255.0", title_url="url_i"),
            make_event(user="192.168.255.1", title_url="url_j"),
            make_event(user="192.168.255.2", title_url="url_k"),
            make_event(user="192.168.255.3", title_url="url_l"),
            make_event(user="192.168.255.4", title_url="url_m"),
            make_event(user="192.168.255.5", title_url="url_n"),
            make_event(user="192.168.0.6", title_url="url_o"),
            make_event(user="192.168.255.6", title_url="url_p"),
        ])

        mock_sseclient.return_value = mock_client

        wc = WikiChangeWatcher(None, fltr)
        wc.run()
        time.sleep(0.1)
        wc.stop()

        self.assertEqual(filtered_events.qsize(), 12)

        url_c_event = filtered_events.get()
        url_d_event = filtered_events.get()
        url_e_event = filtered_events.get()
        url_f_event = filtered_events.get()
        url_g_event = filtered_events.get()
        url_h_event = filtered_events.get()
        url_i_event = filtered_events.get()
        url_j_event = filtered_events.get()
        url_k_event = filtered_events.get()
        url_l_event = filtered_events.get()
        url_m_event = filtered_events.get()
        url_n_event = filtered_events.get()

        self.assertEqual(url_c_event['title_url'], 'url_c')
        self.assertEqual(url_d_event['title_url'], 'url_d')
        self.assertEqual(url_e_event['title_url'], 'url_e')
        self.assertEqual(url_f_event['title_url'], 'url_f')
        self.assertEqual(url_g_event['title_url'], 'url_g')
        self.assertEqual(url_h_event['title_url'], 'url_h')
        self.assertEqual(url_i_event['title_url'], 'url_i')
        self.assertEqual(url_j_event['title_url'], 'url_j')
        self.assertEqual(url_k_event['title_url'], 'url_k')
        self.assertEqual(url_l_event['title_url'], 'url_l')
        self.assertEqual(url_m_event['title_url'], 'url_m')
        self.assertEqual(url_n_event['title_url'], 'url_n')

    @mock.patch('wikichangewatcher.wikichangewatcher.SSEClient')
    def test_ipv6_filter_multi_fixed(self, mock_sseclient):
        filtered_events = Queue()

        def handle_event(event):
            filtered_events.put(event)

        addr = "0000:1111:2222:3333:4444:5555:6666:7777"
        fltr = IpV6Filter(addr).on_match(handle_event)

        mock_client = FakeSSEClient([
            make_event(user="test-user", title_url="url_user"),
            make_event(user="192.44.44.44", title_url="url_a"),
            make_event(user="a:a:a:a:a:a:a:a", title_url="url_b"),
            make_event(user=addr, title_url="url_c"),
            make_event(user=addr, title_url="url_d")
        ])

        mock_sseclient.return_value = mock_client

        wc = WikiChangeWatcher(None, fltr)
        wc.run()
        time.sleep(0.1)
        wc.stop()

        self.assertEqual(filtered_events.qsize(), 2)

        url_c_event = filtered_events.get()
        url_d_event = filtered_events.get()
        self.assertEqual(url_c_event['title_url'], 'url_c')
        self.assertEqual(url_d_event['title_url'], 'url_d')

    @mock.patch('wikichangewatcher.wikichangewatcher.SSEClient')
    def test_ipv6_filter_multi_range(self, mock_sseclient):
        filtered_events = Queue()

        def handle_event(event):
            filtered_events.put(event)

        addr = "0000:1111:2222:3333:4444:5555:6666:0-5"
        fltr = IpV6Filter(addr).on_match(handle_event)

        mock_client = FakeSSEClient([
            make_event(user="test-user", title_url="url_user"),
            make_event(user="192.44.44.44", title_url="url_a"),
            make_event(user="a:a:a:a:a:a:a:a", title_url="url_b"),
            make_event(user="0000:1111:2222:3333:4444:5555:6666:0", title_url="url_c"),
            make_event(user="0000:1111:2222:3333:4444:5555:6666:1", title_url="url_d"),
            make_event(user="0000:1111:2222:3333:4444:5555:6666:2", title_url="url_e"),
            make_event(user="0000:1111:2222:3333:4444:5555:6666:3", title_url="url_f"),
            make_event(user="0000:1111:2222:3333:4444:5555:6666:4", title_url="url_g"),
            make_event(user="0000:1111:2222:3333:4444:5555:6666:5", title_url="url_h"),
            make_event(user="0000:1111:2222:3333:4444:5555:6666:6", title_url="url_i"),
        ])

        mock_sseclient.return_value = mock_client

        wc = WikiChangeWatcher(None, fltr)
        wc.run()
        time.sleep(0.1)
        wc.stop()

        self.assertEqual(filtered_events.qsize(), 6)

        url_c_event = filtered_events.get()
        url_d_event = filtered_events.get()
        url_e_event = filtered_events.get()
        url_f_event = filtered_events.get()
        url_g_event = filtered_events.get()
        url_h_event = filtered_events.get()

        self.assertEqual(url_c_event['title_url'], 'url_c')
        self.assertEqual(url_d_event['title_url'], 'url_d')
        self.assertEqual(url_e_event['title_url'], 'url_e')
        self.assertEqual(url_f_event['title_url'], 'url_f')
        self.assertEqual(url_g_event['title_url'], 'url_g')
        self.assertEqual(url_h_event['title_url'], 'url_h')

    @mock.patch('wikichangewatcher.wikichangewatcher.SSEClient')
    def test_ipv6_filter_multi_range_wildcard(self, mock_sseclient):
        filtered_events = Queue()

        def handle_event(event):
            filtered_events.put(event)

        addr = "0000:1111:2222:3333:4444:5555:*:0-5"
        fltr = IpV6Filter(addr).on_match(handle_event)

        mock_client = FakeSSEClient([
            make_event(user="test-user", title_url="url_user"),
            make_event(user="192.44.44.44", title_url="url_a"),
            make_event(user="a:a:a:a:a:a:a:a", title_url="url_b"),
            make_event(user="0000:1111:2222:3333:4444:5555:0:0", title_url="url_c"),
            make_event(user="0000:1111:2222:3333:4444:5555:0:1", title_url="url_d"),
            make_event(user="0000:1111:2222:3333:4444:5555:0:2", title_url="url_e"),
            make_event(user="0000:1111:2222:3333:4444:5555:0:3", title_url="url_f"),
            make_event(user="0000:1111:2222:3333:4444:5555:0:4", title_url="url_g"),
            make_event(user="0000:1111:2222:3333:4444:5555:0:5", title_url="url_h"),
            make_event(user="0000:1111:2222:3333:4444:5555:ffff:0", title_url="url_i"),
            make_event(user="0000:1111:2222:3333:4444:5555:ffff:1", title_url="url_j"),
            make_event(user="0000:1111:2222:3333:4444:5555:ffff:2", title_url="url_k"),
            make_event(user="0000:1111:2222:3333:4444:5555:ffff:3", title_url="url_l"),
            make_event(user="0000:1111:2222:3333:4444:5555:ffff:4", title_url="url_m"),
            make_event(user="0000:1111:2222:3333:4444:5555:ffff:5", title_url="url_n"),
            make_event(user="0000:1111:2222:3333:4444:5555:0:6", title_url="url_o"),
            make_event(user="0000:1111:2222:3333:4444:5555:ffff:6", title_url="url_p"),
        ])

        mock_sseclient.return_value = mock_client

        wc = WikiChangeWatcher(None, fltr)
        wc.run()
        time.sleep(0.1)
        wc.stop()

        self.assertEqual(filtered_events.qsize(), 12)

        url_c_event = filtered_events.get()
        url_d_event = filtered_events.get()
        url_e_event = filtered_events.get()
        url_f_event = filtered_events.get()
        url_g_event = filtered_events.get()
        url_h_event = filtered_events.get()
        url_i_event = filtered_events.get()
        url_j_event = filtered_events.get()
        url_k_event = filtered_events.get()
        url_l_event = filtered_events.get()
        url_m_event = filtered_events.get()
        url_n_event = filtered_events.get()

        self.assertEqual(url_c_event['title_url'], 'url_c')
        self.assertEqual(url_d_event['title_url'], 'url_d')
        self.assertEqual(url_e_event['title_url'], 'url_e')
        self.assertEqual(url_f_event['title_url'], 'url_f')
        self.assertEqual(url_g_event['title_url'], 'url_g')
        self.assertEqual(url_h_event['title_url'], 'url_h')
        self.assertEqual(url_i_event['title_url'], 'url_i')
        self.assertEqual(url_j_event['title_url'], 'url_j')
        self.assertEqual(url_k_event['title_url'], 'url_k')
        self.assertEqual(url_l_event['title_url'], 'url_l')
        self.assertEqual(url_m_event['title_url'], 'url_m')
        self.assertEqual(url_n_event['title_url'], 'url_n')

    @mock.patch('wikichangewatcher.wikichangewatcher.SSEClient')
    def test_username_filter_multi_fixed(self, mock_sseclient):
        filtered_events = Queue()

        def handle_event(event):
            filtered_events.put(event)

        user = "other-test-user"
        fltr = UsernameRegexSearchFilter(user).on_match(handle_event)

        mock_client = FakeSSEClient([
            make_event(user="test-user", title_url="url_user"),
            make_event(user="192.44.44.44", title_url="url_a"),
            make_event(user="0:1:2:3:a:b:c:d", title_url="url_b"),
            make_event(user=user, title_url="url_c"),
            make_event(user=user, title_url="url_d")
        ])

        mock_sseclient.return_value = mock_client

        wc = WikiChangeWatcher(None, fltr)
        wc.run()
        time.sleep(0.1)
        wc.stop()

        self.assertEqual(filtered_events.qsize(), 2)

        url_c_event = filtered_events.get()
        url_d_event = filtered_events.get()
        self.assertEqual(url_c_event['title_url'], 'url_c')
        self.assertEqual(url_d_event['title_url'], 'url_d')

    @mock.patch('wikichangewatcher.wikichangewatcher.SSEClient')
    def test_pageurl_filter_multi_fixed(self, mock_sseclient):
        filtered_events = Queue()

        def handle_event(event):
            filtered_events.put(event)

        url = "special-test-url"
        fltr = PageUrlRegexSearchFilter(url).on_match(handle_event)

        mock_client = FakeSSEClient([
            make_event(user="test-user", title_url="url_user"),
            make_event(user="192.44.44.44", title_url="url_a"),
            make_event(user="0:1:2:3:a:b:c:d", title_url="url_b"),
            make_event(user="editor1", title_url=url),
            make_event(user="editor2", title_url=url)
        ])

        mock_sseclient.return_value = mock_client

        wc = WikiChangeWatcher(None, fltr)
        wc.run()
        time.sleep(0.1)
        wc.stop()

        self.assertEqual(filtered_events.qsize(), 2)

        url_1_event = filtered_events.get()
        url_2_event = filtered_events.get()
        self.assertEqual(url_1_event['title_url'], url)
        self.assertEqual(url_1_event['user'], "editor1")
        self.assertEqual(url_2_event['title_url'], url)
        self.assertEqual(url_2_event['user'], "editor2")

    @mock.patch('wikichangewatcher.wikichangewatcher.SSEClient')
    def test_pageurl_filter_combine_bitwise(self, mock_sseclient):
        filtered_events = Queue()

        def handle_event(event):
            filtered_events.put(event)

        collection = (IpV4Filter("1.1.1.1") & PageUrlRegexSearchFilter("john") |
                      IpV6Filter("a:a:a:a:a:a:a:a")).on_match(handle_event)

        mock_client = FakeSSEClient([
            make_event(user="test-user", title_url="url_user"),
            make_event(user="192.44.44.44", title_url="url_a"),
            make_event(user="1.1.1.1", title_url="john"),
            make_event(user="a:a:a:a:a:a:a:a", title_url="john2"),
            make_event(user="1.1.1.1", title_url="sally"),
            make_event(user="1.1.1.2", title_url="john"),
        ])

        mock_sseclient.return_value = mock_client

        wc = WikiChangeWatcher(None, collection)
        wc.run()
        time.sleep(0.1)
        wc.stop()

        self.assertEqual(filtered_events.qsize(), 2)

        url_1_event = filtered_events.get()
        url_2_event = filtered_events.get()
        self.assertEqual(url_1_event['title_url'], 'john')
        self.assertEqual(url_1_event['user'], '1.1.1.1')
        self.assertEqual(url_2_event['title_url'], 'john2')
        self.assertEqual(url_2_event['user'], 'a:a:a:a:a:a:a:a')

    @mock.patch('wikichangewatcher.wikichangewatcher.SSEClient')
    def test_pageurl_two_collections_combine_bitwise(self, mock_sseclient):
        filtered_events = Queue()

        def handle_event(event):
            filtered_events.put(event)

        collection1 = FilterCollection(IpV4Filter("1.1.1.1") & PageUrlRegexSearchFilter("john"))
        collection2 = FilterCollection(IpV6Filter("a:a:a:a:a:a:a:a"))
        collection = (collection1 | collection2).on_match(handle_event)

        mock_client = FakeSSEClient([
            make_event(user="test-user", title_url="url_user"),
            make_event(user="192.44.44.44", title_url="url_a"),
            make_event(user="1.1.1.1", title_url="john"),
            make_event(user="a:a:a:a:a:a:a:a", title_url="john2"),
            make_event(user="1.1.1.1", title_url="sally"),
            make_event(user="1.1.1.2", title_url="john"),
        ])

        mock_sseclient.return_value = mock_client

        wc = WikiChangeWatcher(None, collection)
        wc.run()
        time.sleep(0.1)
        wc.stop()

        self.assertEqual(filtered_events.qsize(), 2)

        url_1_event = filtered_events.get()
        url_2_event = filtered_events.get()
        self.assertEqual(url_1_event['title_url'], 'john')
        self.assertEqual(url_1_event['user'], '1.1.1.1')
        self.assertEqual(url_2_event['title_url'], 'john2')
        self.assertEqual(url_2_event['user'], 'a:a:a:a:a:a:a:a')

    @mock.patch('wikichangewatcher.wikichangewatcher.SSEClient')
    def test_pageurl_filter_collection_combine_bitwise(self, mock_sseclient):
        filtered_events = Queue()

        def handle_event(event):
            filtered_events.put(event)

        collection1 = FilterCollection(IpV4Filter("1.1.1.1") & PageUrlRegexSearchFilter("john"))
        collection = (collection1 | IpV6Filter("a:a:a:a:a:a:a:a")).on_match(handle_event)

        mock_client = FakeSSEClient([
            make_event(user="test-user", title_url="url_user"),
            make_event(user="192.44.44.44", title_url="url_a"),
            make_event(user="1.1.1.1", title_url="john"),
            make_event(user="a:a:a:a:a:a:a:a", title_url="john2"),
            make_event(user="1.1.1.1", title_url="sally"),
            make_event(user="1.1.1.2", title_url="john"),
        ])

        mock_sseclient.return_value = mock_client

        wc = WikiChangeWatcher(None, collection)
        wc.run()
        time.sleep(0.1)
        wc.stop()

        self.assertEqual(filtered_events.qsize(), 2)

        url_1_event = filtered_events.get()
        url_2_event = filtered_events.get()
        self.assertEqual(url_1_event['title_url'], 'john')
        self.assertEqual(url_1_event['user'], '1.1.1.1')
        self.assertEqual(url_2_event['title_url'], 'john2')
        self.assertEqual(url_2_event['user'], 'a:a:a:a:a:a:a:a')

    @mock.patch('wikichangewatcher.wikichangewatcher.SSEClient')
    def test_pageurl_filter_collection_combine_bitwise_swapped_order(self, mock_sseclient):
        filtered_events = Queue()

        def handle_event(event):
            filtered_events.put(event)

        collection1 = FilterCollection(IpV4Filter("1.1.1.1") & PageUrlRegexSearchFilter("john"))
        collection = (IpV6Filter("a:a:a:a:a:a:a:a") | collection1).on_match(handle_event)

        mock_client = FakeSSEClient([
            make_event(user="test-user", title_url="url_user"),
            make_event(user="192.44.44.44", title_url="url_a"),
            make_event(user="1.1.1.1", title_url="john"),
            make_event(user="a:a:a:a:a:a:a:a", title_url="john2"),
            make_event(user="1.1.1.1", title_url="sally"),
            make_event(user="1.1.1.2", title_url="john"),
        ])

        mock_sseclient.return_value = mock_client

        wc = WikiChangeWatcher(None, collection)
        wc.run()
        time.sleep(0.1)
        wc.stop()

        self.assertEqual(filtered_events.qsize(), 2)

        url_1_event = filtered_events.get()
        url_2_event = filtered_events.get()
        self.assertEqual(url_1_event['title_url'], 'john')
        self.assertEqual(url_1_event['user'], '1.1.1.1')
        self.assertEqual(url_2_event['title_url'], 'john2')
        self.assertEqual(url_2_event['user'], 'a:a:a:a:a:a:a:a')


    @mock.patch('wikichangewatcher.wikichangewatcher.SSEClient')
    def test_pageurl_filter_collections_same_match_type(self, mock_sseclient):
        filtered_events = Queue()

        def handle_event(event):
            filtered_events.put(event)

        collection1 = FilterCollection(IpV4Filter("1.1.1.1"), IpV4Filter("2.2.2.2")).set_match_type(MatchType.ANY)
        collection2 = FilterCollection(IpV4Filter("3.3.3.3")).set_match_type(MatchType.ANY)
        collection = (collection1 | collection2).on_match(handle_event)

        mock_client = FakeSSEClient([
            make_event(user="test-user", title_url="url_user"),
            make_event(user="192.44.44.44", title_url="url_a"),
            make_event(user="1.1.1.1", title_url="john"),
            make_event(user="2.2.2.2", title_url="sally"),
            make_event(user="3.3.3.3", title_url="mark"),
            make_event(user="3.3.1.3", title_url="mark"),
        ])

        mock_sseclient.return_value = mock_client

        wc = WikiChangeWatcher(None, collection)
        wc.run()
        time.sleep(0.1)
        wc.stop()

        self.assertEqual(filtered_events.qsize(), 3)

        user_1_event = filtered_events.get()
        user_2_event = filtered_events.get()
        user_3_event = filtered_events.get()
        self.assertEqual(user_1_event['title_url'], 'john')
        self.assertEqual(user_1_event['user'], '1.1.1.1')
        self.assertEqual(user_2_event['title_url'], 'sally')
        self.assertEqual(user_2_event['user'], '2.2.2.2')
        self.assertEqual(user_3_event['title_url'], 'mark')
        self.assertEqual(user_3_event['user'], '3.3.3.3')

    @mock.patch('wikichangewatcher.wikichangewatcher.SSEClient')
    def test_filter_collection_add_filter(self, mock_sseclient):
        filtered_events = Queue()

        def handle_event(event):
            filtered_events.put(event)

        collection1 = FilterCollection(IpV4Filter("1.1.1.1") & PageUrlRegexSearchFilter("john"))

        collection2 = FilterCollection(IpV6Filter("a:a:a:a:a:a:a:a"))
        collection = (collection1 | collection2).on_match(handle_event)

        mock_client = FakeSSEClient([
            make_event(user="test-user", title_url="url_user"),
            make_event(user="192.44.44.44", title_url="url_a"),
            make_event(user="1.1.1.1", title_url="john"),
            make_event(user="a:a:a:a:a:a:a:a", title_url="john2"),
            make_event(user="1.1.1.1", title_url="sally"),
            make_event(user="1.1.1.2", title_url="john"),
        ])

        mock_sseclient.return_value = mock_client

        wc = WikiChangeWatcher(None).add_filter(collection)
        wc.run()
        time.sleep(0.1)
        wc.stop()

        self.assertEqual(filtered_events.qsize(), 2)

        url_1_event = filtered_events.get()
        url_2_event = filtered_events.get()
        self.assertEqual(url_1_event['title_url'], 'john')
        self.assertEqual(url_1_event['user'], '1.1.1.1')
        self.assertEqual(url_2_event['title_url'], 'john2')
        self.assertEqual(url_2_event['user'], 'a:a:a:a:a:a:a:a')

    @mock.patch('wikichangewatcher.wikichangewatcher.SSEClient')
    def test_invalid_bitwise_combine(self, mock_sseclient):
        filtered_events = Queue()

        def handle_event(event):
            filtered_events.put(event)

        collection1 = FilterCollection(IpV4Filter("1.1.1.1"), IpV4Filter("2.2.2.2")).set_match_type(MatchType.ANY)

        valueerror_raised = False
        try:
            collection = (collection1 | 2).on_match(handle_event)
        except ValueError:
            valueerror_raised = True

        self.assertTrue(valueerror_raised)

    @mock.patch('wikichangewatcher.wikichangewatcher.SSEClient')
    def test_log_events_ignored(self, mock_sseclient):
        filtered_events = Queue()

        def handle_event(event):
            filtered_events.put(event)

        addr = "192.168.33.44"
        fltr = IpV4Filter(addr).on_match(handle_event)

        mock_client = FakeSSEClient([
            make_event(user="test-user", title_url="url_user"),
            make_event(user="192.44.44.44", title_url="url_a"),
            make_event(user="192.44.55.44", title_url="url_b"),
            make_event(user=addr, title_url="url_c"),
            make_event(user=addr, title_url="url_d"),
            make_event(user=addr, title_url="url_e", log_event=True),
            make_event(user=addr, title_url="url_f", log_event=True),
            make_event(user=addr, title_url="url_g", log_event=True),
        ])

        mock_sseclient.return_value = mock_client

        wc = WikiChangeWatcher(None, fltr)
        wc.run()
        time.sleep(0.1)
        wc.stop()

        self.assertEqual(filtered_events.qsize(), 2)

        url_c_event = filtered_events.get()
        url_d_event = filtered_events.get()
        self.assertEqual(url_c_event['title_url'], 'url_c')
        self.assertEqual(url_d_event['title_url'], 'url_d')

    def test_invalid_ipv4_filter(self):
        self.assertRaises(ValueError, IpV4Filter, "hey")
        self.assertRaises(ValueError, IpV4Filter, "22")
        self.assertRaises(ValueError, IpV4Filter, "22.22.22")
        self.assertRaises(ValueError, IpV4Filter, "22.22.22.33.33")
        self.assertRaises(ValueError, IpV4Filter, "22.22.hi.22")
        self.assertRaises(ValueError, IpV4Filter, "22.22.22.22-25-27")
        self.assertRaises(ValueError, IpV4Filter, "22.22.22!.22")
        self.assertRaises(ValueError, IpV4Filter, "22.22.22.256")
        self.assertRaises(ValueError, IpV4Filter, "22.22.22.-1")
        self.assertRaises(ValueError, IpV4Filter, "22.**.22.22")

    def test_invalid_ipv6_filter(self):
        self.assertRaises(ValueError, IpV6Filter, "hey")
        self.assertRaises(ValueError, IpV6Filter, "abcd")
        self.assertRaises(ValueError, IpV6Filter, "abcd:dd:dd:dd")
        self.assertRaises(ValueError, IpV6Filter, "abcd:dd:dd:dd:ee:ee:ee:ho")
        self.assertRaises(ValueError, IpV6Filter, "abcd:dd:dd:dd:ee:ee:ee:ee:ee")
        self.assertRaises(ValueError, IpV6Filter, "abcd:dd:dd:dd:ee:ee:ee:0-2-3")
        self.assertRaises(ValueError, IpV6Filter, "abcd:dd:dd:dd:ee:ee:ee:!3")
        self.assertRaises(ValueError, IpV6Filter, "abcd:dd:dd:dd:ee:ee:ee:fffff")
        self.assertRaises(ValueError, IpV6Filter, "abcd:dd:dd:dd:ee:ee:ee:-1")
        self.assertRaises(ValueError, IpV6Filter, "abcd:dd:dd:dd:ee:ee:**:ee")

    def test_string_representations(self):
        self.assertEqual(str(IpV4Filter("1.2.3.4")), 'IpV4Filter("1.2.3.4")')
        self.assertEqual(repr(IpV4Filter("1.2.3.4")), 'IpV4Filter("1.2.3.4")')

        self.assertEqual(str(IpV6Filter("a:a:a:a:a:a:a:a")), 'IpV6Filter("a:a:a:a:a:a:a:a")')
        self.assertEqual(repr(IpV6Filter("a:a:a:a:a:a:a:a")), 'IpV6Filter("a:a:a:a:a:a:a:a")')

        self.assertEqual(str(PageUrlRegexSearchFilter("[Bb]ot")), 'PageUrlRegexSearchFilter("[Bb]ot")')
        self.assertEqual(repr(PageUrlRegexSearchFilter("[Bb]ot")), 'PageUrlRegexSearchFilter("[Bb]ot")')

        self.assertEqual(str(UsernameRegexSearchFilter("blabla")), 'UsernameRegexSearchFilter("blabla")')
        self.assertEqual(repr(UsernameRegexSearchFilter("blabla")), 'UsernameRegexSearchFilter("blabla")')

        self.assertEqual(str(FieldRegexSearchFilter("blabla", "bloobloo")), 'FieldRegexSearchFilter(blabla, "bloobloo")')
        self.assertEqual(repr(FieldRegexSearchFilter("blabla", "bloobloo")), 'FieldRegexSearchFilter(blabla, "bloobloo")')

        self.assertEqual(str(FilterCollection(IpV6Filter(), IpV4Filter())), 'FilterCollection(ALL, IpV6Filter("*:*:*:*:*:*:*:*"), IpV4Filter("*.*.*.*"))')
        self.assertEqual(repr(FilterCollection(IpV6Filter(), IpV4Filter())), 'FilterCollection(ALL, IpV6Filter("*:*:*:*:*:*:*:*"), IpV4Filter("*.*.*.*"))')

    @mock.patch('wikichangewatcher.wikichangewatcher.SSEClient')
    def test_dropped_sse_event(self, mock_sseclient):
        filtered_events = Queue()

        def handle_event(event):
            filtered_events.put(event)

        addr = "192.168.33.44"
        fltr = IpV4Filter(addr).on_match(handle_event)

        mock_client = FakeSSEClient([make_event(invalid_event=True)])

        mock_sseclient.return_value = mock_client

        wc = WikiChangeWatcher(None, fltr)
        wc.run()
        time.sleep(0.1)
        wc.stop()

        self.assertEqual(filtered_events.qsize(), 0)
