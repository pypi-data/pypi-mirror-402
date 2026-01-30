import json
import time

from tenacity import retry, stop_after_attempt, wait_exponential

from smartpush.base.request_base import RequestBase
from smartpush.base.url_enum import URL


class Contacts(RequestBase):

    def callGetContactPersonList(self, value):
        """
        查询联系人信息
        :param value:
        :return:
        """
        requestParam = {"rules": {"query": value}, "sessionId": "", "page": 1, "pageSize": 20}
        result = self.request(method=URL.Contacts.getContactPersonList.method,
                              path=URL.Contacts.getContactPersonList.url, data=requestParam)
        return result['resultData']


class AssertContacts(Contacts,):
    tries=3
    @retry(stop=stop_after_attempt(tries), wait=wait_exponential(multiplier=1, min=1, max=2))
    def AssertEmailOrNameInContactPersonList(self, value, subscribeEmailStatus=False, subscribeSmsStatus=False):
        result = self.callGetContactPersonList(value)
        contactPersonDetailList = result['resultData']['contactPersonDetailList']
        for contactPersonDetail in contactPersonDetailList:
            contactPersonDetailEmail = contactPersonDetail['email']
            contactPersonDetailName = contactPersonDetail['userName']
            contactPersonDetailSubscribeEmailStatus = contactPersonDetail['subscribeEmailStatus']
            contactPersonDetailSubscribeSmsStatus = contactPersonDetail['subscribeSmsStatus']
            # 断言内容
            assert contactPersonDetailEmail == value or contactPersonDetailName == value
            assert contactPersonDetailSubscribeEmailStatus == subscribeEmailStatus
            assert contactPersonDetailSubscribeSmsStatus == subscribeSmsStatus


