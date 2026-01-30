from enum import Enum, unique

POST = 'POST'
GET = 'GET'


@unique
class BaseEnum(Enum):
    @property
    def method(self):
        return self.value[1]

    @property
    def url(self):
        return self.value[0]


class URL:
    """
    GET的参数用params，
    POST参数用data，
    """

    class FormReport(BaseEnum):
        """
        :type:表单报告
        """
        pageFormReportDetail = '/formReport/detail/pageFormReportDetail', POST  # 获取表单收集数据
        getFormReportDetail = '/formReport/getFormReportDetail', POST  # 获取表单报告数据(曝光/点击)
        getFormPerformanceTrend = 'formReport/getFormPerformanceTrend', POST

    class Crowd(BaseEnum):
        """
        :type 群组
        """
        editCrowdPackage = '/crowdPackage/editCrowdPackage', POST
        crowdPersonListInPackage = '/crowdPackage/crowdPersonList', POST
        crowdPackageDetail = '/crowdPackage/detail', POST
        crowdPackageList = '/crowdPackage/list', POST

    class Contacts(BaseEnum):
        """
        :type 联系人
        """
        getContactPersonList = '/contact/getContactPersonList', POST

    class Form(BaseEnum):
        """
        :type 表单操作
        """
        deleteForm = '/form/deleteFormInfo', GET
        getFormList = '/form/getFormList', POST
        getFormInfo = '/form/getFormInfo', GET

    class UniversalContent(BaseEnum):
        """
        :type 素材收藏
        """
        saveUniversalContent = "/universalContent/saveUniversalContent", POST
        deleteUniversalContent = "/universalContent/deleteUniversalContent", GET
        updateUniversalContent = "/universalContent/updateUniversalContent", POST
        queryUniversalContent = "/universalContent/query", POST
        updateCampaignUsed = "/universalContent/updateCampaignUsed", POST
        queryUsedDetail = "/universalContent/queryUsedDetail", POST

    class Activity(BaseEnum):
        """
        :type 活动
        """
        step1 = "/marketing/insertOrUpdateActivity/step1", POST
        step2 = "/marketing/insertOrUpdateActivity/step2", POST
        step2_get = "/marketing/activityDetail/step2", GET
        delete = "/marketing/deleteActivity", GET
        copy = '/marketing/copyActivity', GET

    class OpenApi(BaseEnum):
        """
        :type OpenApi
        """
        getEventMetaList = '/metrics/getEventMetaList', POST
        getEventMetaById = '/metrics/getEventMetaById', POST
        delEventMetaById = '/metrics/delEventMetaById', POST
        editEventMeta = '/metrics/editEventMeta', POST
        getEventChannel = '/metrics/getEventChannel', GET
        getEventAttr = '/metrics/getEventAttr', POST



if __name__ == '__main__':
    print(URL.FormReport.pageFormReportDetail.url)
    print(URL.FormReport.pageFormReportDetail.method)
    print(BaseEnum.url)
    # print(URL.getFormReportDetail.url)
