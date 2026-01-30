import random

from smartpush.base.request_base import OpenApiRequestBase
from smartpush.base.url_enum import URL


class OpenApi(OpenApiRequestBase):
    def __init__(self, host, headers, event_id=None, **kwargs):
        """初始化OpenApi，支持传入event_id"""
        super().__init__(event_id, host, headers, **kwargs)
        self.event_id = event_id  # 初始化event_id属性
        self.attrTypeList = ('STRING', 'BIGINT', 'BOOLEAN', 'DATE', 'DECIMAL')

    def get_attribute_type(self, _type=None):
        """
        返回一个数据类型('STRING', 'BIGINT', 'BOOLEAN', 'DATE', 'DECIMAL')
        :param _type:
        :return:
        """

        if _type is not None and _type in self.attrTypeList:
            return _type
        else:
            return random.choice(self.attrTypeList)

    def getEventMetaList(self, code=None, channel=None):
        """
        获取EventMeta数据
        :param code: 事件编码
        :param channel: 渠道类型
        :return: 请求结果
        """
        requestParam = {"pageModel": {"page": 1, "pageSize": 20}}
        # 正确的参数更新逻辑：有值才更新
        if channel:
            requestParam["channel"] = channel
        if code:
            requestParam["code"] = code
        result = self.request(
            path=URL.OpenApi.getEventMetaList.url,
            method=URL.OpenApi.getEventMetaList.method,
            data=requestParam
        )
        return result

    def getEventMetaById(self, eventCode):
        """
        获取事件详情
        :param eventCode: 事件编码
        :return: 请求结果
        """
        if not self.event_id:
            raise ValueError("event_id未初始化，请在实例化时传入")
        requestParam = {"id": self.event_id, "eventCode": eventCode}
        result = self.request(
            path=URL.OpenApi.getEventMetaById.url,
            method=URL.OpenApi.getEventMetaById.method,
            data=requestParam
        )
        return result

    def deleteEventMetaById(self, eventCode):
        """
        删除事件（根据ID）
        :param eventCode: 事件编码
        :return: 请求结果
        """
        if not self.event_id:
            raise ValueError("event_id未初始化，请在实例化时传入")
        requestParam = {"id": self.event_id, "eventCode": eventCode}
        result = self.request(
            path=URL.OpenApi.delEventMetaById.url,
            method=URL.OpenApi.delEventMetaById.method,
            data=requestParam
        )
        return result

    def editEventMeta(self, eventCode, eventName, eventChannel, channelMetaTabi, eventAttrs: list,
                      updateEventAttrs: list, deleteEventAttrs: list):
        if not self.event_id:
            raise ValueError("event_id未初始化，请在实例化时传入")
        requestParam = {
            "eventCode": eventCode,
            "eventName": eventName,
            "eventChannel": eventChannel,
            "eventAttrs": eventAttrs,
            "id": self.event_id,
            "channel": {
                "updateEventChannel": {
                    "channelMetaTabi": channelMetaTabi,
                    "channelCode": "eventChannel"
                }
            },
            "attrs": {
                "updateEventAttrs": updateEventAttrs,
                "deleteEventAttrs": deleteEventAttrs
            }
        }
        result = self.request(
            path=URL.OpenApi.editEventMeta.url,
            method=URL.OpenApi.editEventMeta.method,
            data=requestParam
        )
        return result

    def getEventChannel(self):
        # requestParam = {"id": self.event_id, "eventCode": eventCode}
        result = self.request(
            path=URL.OpenApi.getEventChannel.url,
            method=URL.OpenApi.getEventChannel.method,
        )
        return result

    def getEventAttr(self, pageSize=200, pageNumber=1):
        requestParam = {"pageSize": pageSize, "pageNum": pageNumber}
        result = self.request(
            path=URL.OpenApi.getEventAttr.url,
            method=URL.OpenApi.getEventAttr.method,
            data=requestParam
        )
        return result


class AssertOpenApi(OpenApi):
    def assert_event_create_success(self, code, channel, is_delete=True) -> str:
        """
        断言事件新增成功，并返回eventId
        :param code: 事件编码
        :param channel: 渠道类型
        :param is_delete: 是否删除事件
        :return: eventId
        """
        event_id = None
        try:
            result = self.getEventMetaList(code=code, channel=channel)
            # 安全获取数据，避免KeyError
            result_data = result.get("resultData", {})
            datas = result_data.get("datas", [])

            if not datas:
                raise AssertionError(f"未找到事件：code={code}, channel={channel}")
            matched_data = None
            for data in datas:
                if data.get("eventCode") == code and data.get("channelType") == channel:
                    matched_data = data
                    break
            if not matched_data:
                raise AssertionError(f"事件属性不匹配：code={code}, channel={channel}")

            # 断言关键属性
            assert matched_data.get("isMerchantEvent"), "isMerchantEvent应为True"
            event_id = matched_data.get("eventId")
            assert event_id, "eventId不存在"
            return event_id

        except Exception as e:
            raise AssertionError(f"事件新增断言失败：{str(e)}") from e
        finally:
            if is_delete and event_id:
                self.event_id = event_id
                self.deleteEventMetaById(code)

    def assert_event_attr_create_success(self, attr_code):
        """
        断言事件字段添加成功，并返回attr的id
        :param attr_code:
        :return:
        :rtype: tuple[bool, Any]
        """
        datas = self.getEventAttr().get('resultData', {}).get('datas', []).get('eventAttrs', [])
        for data in datas:
            if data.get('attrCode') == attr_code:
                return True,data.get("attrMetaTabi")
        assert False, f'{attr_code} 新增失败'


if __name__ == '__main__':
    head = {'Content-Type': 'application/json',
            'cookie': 'osudb_appid=SMARTPUSH;osudb_oar=#01#SID0000142BLW1n/EjSTsnwj+GuvYaBsRpZKHfrkfcwypZmDI/ehcXOLaz0i6efc9ot2EmTuPrdEdroZb2nq2KcvcvhQsv7AWwcNMOQ2odLp2dSQFxS7HFcanEI1t8t1sDag3Btf/unj8TzEV+7QkfaB97O+8m;osudb_subappid=1;osudb_uid=4213785247;ecom_http_token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3NjcxNTM2NTYsImp0aSI6IjUxODM2Y2Q1LTliYmEtNDdkMS1hN2ZkLTRkYWFjMmZlMjdmNSIsInVzZXJJbmZvIjp7ImlkIjowLCJ1c2VySWQiOiI0MjEzNzg1MjQ3IiwidXNlcm5hbWUiOiIiLCJlbWFpbCI6ImZlbGl4LnNoYW9Ac2hvcGxpbmVhcHAuY29tIiwidXNlclJvbGUiOiJvd25lciIsInBsYXRmb3JtVHlwZSI6Nywic3ViUGxhdGZvcm0iOjEsInBob25lIjoiIiwibGFuZ3VhZ2UiOiJ6aC1oYW5zLWNuIiwiYXV0aFR5cGUiOiIiLCJhdHRyaWJ1dGVzIjp7ImNvdW50cnlDb2RlIjoiQ04iLCJjdXJyZW5jeSI6IkpQWSIsImN1cnJlbmN5U3ltYm9sIjoiSlDCpSIsImRvbWFpbiI6InNtYXJ0cHVzaDQubXlzaG9wbGluZXN0Zy5jb20iLCJsYW5ndWFnZSI6ImVuIiwibWVyY2hhbnRFbWFpbCI6ImZlbGl4LnNoYW9Ac2hvcGxpbmUuY29tIiwibWVyY2hhbnROYW1lIjoiU21hcnRQdXNoNF9lYzJf6Ieq5Yqo5YyW5bqX6ZO6IiwicGhvbmUiOiIiLCJzY29wZUNoYW5nZWQiOmZhbHNlLCJzdGFmZkxhbmd1YWdlIjoiemgtaGFucy1jbiIsInN0YXR1cyI6MCwidGltZXpvbmUiOiJBc2lhL01hY2FvIn0sInN0b3JlSWQiOiIxNjQ0Mzk1OTIwNDQ0IiwiaGFuZGxlIjoic21hcnRwdXNoNCIsImVudiI6IkNOIiwic3RlIjoiIiwidmVyaWZ5IjoiIiwiaXNGaXJzdEJpbmQiOmZhbHNlfSwibG9naW5UaW1lIjoxNzY0NTYxNjU2NzA1LCJzY29wZSI6WyJlbWFpbC1tYXJrZXQiLCJjb29raWUiLCJzbC1lY29tLWVtYWlsLW1hcmtldC1uZXctdGVzdCIsImVtYWlsLW1hcmtldC1uZXctZGV2LWZzIiwiYXBpLXVjLWVjMiIsImFwaS1zdS1lYzIiLCJhcGktZW0tZWMyIiwiZmxvdy1wbHVnaW4iLCJhcGktc3AtbWFya2V0LWVjMiJdLCJjbGllbnRfaWQiOiJlbWFpbC1tYXJrZXQifQ.bgfuaOJqX2BXDmOorrWrE6iiQswpqYO0bW78pwbP4Wk;',
            'authorization': 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3NjcxNTM2NTYsImp0aSI6IjUxODM2Y2Q1LTliYmEtNDdkMS1hN2ZkLTRkYWFjMmZlMjdmNSIsInVzZXJJbmZvIjp7ImlkIjowLCJ1c2VySWQiOiI0MjEzNzg1MjQ3IiwidXNlcm5hbWUiOiIiLCJlbWFpbCI6ImZlbGl4LnNoYW9Ac2hvcGxpbmVhcHAuY29tIiwidXNlclJvbGUiOiJvd25lciIsInBsYXRmb3JtVHlwZSI6Nywic3ViUGxhdGZvcm0iOjEsInBob25lIjoiIiwibGFuZ3VhZ2UiOiJ6aC1oYW5zLWNuIiwiYXV0aFR5cGUiOiIiLCJhdHRyaWJ1dGVzIjp7ImNvdW50cnlDb2RlIjoiQ04iLCJjdXJyZW5jeSI6IkpQWSIsImN1cnJlbmN5U3ltYm9sIjoiSlDCpSIsImRvbWFpbiI6InNtYXJ0cHVzaDQubXlzaG9wbGluZXN0Zy5jb20iLCJsYW5ndWFnZSI6ImVuIiwibWVyY2hhbnRFbWFpbCI6ImZlbGl4LnNoYW9Ac2hvcGxpbmUuY29tIiwibWVyY2hhbnROYW1lIjoiU21hcnRQdXNoNF9lYzJf6Ieq5Yqo5YyW5bqX6ZO6IiwicGhvbmUiOiIiLCJzY29wZUNoYW5nZWQiOmZhbHNlLCJzdGFmZkxhbmd1YWdlIjoiemgtaGFucy1jbiIsInN0YXR1cyI6MCwidGltZXpvbmUiOiJBc2lhL01hY2FvIn0sInN0b3JlSWQiOiIxNjQ0Mzk1OTIwNDQ0IiwiaGFuZGxlIjoic21hcnRwdXNoNCIsImVudiI6IkNOIiwic3RlIjoiIiwidmVyaWZ5IjoiIiwiaXNGaXJzdEJpbmQiOmZhbHNlfSwibG9naW5UaW1lIjoxNzY0NTYxNjU2NzA1LCJzY29wZSI6WyJlbWFpbC1tYXJrZXQiLCJjb29raWUiLCJzbC1lY29tLWVtYWlsLW1hcmtldC1uZXctdGVzdCIsImVtYWlsLW1hcmtldC1uZXctZGV2LWZzIiwiYXBpLXVjLWVjMiIsImFwaS1zdS1lYzIiLCJhcGktZW0tZWMyIiwiZmxvdy1wbHVnaW4iLCJhcGktc3AtbWFya2V0LWVjMiJdLCJjbGllbnRfaWQiOiJlbWFpbC1tYXJrZXQifQ.bgfuaOJqX2BXDmOorrWrE6iiQswpqYO0bW78pwbP4Wk'}
    openapi = OpenApi(headers=head, host='https://test.smartpushedm.com/bff/api-sp-market-ec2')
    # openapi.getEventMetaList(channel= 'Smartpush_API')
    assertopenapi = AssertOpenApi(headers=head, host='https://test.smartpushedm.com/bff/api-sp-market-ec2')
    print(assertopenapi.assert_event_attr_create_success('cus_autotest_int'))
    # assert False
