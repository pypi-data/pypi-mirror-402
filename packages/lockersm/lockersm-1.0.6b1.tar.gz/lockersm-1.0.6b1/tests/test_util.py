from datetime import datetime

from locker import util
from locker.ls_resources.secret import Secret


class TestUtil(object):
    def test_get_object_classes(self):
        assert isinstance(util.get_object_classes(), dict)

    def test_convert_to_ls_object(self):
        resp = {
            "object": "secret",
            "id": "secret-id",
            "data": {
              "key": "MOCK_KEY_SECRET",
              "value": "MOCK_VALUE_SECRET",
              "description": None
            },
            "key": "MOCK_KEY_SECRET",
            "value": "MOCK_VALUE_SECRET",
            "description": None,
            "creation_date": 1686109221.0,
            "revision_date": 1686109221.0,
            "updated_date": 1686109221.0,
            "deleted_date": None,
            "last_use_date": None,
            "project_id": 1,
            "environment_id": None
        }
        obj = util.convert_to_ls_object(resp)
        assert isinstance(obj, Secret)
        assert obj.key == resp.get("data").get("key")
        assert obj.value == resp.get("data").get("value")
        assert obj.description == resp.get("data").get("description")

    def test_read_special_variable(self):
        access_key_id_test = "access_key_id_test"
        secret_access_key_test = "secret_access_key_test"
        access_key_id_default = "THE_ID_DEFAULT"
        secret_access_key_default = "THE_SECRET_DEFAULT"
        params = {
            "access_key_id": access_key_id_test,
            "secret_access_key": secret_access_key_test
        }
        access_key_id = util.read_special_variable(params, "access_key_id", default_value=None)
        secret_access_key = util.read_special_variable(params, "secret_access_key", default_value=None)
        assert access_key_id == access_key_id_test
        assert secret_access_key == secret_access_key_test

        params = {
            "access_key_id": access_key_id_test,
            "secret_access_key": secret_access_key_test
        }
        access_key_id = util.read_special_variable(params, "access_key_id", access_key_id_default)
        secret_access_key = util.read_special_variable(params, "secret_access_key", secret_access_key_default)
        assert access_key_id == access_key_id_default
        assert secret_access_key == secret_access_key_default

    def test_encode_datetime(self):
        utc_ts = util.encode_datetime(datetime(2023, 1, 1))
        assert isinstance(utc_ts, int) or isinstance(utc_ts, float)
        assert utc_ts <= 1672506000 + 60

    def test_api_encode(self):
        data = {"search": "live_search_text", "page": "1", "size": 10}
        encoded_params = list(util.api_encode(data))
        for encoded_param in encoded_params:
            assert encoded_param[1] == data.get(encoded_param[0])

    def test_merge_dicts(self):
        x = {"x_key": "x_value"}
        y = {"y_key": "y_value"}
        z_expected = x.copy()
        z_expected.update(y)
        z = util.merge_dicts(x, y)
        assert z == z_expected
