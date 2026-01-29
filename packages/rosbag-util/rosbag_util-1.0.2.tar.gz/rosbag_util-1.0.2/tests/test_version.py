import rosbag_util


def test_version_exposed():
    assert isinstance(rosbag_util.__version__, str)
