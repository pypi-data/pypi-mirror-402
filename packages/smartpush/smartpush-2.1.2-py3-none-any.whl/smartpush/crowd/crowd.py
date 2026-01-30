import json
import time

from tenacity import retry, stop_after_attempt, wait_fixed

from smartpush.base.request_base import CrowdRequestBase, RequestBase
from smartpush.base.url_enum import URL
from smartpush.export.basic.ExcelExportChecker import compare_dicts
from smartpush.export.basic.GetOssUrl import log_attempt
from smartpush.utils import ListDictUtils


class Crowd(CrowdRequestBase):

    def callEditCrowdPackage(self, crowdName="", groupRules=None, groupRelation="$AND",
                             triggerStock=False):
        """
        更新群组条件id
        :param triggerStock:
        :param crowdName:
        :param groupRules:
        :param groupRelation:
        :return:
        """
        requestParam = {"id": self.crowd_id, "crowdName": crowdName, "groupRelation": groupRelation,
                        "groupRules": groupRules, "triggerStock": triggerStock}
        result = self.request(method=URL.Crowd.editCrowdPackage.method, path=URL.Crowd.editCrowdPackage.url, data=requestParam)
        return result['resultData']

    def callCrowdPersonListInPackage(self, page=1, pageSize=20, filter_type=None, operator='eq', filter_value=None):
        """
        获取群组联系人列表
        :param operator:操作符：eq/in/invalidPerson/subscribeStatusEnum/
        :param page:
        :param pageSize:
        :param filter_type: 过滤类型，email、sms、
        :param filter_value:具体值
        :return:
        """
        requestParam = {"id": self.crowd_id, "page": page, "pageSize": pageSize}
        if filter_value is not None:
            requestParam["filter"] = {filter_type: {operator: filter_value}}
        result = self.request(method=URL.Crowd.crowdPersonListInPackage.method,
                              path=URL.Crowd.crowdPersonListInPackage.url,
                              data=requestParam)
        resultData = result['resultData']
        return resultData

    def callCrowdPackageDetail(self, page=1, pageSize=20):
        """
        获取群组详情
        :param page:
        :param pageSize:
        :return:
        """
        requestParam = {"id": self.crowd_id, "page": page, "pageSize": pageSize, "filter": {}}
        # if filter_value is not None:
        #     requestParam["filter"] = {filter_type: {"in": filter_value}}
        result = self.request(method=URL.Crowd.crowdPackageDetail.method, path=URL.Crowd.crowdPackageDetail.url,
                              data=requestParam)
        resultData = result['resultData']
        return resultData

    def check_crowd(self, expected_rule, expected_ids, sleep=5):
        """校验群组结果"""
        result = {}
        # 校验群组详情条件
        crowd_detail = self.callCrowdPackageDetail()
        if crowd_detail["groupRules"] == expected_rule:
            result["rule"] = True
        else:
            result["rule"] = {"条件断言": False, "实际条件": crowd_detail["groupRules"]}
        # 校验群组筛选人群
        time.sleep(sleep)
        crowd_persons = self.callCrowdPersonListInPackage()
        crowd_person_uids = [person["uid"] for person in crowd_persons["responseResult"]]
        print("expected_ids", expected_ids, type(expected_ids))
        print("crowd_person_uids", crowd_person_uids, type(crowd_person_uids))
        result["联系人断言"] = ListDictUtils.check_values_in_list_set(a=expected_ids, b=crowd_person_uids)
        return result


class CrowdList(RequestBase):
    def callCrowdPackageList(self, page=1, pageSize=20):
        """
        获取群组联系人列表
        :param page:
        :param pageSize:
        :param filter_type:
        :param filter_value:
        :return:
        """
        requestParam = {"page": page, "pageSize": pageSize}
        result = self.request(method=URL.Crowd.crowdPackageList.method, path=URL.Crowd.crowdPackageList.url,
                              data=requestParam)
        resultData = result['resultData']
        return resultData

class AssertCrowd(Crowd):
    def __init__(self, crowd_id, host, headers, **kwargs):
        super(AssertCrowd, self).__init__(crowd_id=crowd_id, host=host, headers=headers, **kwargs)
        self.crowd_id = crowd_id

    @retry(stop=stop_after_attempt(3), wait=wait_fixed(3), after=log_attempt)
    def assert_filter_value_in_person_package(self, page=1, pageSize=20, filter_type=None, operator='eq', filter_value=None):
        try:
            crowd_persons = super.callCrowdPersonListInPackage(page=page, pageSize=pageSize, filter_type=filter_type, operator=operator, filter_value=filter_value)
            assert crowd_persons['num'] >=1
            assert crowd_persons['responseResult'][0][filter_type] == filter_value
        except:
            raise


if __name__ == '__main__':
    host = "https://test.smartpushedm.com/bff/api-em-ec2"
    headers = {
        "cookie": "sl_lc_session_id=ARdgF0IxFkAHFAOZAAAAAAAAABJgXW48NEPOu5SFl0dmT_3mihLHpce906zxUbThGnBe; _ga=GA1.1.676535481.1761883127; _ga_D2KXR23WN3=GS2.1.s1761883127$o1$g0$t1761883170$j17$l0$h0; sl_lr_session_id=ARdiIhhRFkAHFBUHAAAAAAAAAF08xxHuy0uKhjUqNs0ySkc050947mcvDaYK1whe3bi0; sp-session-open=true; osudb_lang=; sl_sc_session_id=ARdjNlKHFkAHFBUHAAAAAAAAACKxXGuiEEi6p_f7aB_GsR1asT_RaDMApK3eKmrzF7K4; sl_sr_session_id=ARdjNlKHFkAHFBUHAAAAAAAAALw794pz7UbdgxmE9hqsfoCD0maOX-3IE8uxltg4-wSI; osudb_appid=SMARTPUSH; osudb_subappid=1; osudb_uid=4600602538; osudb_oar=#01#SID0000142BPp54f8NDtV4PIn2E2jFeSWv0Yvr3/bJiObNipUuVmL68bE0gjeq6e4AvQlafd9IfQNXzplOpO1uv7soFJlYEudAcdY+RHiefXV9GaweU3oaqcQhHDeybhaEVH1wYJxato/m3SY4rrPu/mgUba51; JSESSIONID=176938AB2D7E2F1BBEDB9B71E88EE8D5",
        # "authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3NjA2NzA4MzUsImp0aSI6ImQyZTkxMzMyLTYwMTMtNGI3NC04NzAzLWQzZDAxMzkyNTdjNSIsInVzZXJJbmZvIjp7ImlkIjowLCJ1c2VySWQiOiI0NjAwNjAyNTM4IiwidXNlcm5hbWUiOiIiLCJlbWFpbCI6Imx1Lmx1QHNob3BsaW5lLmNvbSIsInVzZXJSb2xlIjoib3duZXIiLCJwbGF0Zm9ybVR5cGUiOjcsInN1YlBsYXRmb3JtIjoxLCJwaG9uZSI6IiIsImxhbmd1YWdlIjoiemgtaGFucy1jbiIsImF1dGhUeXBlIjoiIiwiYXR0cmlidXRlcyI6eyJjb3VudHJ5Q29kZSI6IkNOIiwiY3VycmVuY3kiOiJVU0QiLCJjdXJyZW5jeVN5bWJvbCI6IlVTJCIsImRvbWFpbiI6Imx1LWx1LmVtYWlsIiwibGFuZ3VhZ2UiOiJ6aC1oYW50LXR3IiwibWVyY2hhbnRFbWFpbCI6Imx1Lmx1QHNob3BsaW5lLmNvbSIsIm1lcmNoYW50TmFtZSI6Imx1bHUzODIt6K6i6ZiF5byP55S15ZWGIiwicGhvbmUiOiIiLCJzY29wZUNoYW5nZWQiOmZhbHNlLCJzdGFmZkxhbmd1YWdlIjoiemgtaGFucy1jbiIsInN0YXR1cyI6MCwidGltZXpvbmUiOiJBc2lhL1NoYW5naGFpIn0sInN0b3JlSWQiOiIxNzQ1Mzc3NzA1OTM2IiwiaGFuZGxlIjoibHVsdTM4MiIsImVudiI6IkNOIiwic3RlIjoiIiwidmVyaWZ5IjoiIn0sImxvZ2luVGltZSI6MTc1ODA3ODgzNTYwMiwic2NvcGUiOlsiZW1haWwtbWFya2V0IiwiY29va2llIiwic2wtZWNvbS1lbWFpbC1tYXJrZXQtbmV3LXRlc3QiLCJlbWFpbC1tYXJrZXQtbmV3LWRldi1mcyIsImFwaS11Yy1lYzIiLCJhcGktc3UtZWMyIiwiYXBpLWVtLWVjMiIsImZsb3ctcGx1Z2luIiwiYXBpLXNwLW1hcmtldC1lYzIiXSwiY2xpZW50X2lkIjoiZW1haWwtbWFya2V0In0.ZMtJ83tH8i-BArVnSvfS4rKCD49N8WLsnhxVJ11BddI"
    }


    # crowd_id = "687a028fa34ae35465dc91a2"

    # def diff_person(_crowd_id, path):
    ## 这里是查询群组的人的差异
    # list_len = 0
    # flag = True
    # page = 1
    # crowd = Crowd(crowd_id=_crowd_id, host=host, headers=headers)
    # result_list = []
    #
    # while flag:
    #     result = crowd.callCrowdPersonListInPackage(pageSize=100, page=page)
    #     page += 1
    #     num = result['num']
    #     list_len += len(result['responseResult'])
    #     for data in result['responseResult']:
    #         result_list.append(data['id'])
    #     if list_len >= num:
    #         break
    # print(result_list)
    # print("es查询群组数量：", len(result_list))

    #     # 这里是解析本地文件，查看
    #     key = ["user_id"]
    #     data = read_excel_file_form_local_path(path, key)
    #     print(data)
    #     print(list(data.get(key)))
    #     compare_lists(list(data.get("crowd_id")))
    #
    #
    def diff_crowd_num(sql_result_list):
        ## 比较哪些群组数量不一致
        _sql_result_list = {item["crowd_id"]: item["num"] for item in sql_result_list}
        crowd_list = CrowdList(host=host, headers=headers)
        cc = crowd_list.callCrowdPackageList(1, 100)
        crowd_dict = {i['id']: i['nums'] for i in cc['responseList']}

        print("-----sql_result_list-----:\n", json.dumps(sql_result_list, ensure_ascii=False))
        print("****crowd_dict*****:\n", json.dumps(cc, ensure_ascii=False))
        print(f"人群列表数量:{len(crowd_dict)}，hive数量：{len(_sql_result_list)}")
        print(":::::差异:::::\n", json.dumps(compare_dicts(crowd_dict, _sql_result_list), ensure_ascii=False))


    sql_result_list = [
  {
    "crowd_id": "682b0aca244a981570817656",
    "num": "4"
  },
  {
    "crowd_id": "69086abbd283550420102410",
    "num": "19"
  },
  {
    "crowd_id": "6822ad71d917d574ee10133c",
    "num": "3"
  },
  {
    "crowd_id": "6858f2e0a4025622a4245310",
    "num": "3"
  },
  {
    "crowd_id": "68e880910d5a50be1f816898",
    "num": "1"
  },
  {
    "crowd_id": "682c2cc8da627a549206b8eb",
    "num": "152"
  },
  {
    "crowd_id": "68e87fd00d5a50be1f816897",
    "num": "2"
  },
  {
    "crowd_id": "68e87f440d5a50be1f816896",
    "num": "2"
  },
  {
    "crowd_id": "68244081702ed60ff73adbc6",
    "num": "4"
  },
  {
    "crowd_id": "68c93bfe68575727b9f02269",
    "num": "1"
  },
  {
    "crowd_id": "6923fc88870f8d72c6d05de7",
    "num": "19"
  },
  {
    "crowd_id": "6923fec9870f8d72c6d05e01",
    "num": "15"
  },
  {
    "crowd_id": "691e7c1de425257bf240470a",
    "num": "155"
  },
  {
    "crowd_id": "6923fcf8870f8d72c6d05dec",
    "num": "18"
  },
  {
    "crowd_id": "6923ff07870f8d72c6d05e08",
    "num": "2"
  },
  {
    "crowd_id": "6923fcbe870f8d72c6d05dea",
    "num": "1"
  },
  {
    "crowd_id": "6923fda9870f8d72c6d05df5",
    "num": "14"
  },
  {
    "crowd_id": "6923fdfc870f8d72c6d05df9",
    "num": "8"
  },
  {
    "crowd_id": "6912db312f12dc67394a50d1",
    "num": "2"
  },
  {
    "crowd_id": "6923fe45870f8d72c6d05dfb",
    "num": "6"
  },
  {
    "crowd_id": "69240e54870f8d72c6d05e87",
    "num": "6"
  },
  {
    "crowd_id": "691d98b8ff6d32155eeb5efc",
    "num": "152"
  },
  {
    "crowd_id": "6923ff57870f8d72c6d05e13",
    "num": "4"
  },
  {
    "crowd_id": "6923ff40870f8d72c6d05e12",
    "num": "12"
  },
  {
    "crowd_id": "6923ff1d870f8d72c6d05e0c",
    "num": "5"
  },
  {
    "crowd_id": "6923fd66870f8d72c6d05df0",
    "num": "15"
  },
  {
    "crowd_id": "6924101b870f8d72c6d05e91",
    "num": "10"
  }
]
    diff_crowd_num(sql_result_list)

    # diff_person(_crowd_id="687a028fa34ae35465dc91a2",
    #             path="/Users/lulu/Downloads/临时文件2_20250719155155.xls")
