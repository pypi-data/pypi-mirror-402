from smartpush.base.request_base import ActivityTemplateRequestBase
from smartpush.base.url_enum import URL
from smartpush.email.schema import *
from smartpush.utils.date_utils import *


class ActivityTemplate(ActivityTemplateRequestBase):

    def create_activity_template(self):
        requestParam = {"activityName": "自动化创建草稿活动-" + DateUtils.get_current_datetime_to_str(),
                        "pickContactPacks": [],
                        "smartSending": False, "subjectId": [], "emailName": "测试", "subtitle": "",
                        "sender": "SmartPush_AutoTest_ec2自动化店铺 AutoTestName", "senderDomain": "DEFAULT_DOMAIN",
                        "receiveAddress": "autotest-smartpushauto@smartpush.com", "utmConfigEnable": False,
                        "language": "en", "sendType": "EMAIL", "type": "MKT", "id": None, "domainType": 3,
                        "activityTemplateId": None, "activityId": None, "timezone": None, "timezoneGmt": None,
                        "originTemplate": 6, "createSource": 0, "sendStrategy": "DELAY", "booster": None,
                        "customerGroupIds": [], "excludeContactPacks": [], "excludeCustomerGroupIds": [],
                        "warmupPack": 0}
        result = self.request(path=URL.Activity.step1.url, method=URL.Activity.step1.method, data=requestParam)
        return result

    def update_activity_template_schema(self, currentJsonSchema, schema):
        currentJsonSchema = self.add_element_to_section_column_children(currentJsonSchema, schema)
        final_currentJsonSchema = json.dumps(isinstance) if isinstance(currentJsonSchema, dict) else currentJsonSchema
        requestParam = {"id": self.activityTemplateId,
                        "activityImage": DateUtils.get_current_timestamp(),
                        "blocks": None,
                        "currentHtml": "",
                        "currentJsonSchema": final_currentJsonSchema,
                        "previewJsonSchema": final_currentJsonSchema,
                        "schemaAnalysis": BlockSchema.genSchemaAnalysis(json.loads(final_currentJsonSchema))}

        result = self.request(path=URL.Activity.step2.url, method=URL.Activity.step2.method,
                              data=requestParam)
        return result

    def get_activity_template_step2(self):
        requestParam = {"id": self.activityTemplateId}
        result = self.request(path=URL.Activity.step2_get.url, method=URL.Activity.step2_get.method,
                              params=requestParam)
        return result

    def delete_activity_template_by_id(self, mtoken='123456'):
        """
        删除活动
        :param mtoken:
        :return:
        """
        requestParam = {"id": self.activityTemplateId, "mtoken": mtoken}
        result = self.request(path=URL.Activity.delete.url, method=URL.Activity.delete.method,
                              params=requestParam)
        return result

    def copy_activity_template_by_id(self):
        """
        复制活动
        :return:
        """
        requestParam = {"id": self.activityTemplateId}
        result = self.request(path=URL.Activity.copy.url, method=URL.Activity.copy.method,params=requestParam)
        return result

    @staticmethod
    def add_element_to_section_column_children(currentJsonSchema, new_schema):
        """
        在Section下的Column节点的children中添加元素，并返回原JSON（已修改）
        :param new_schema: 原始JSON字典
        :param currentJsonSchema:  要添加的元素（字典）
        :return: 修改后的原始JSON字典
        """
        # 1. 遍历找到type为Section的节点
        for child in currentJsonSchema.get("children", []):
            if child.get("type") == "Section":
                # 2. 在Section的children中找到Column节点
                for column in child.get("children", []):
                    if column.get("type") == "Column":
                        # 3. 向Column的children添加元素
                        column["children"].append(new_schema)
                        break  # 若有多个Column可根据需求调整，这里匹配第一个Column
                break  # 若有多个Section可根据需求调整，这里匹配第一个Section
        return currentJsonSchema

    @staticmethod
    def get_column_children_universal_property(currentJsonSchema, universalId, property):
        _currentJsonSchema = currentJsonSchema if isinstance(currentJsonSchema, dict) else json.loads(currentJsonSchema)
        for child in _currentJsonSchema.get("children", []):
            if child.get("type") == "Section":
                # 2. 在Section的children中找到Column节点
                for column in child.get("children", []):
                    if column.get("type") == "Column":
                        for block in column.get("children", []):
                            if block.get("universalId") == universalId:
                                result = block.get('props').get(property)
                                return result
        return None

    def assert_activity_template_schema_is_update(self, universalId, property='containerBackgroundColor',
                                                  value='#123456'):
        step2_result = self.get_activity_template_step2()
        currentJsonSchema = json.loads(step2_result['resultData']['currentJsonSchema'])
        assert self.get_column_children_universal_property(currentJsonSchema, universalId, property) == value


if __name__ == '__main__':
    # currentJsonSchema = json.loads(
    #     "{\"id\":\"6ou4lnz43\",\"type\":\"Stage\",\"props\":{\"backgroundColor\":\"#EAEDF1\",\"width\":\"600px\",\"fullWidth\":\"normal-width\"},\"children\":[{\"id\":\"wrgsuiu5a\",\"type\":\"Header\",\"props\":{\"backgroundColor\":\"#ffffff\",\"borderLeft\":\"1px none #ffffff\",\"borderRight\":\"1px none #ffffff\",\"borderTop\":\"1px none #ffffff\",\"borderBottom\":\"1px none #ffffff\",\"paddingTop\":\"0px\",\"paddingBottom\":\"0px\",\"paddingLeft\":\"0px\",\"paddingRight\":\"0px\",\"cols\":[12]},\"children\":[{\"id\":\"jk2qppaqu\",\"type\":\"Column\",\"props\":{},\"children\":[]}]},{\"id\":\"2yowv8vnc\",\"type\":\"Section\",\"props\":{\"backgroundColor\":\"#ffffff\",\"borderLeft\":\"1px none #ffffff\",\"borderRight\":\"1px none #ffffff\",\"borderTop\":\"1px none #ffffff\",\"borderBottom\":\"1px none #ffffff\",\"paddingTop\":\"0px\",\"paddingBottom\":\"0px\",\"paddingLeft\":\"0px\",\"paddingRight\":\"0px\",\"cols\":[12]},\"children\":[{\"id\":\"emkpt5gqk\",\"type\":\"Column\",\"props\":{},\"children\":[{\"id\":\"jpbphqkmt\",\"universalId\":\"08424a7a-cbf5-46ca-808c-cc4eec061d9a\",\"universalName\":\"Auto-Logo-2025-11-26 17:06:31\",\"type\":\"Logo\",\"props\":{\"width\":120,\"height\":120,\"imgRatio\":1,\"src\":\"https://cdn.smartpushedm.com/frontend/smart-push/staging/1741054956275/1758595834300_74d62ae6.png?width=120&height=120\",\"href\":\"https://smartpush4.myshoplinestg.com\",\"align\":\"center\",\"containerBackgroundColor\":\"#123456\",\"paddingLeft\":\"20px\",\"paddingRight\":\"20px\",\"paddingTop\":\"20px\",\"paddingBottom\":\"20px\",\"paddingCondition\":true,\"segmentTypeConfig\":1},\"children\":[]}]}]},{\"id\":\"x3fqcszdh\",\"type\":\"Footer\",\"props\":{\"backgroundColor\":\"#ffffff\",\"borderLeft\":\"1px none #ffffff\",\"borderRight\":\"1px none #ffffff\",\"borderTop\":\"1px none #ffffff\",\"borderBottom\":\"1px none #ffffff\",\"paddingTop\":\"0px\",\"paddingBottom\":\"0px\",\"paddingLeft\":\"0px\",\"paddingRight\":\"0px\",\"cols\":[12]},\"children\":[{\"id\":\"tyqqxszro\",\"type\":\"Column\",\"props\":{},\"children\":[{\"id\":\"xarkbgqzj\",\"type\":\"Subscribe\",\"props\":{\"content\":\"<p style=\\\"text-align:center;\\\"><span style=\\\"font-size:12px\\\"><span style=\\\"font-family:Arial, Helvetica, sans-serif\\\">在此處輸入聯繫地址，可以讓你的顧客更加信任這封郵件</span></span></p>\"},\"children\":[]}]}]}],\"extend\":{\"version\":\"1.0.0\",\"updateTime\":null}}")
    # print(ActivityTemplate.get_column_children_universal_property(currentJsonSchema,
    #                                                               '4c8a94eb-fb4f-4cba-934c-8bbcf4f02f63',
    #                                                               'containerBackgroundColor'))
    headers = {"cookie":"osudb_appid=SMARTPUSH;osudb_oar=#01#SID0000142BBMtQZENFwRum+auwG8xaPKEtK5HgGx0lValeKMgM9lpDwayeZG4gcRV7ZCuWuhkHOLinjdGep+EhqYgs+3jHB4HX+JlKMjwHl+xti50WubQSH0AdBVthnmGoGxKTnB6xlaZ+IjorbD+HKOoEBuJ;osudb_subappid=1;osudb_uid=4213785247;ecom_http_token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3NjY2MzUyNTYsImp0aSI6ImRiOGNkNTIyLTkwMmQtNDcwNS1iM2JkLTc4Nzg5OTQwNzVmNCIsInVzZXJJbmZvIjp7ImlkIjowLCJ1c2VySWQiOiI0MjEzNzg1MjQ3IiwidXNlcm5hbWUiOiIiLCJlbWFpbCI6ImZlbGl4LnNoYW9Ac2hvcGxpbmVhcHAuY29tIiwidXNlclJvbGUiOiJvd25lciIsInBsYXRmb3JtVHlwZSI6Nywic3ViUGxhdGZvcm0iOjEsInBob25lIjoiIiwibGFuZ3VhZ2UiOiJ6aC1oYW5zLWNuIiwiYXV0aFR5cGUiOiIiLCJhdHRyaWJ1dGVzIjp7ImNvdW50cnlDb2RlIjoiQ04iLCJjdXJyZW5jeSI6IkpQWSIsImN1cnJlbmN5U3ltYm9sIjoiSlDCpSIsImRvbWFpbiI6InNtYXJ0cHVzaDQubXlzaG9wbGluZXN0Zy5jb20iLCJsYW5ndWFnZSI6ImVuIiwibWVyY2hhbnRFbWFpbCI6ImZlbGl4LnNoYW9Ac2hvcGxpbmUuY29tIiwibWVyY2hhbnROYW1lIjoiU21hcnRQdXNoNF9lYzJf6Ieq5Yqo5YyW5bqX6ZO6IiwicGhvbmUiOiIiLCJzY29wZUNoYW5nZWQiOmZhbHNlLCJzdGFmZkxhbmd1YWdlIjoiemgtaGFucy1jbiIsInN0YXR1cyI6MCwidGltZXpvbmUiOiJBc2lhL01hY2FvIn0sInN0b3JlSWQiOiIxNjQ0Mzk1OTIwNDQ0IiwiaGFuZGxlIjoic21hcnRwdXNoNCIsImVudiI6IkNOIiwic3RlIjoiIiwidmVyaWZ5IjoiIn0sImxvZ2luVGltZSI6MTc2NDA0MzI1Njk1Miwic2NvcGUiOlsiZW1haWwtbWFya2V0IiwiY29va2llIiwic2wtZWNvbS1lbWFpbC1tYXJrZXQtbmV3LXRlc3QiLCJlbWFpbC1tYXJrZXQtbmV3LWRldi1mcyIsImFwaS11Yy1lYzIiLCJhcGktc3UtZWMyIiwiYXBpLWVtLWVjMiIsImZsb3ctcGx1Z2luIiwiYXBpLXNwLW1hcmtldC1lYzIiXSwiY2xpZW50X2lkIjoiZW1haWwtbWFya2V0In0.dAPLGpef8jYXrIu9Wr-diKNGksWZ3mKmDW_f0djxtKs;"}

    var = ActivityTemplate(444917, 'https://test.smartpushedm.com/bff/api-em-ec2', headers=headers)
    var.copy_activity_template_by_id()