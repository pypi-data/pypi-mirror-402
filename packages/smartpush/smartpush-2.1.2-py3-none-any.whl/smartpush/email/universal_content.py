import time
from typing import Optional, List, Dict, Any

from smartpush.base.request_base import RequestBase
from smartpush.base.url_enum import *
from smartpush.email.schema import *


def gen_universal_request_param(universalId, schema, **kwargs):
    """
    生成单个universal的请求参数
    :param schema:
    :type universalId:
    kwargs :
    universalName/subUniversal_id/type/flowModal
    """
    universalName = kwargs.get('universalName', gen_universal_name(schema))
    result_schema = get_universal_schema(schema=schema, _id=generate_UUID(9), universalId=universalId,
                                         universalName=universalName)
    requestParam = {
        "universalId": universalId,
        "universalName": universalName,
        "schema": json.dumps(result_schema),
        "subUniversalId": kwargs.get('subUniversal_id', universalId),
        "type": BlockType.getType(result_schema.get('type')),
        "blockType": result_schema.get('type'),
        "flowModal": kwargs.get('flowModal', '')
    }
    return json.dumps(requestParam) if kwargs.get('jsonDumps') else requestParam


def gen_update_universal_param(
        block_schema_list: Optional[List[Dict[str, Any]]] = None,
        section_schema: Optional[Dict[str, Any]] = None
) -> dict[str, list[dict[str, Any]] | int]:
    """
    根据Block列表生成更新参数，支持同时更新关联的Section（Section始终放在参数列表首位）

    :param block_schema_list: Block schema列表（每个元素为字典格式的schema）
    :param section_schema: Section schema字典（可选，传入则同步更新Section）
    :return: 统一格式的更新请求参数列表（字典类型，未序列化）
    """
    # 初始化参数列表和Block收集列表（默认空列表，避免None判断）
    update_params: List[Dict[str, Any]] = []
    valid_block_schemas: List[Dict[str, Any]] = []
    type = 0
    # 处理Block参数（过滤无效schema，避免异常）
    block_schema_list = block_schema_list or []
    for block_schema in block_schema_list:
        if not isinstance(block_schema, dict):
            print("不符合格式：",block_schema)
            continue  # 跳过非字典格式的无效schema
        # 提取必要字段（无默认值时用空字符串兜底，避免KeyError）
        universal_id = block_schema.get('universalId', '')
        universal_name = block_schema.get('universalName', '')

        # 生成Block更新参数（指定jsonDumps=False返回字典，保持格式统一）
        block_param = gen_universal_request_param(
            universalId=universal_id,
            schema=block_schema,
            jsonDumps=False,
            universalName=universal_name
        )
        update_params.append(block_param)

        # 收集有效Block，用于更新Section的children
        if section_schema:
            valid_block_schemas.append(block_schema)

    # 处理Section参数（如需同步更新，插入列表首位）
    if isinstance(section_schema, dict):
        # 提取Section必要字段
        section_id = section_schema.get('universalId', '')
        section_name = section_schema.get('universalName', '')
        section_inner_id = section_schema.get('id', '')

        # 若有有效Block，更新Section的children（保持原逻辑）
        final_section_schema = section_schema
        if valid_block_schemas:
            final_section_schema = get_universal_schema(
                schema=BlockSchema.genSection(valid_block_schemas),
                _id=section_inner_id,
                universalId=section_id,
                universalName=section_name
            )

        # 生成Section更新参数
        section_param = gen_universal_request_param(
            universalId=section_id,
            schema=final_section_schema,
            jsonDumps=False,
            universalName=section_name
        )
        type = 1
        # 插入列表开头（确保Section在首位）
        update_params.insert(0, section_param)
    print(f"生成更新请求参数（共{len(update_params)}个）：\n{json.dumps(update_params, indent=2, ensure_ascii=False)}")
    return {'data':update_params,'type':type}


class UniversalContent(RequestBase):
    # 写一个init初始化
    def __init__(self, universal_id=None, *args, **kwargs):
        """初始化，传入"""
        super().__init__(*args, **kwargs)  # 调用父类初始化
        self.universal_id = universal_id  # 初始化event_id属性

    # 创建universal
    def create_universal(self, requestParam):
        result = self.request(method=URL.UniversalContent.saveUniversalContent.method,
                              path=URL.UniversalContent.saveUniversalContent.url,
                              data=requestParam)
        return result

    # 查询universal
    def query_universal(self, universa_name='', blockType_list=[]):
        """
        查询素材
        :param blockType_list:
        :param universa_name:
        :return:
        """
        requestParam = {'universalName': universa_name}
        if blockType_list and type(blockType_list) == list:
            requestParam.update(blockType=blockType_list)
        result = self.request(method=URL.UniversalContent.queryUniversalContent.method,
                              path=URL.UniversalContent.queryUniversalContent.url,
                              data=requestParam)
        return result

    # 更新universal
    def update_universal(self, universal_list):
        """
        更新素材，需要多个universal参数组合，type参数为section =1 ，block =0，有section和block时取section
        :param universal_list:
        {
            "data": [
                {
                    "universalId": "9a1d1b16-7b48-4f9e-9dc9-f379efd746a5",
                    "universalName": "Auto-Section-2025-12-03 14:44:01",
                    "schema": "{\"id\": \"546bced03\", \"universalId\": \"9a1d1b16-7b48-4f9e-9dc9-f379efd746a5\", \"universalName\": \"Auto-Section-2025-12-03 14:44:01\", \"type\": \"Section\", \"props\": {\"backgroundColor\": \"#f1e6e6\", \"borderLeft\": \"1px none #ffffff\", \"borderRight\": \"1px none #ffffff\", \"borderTop\": \"1px none #ffffff\", \"borderBottom\": \"1px none #ffffff\", \"paddingTop\": \"0px\", \"paddingBottom\": \"0px\", \"paddingLeft\": \"0px\", \"paddingRight\": \"0px\", \"cols\": [12]}, \"children\": [{\"id\": \"8cab9aa48\", \"type\": \"Column\", \"props\": {}, \"children\": [{\"id\": \"f4baab96e\", \"universalId\": \"eed20601-e227-4481-897b-42e4a1a9d37a\", \"universalName\": \"Auto-Logo-2025-12-03 14:44:01\", \"type\": \"Logo\", \"props\": {\"width\": \"120\", \"height\": \"120\", \"imgRatio\": 1, \"src\": \"https://cdn.smartpushedm.com/frontend/smart-push/staging/1741054956275/1758595834300_74d62ae6.png?width=120&height=120\", \"href\": \"https://smartpush4.myshoplinestg.com\", \"align\": \"center\", \"containerBackgroundColor\": \"transparent\", \"paddingLeft\": \"20px\", \"paddingRight\": \"20px\", \"paddingTop\": \"20px\", \"paddingBottom\": \"20px\", \"paddingCondition\": true, \"segmentTypeConfig\": 1}, \"children\": []}]}]}",
                    "subUniversalId": "9a1d1b16-7b48-4f9e-9dc9-f379efd746a5",
                    "type": 1,
                    "blockType": "Section",
                    "flowModal": ""
                },
                {
                    "universalId": "eed20601-e227-4481-897b-42e4a1a9d37a",
                    "universalName": "Auto-Logo-2025-12-03 14:44:01",
                    "schema": "{\"id\": \"f4baab96e\", \"universalId\": \"eed20601-e227-4481-897b-42e4a1a9d37a\", \"universalName\": \"Auto-Logo-2025-12-03 14:44:01\", \"type\": \"Logo\", \"props\": {\"width\": \"120\", \"height\": \"120\", \"imgRatio\": 1, \"src\": \"https://cdn.smartpushedm.com/frontend/smart-push/staging/1741054956275/1758595834300_74d62ae6.png?width=120&height=120\", \"href\": \"https://smartpush4.myshoplinestg.com\", \"align\": \"center\", \"containerBackgroundColor\": \"transparent\", \"paddingLeft\": \"20px\", \"paddingRight\": \"20px\", \"paddingTop\": \"20px\", \"paddingBottom\": \"20px\", \"paddingCondition\": true, \"segmentTypeConfig\": 1}, \"children\": []}",
                    "subUniversalId": "eed20601-e227-4481-897b-42e4a1a9d37a",
                    "type": 0,
                    "blockType": "Logo",
                    "flowModal": ""
                }
            ],
            "type": 1
        }
        :return:
        """
        # block_type_list = []
        # for data in universal_list:
        #     block_type_list.append(data['type'])
        # if BlockType.Section.value in set(block_type_list):
        #     _type = BlockType.Section.value
        # else:
        #     _type = BlockType.Block.value
        requestParam = universal_list
        result = self.request(method=URL.UniversalContent.updateUniversalContent.method,
                              path=URL.UniversalContent.updateUniversalContent.url,
                              data=requestParam)
        return result

    # 删除universal
    def delete_universal(self, universalId):
        """
        删除素材
        :param universalId:
        :param universa_id:
        :return:
        """
        requestParam = {'universalId': universalId}
        result = self.request(method=URL.UniversalContent.deleteUniversalContent.method,
                              path=URL.UniversalContent.deleteUniversalContent.url,
                              params=requestParam)
        return result

    def update_campaign_used(self, campaignId, universalIds: list, _type=0):
        """
        更新活动素材关系
        :param campaignId:
        :param universalIds:
        :param _type:
        :return:
        """
        requestParam = {"type": _type, "campaignId": campaignId, "universalIds": universalIds}
        result = self.request(method=URL.UniversalContent.updateCampaignUsed.method,
                              path=URL.UniversalContent.updateCampaignUsed.url,
                              data=requestParam)
        return result

    def assert_block_in_the_section(self, section_universa_name, block_universa=None):
        """
        判断收藏的block是否在该section中
        :param block_universa:
        :param section_universa_name:
        :return:
        """
        section = {}
        result = self.query_universal(universa_name=section_universa_name)
        if result:
            section = result['resultData']['datas'][0]
            schema = json.loads(section['schema'])
        if section['blockType'] == 'Section':
            try:
                assert block_universa == schema['children'][0]['children']
                # if block_universa_id: # assert ListDictUtils.all_in_list(block_universa_id, #
                # [blockUniversalId:ss['universalId'] ) elif block_universa_name: assert ListDictUtils.all_in_list(
                # block_universa_name, [ss['universalName'] for ss in schema['children'][0]['children']]) elif _id:
                # assert ListDictUtils.all_in_list(_id, [ss['id'] for ss in schema['children'][0]['children']])
                print(f"------收藏的block在该section({section_universa_name})中,断言成功------")
            except:
                raise

    @staticmethod
    def assert_universal_schema_is_update(schema, property='containerBackgroundColor', value='#123456'):
        """
        用于查找素材schema的属性是否更新成功
        :param schema:
        :param property:
        :param value:
        :return:
        """
        _schema = schema if isinstance(schema, dict) else json.loads(schema)
        assert _schema['props'][property] == value


def get_time():
    return str(time.strftime('%Y-%m-%d %H:%M:%S', time.localtime()))


def gen_universal_name(schema):
    """
    生成素材名称
    :param schema:
    :return:
    """
    schema = schema if isinstance(schema, dict) else schema.value
    if schema['type']:
        return 'Auto-' + schema['type'] + '-' + get_time()
    else:
        return 'Auto-' + generate_UUID(5) + '-' + get_time()


def get_universal_schema(schema, _id, universalId, universalName):
    """
    获取素材中的schema
    :param schema:
    :param _id:
    :param universalId:
    :param universalName:
    :return:
    """
    schema = schema if isinstance(schema, dict) else schema.value
    schema.update(id=_id, universalId=universalId, universalName=universalName)
    return schema


if __name__ == '__main__':
    sectionUniversalId = generate_UUID()
    sectionUniversalName = gen_universal_name(BlockSchema.Section)
    # print(sectionUniversalName)
    block_list = [BlockSchema.Logo,BlockSchema.Discount]
    # block_dict = {}
    result_list = []
    # update_request_param = []
    # blockUniversalNameList = []
    for block in block_list:
        name = block.name
        universal_id = generate_UUID()
        block_schema = get_universal_schema(block, _id=generate_UUID(9), universalId=universal_id,
                                            universalName=gen_universal_name(block))
        block_request_param = gen_universal_request_param(universal_id, block_schema, jsonDumps=False)
        result_list.append(block_schema)
        # update_request_param.append(block_request_param)
    section_schema = get_universal_schema(BlockSchema.genSection(result_list), _id=generate_UUID(9),
                                          universalId=sectionUniversalId,
                                          universalName=sectionUniversalName)
    # section_universal_request_param = gen_universal_request_param(sectionUniversalId, section_schema, jsonDumps=False)
    #
    # update_request_param.insert(0, section_universal_request_param)
    # print("update_request_param:", update_request_param)
    # print(result_list)
    # print(section_schema)
    print(gen_update_universal_param(result_list,section_schema))
    # print("universal_request_param:", section_universal_request_param)
    # head = {
    #     "cookie": "osudb_appid=SMARTPUSH;osudb_oar=#01#SID0000141BOhqtUqYGMjRho2SIPBeE5o1HNWFHo9q+qttt/jMLf+gRshde7x0NZUgAST4PB4CfSuAa450BCuCZf6pwolP1vXs/cF+6e/snBhESLvofXaxDaIFN9swZq4Np2xBc4uw6R4V58uWjrwg+s8XTLVv;osudb_subappid=1;osudb_uid=4213785247;ecom_http_token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3NjU1OTg0NzQsImp0aSI6ImU0YzAyZjcxLWQ4NDktNDZlYS1iNzNmLTY1YjU0YTc3MTJjZCIsInVzZXJJbmZvIjp7ImlkIjowLCJ1c2VySWQiOiI0MjEzNzg1MjQ3IiwidXNlcm5hbWUiOiIiLCJlbWFpbCI6ImZlbGl4LnNoYW9Ac2hvcGxpbmVhcHAuY29tIiwidXNlclJvbGUiOiJvd25lciIsInBsYXRmb3JtVHlwZSI6Nywic3ViUGxhdGZvcm0iOjEsInBob25lIjoiIiwibGFuZ3VhZ2UiOiJ6aC1oYW5zLWNuIiwiYXV0aFR5cGUiOiIiLCJhdHRyaWJ1dGVzIjp7ImNvdW50cnlDb2RlIjoiQ04iLCJjdXJyZW5jeSI6IkpQWSIsImN1cnJlbmN5U3ltYm9sIjoiSlDCpSIsImRvbWFpbiI6InNtYXJ0cHVzaDQubXlzaG9wbGluZXN0Zy5jb20iLCJsYW5ndWFnZSI6ImVuIiwibWVyY2hhbnRFbWFpbCI6ImZlbGl4LnNoYW9Ac2hvcGxpbmUuY29tIiwibWVyY2hhbnROYW1lIjoiU21hcnRQdXNoNF9lYzJf6Ieq5Yqo5YyW5bqX6ZO6IiwicGhvbmUiOiIiLCJzY29wZUNoYW5nZWQiOmZhbHNlLCJzdGFmZkxhbmd1YWdlIjoiemgtaGFucy1jbiIsInN0YXR1cyI6MCwidGltZXpvbmUiOiJBc2lhL01hY2FvIn0sInN0b3JlSWQiOiIxNjQ0Mzk1OTIwNDQ0IiwiaGFuZGxlIjoic21hcnRwdXNoNCIsImVudiI6IkNOIiwic3RlIjoiIiwidmVyaWZ5IjoiIn0sImxvZ2luVGltZSI6MTc2MzAwNjQ3NDQzNywic2NvcGUiOlsiZW1haWwtbWFya2V0IiwiY29va2llIiwic2wtZWNvbS1lbWFpbC1tYXJrZXQtbmV3LXRlc3QiLCJlbWFpbC1tYXJrZXQtbmV3LWRldi1mcyIsImFwaS11Yy1lYzIiLCJhcGktc3UtZWMyIiwiYXBpLWVtLWVjMiIsImZsb3ctcGx1Z2luIiwiYXBpLXNwLW1hcmtldC1lYzIiXSwiY2xpZW50X2lkIjoiZW1haWwtbWFya2V0In0.erTiG4r364sutySNgx8X1rmrAjFsyfoe3UIUZ6J9e-o;",
    #     "Content-Type": "application/json", "accept-language": "zh-CN"}
    # universal = UniversalContent(headers=head, host='https://test.smartpushedm.com/bff/api-sp-market-ec2')
    # universal.update_universal(update_request_param)
    #
    # universal = UniversalContent(headers=head, host='https://test.smartpushedm.com/bff/api-sp-market-ec2')
    # try:
    #     # universal.create_universal(requestParam=universal_request_param)
    #     # universal.assert_block_in_the_section(sectionUniversalName, result_list)
    #     _list =[
    #         {"universalId": "ec5d5278-4ed7-4933-8010-2b0c6a776356", "universalName": "Auto-Logo-2025-11-26 00:35:35",
    #          "schema": "{\"id\":\"96997bb0a\",\"universalId\":\"ec5d5278-4ed7-4933-8010-2b0c6a776356\",\"universalName\":\"Auto-Logo-2025-11-26 00:35:35\",\"type\":\"Logo\",\"props\":{\"width\":120,\"height\":120,\"imgRatio\":1,\"src\":\"https://cdn.smartpushedm.com/frontend/smart-push/staging/1741054956275/1758595834300_74d62ae6.png?width=120&height=120\",\"href\":\"https://smartpush4.myshoplinestg.com\",\"align\":\"center\",\"containerBackgroundColor\":\"#b46b6b\",\"paddingLeft\":\"20px\",\"paddingRight\":\"20px\",\"paddingTop\":\"20px\",\"paddingBottom\":\"20px\",\"paddingCondition\":\"true\",\"segmentTypeConfig\":1},\"children\":[]}",
    #          "subUniversalId": "ec5d5278-4ed7-4933-8010-2b0c6a776356", "type": 0, "blockType": "Logo",
    #          "flowModal": ""}]
    #     universal.update_universal(_list)
    # except:
    #     raise
    # finally:
    #     # universal.delete_universal(sectionUniversalId)
    #     # pass
    #     pass
#
