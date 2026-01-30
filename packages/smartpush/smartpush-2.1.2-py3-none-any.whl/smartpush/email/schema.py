import json
import uuid
from enum import unique, Enum


def generate_UUID(length=None):
    _uuid = str(uuid.uuid4())
    if length:
        return _uuid.replace('-', '')[:length]
    else:
        return _uuid


class BlockType(Enum):
    Section = 1
    Block = 0

    @staticmethod
    def getType(block_type):
        if block_type == BlockType.Section.name:
            return BlockType.Section.value
        else:
            return BlockType.Block.value


@unique
class BlockSchema(Enum):
    Logo = {
        "id": generate_UUID(9),
        "universalId": None,
        "universalName": None,
        "type": "Logo",
        "props": {
            "width": "120",
            "height": "120",
            "imgRatio": 1,
            "src": "https://cdn.smartpushedm.com/frontend/smart-push/staging/1741054956275/1758595834300_74d62ae6.png?width=120&height=120",
            "href": "https://smartpush4.myshoplinestg.com",
            "align": "center",
            "containerBackgroundColor": "transparent",
            "paddingLeft": "20px",
            "paddingRight": "20px",
            "paddingTop": "20px",
            "paddingBottom": "20px",
            "paddingCondition": True
            ,
            "segmentTypeConfig": 1
        },
        "children": []
    }
    Link = {
        "id": generate_UUID(9),
        "universalId": None,
        "universalName": None,
        "type": "Navigation",
        "props": {
            "moduleList": [
                {
                    "title": "LINK",
                    "link": "",
                    "linkId": "d5c9ace8-ae39-42f3-ab64-3016da91a4ef"
                },
                {
                    "title": "LINK",
                    "link": "",
                    "linkId": "fb00e389-06bf-4060-b63f-8acbbb906670"
                },
                {
                    "title": "LINK",
                    "link": "",
                    "linkId": "ecd48104-fb52-460e-b2a1-b386ab18d10e"
                }
            ],
            "color": "#242833",
            "fontSize": "14px",
            "fontFamily": "arial,helvetica,sans-serif,Arial, Helvetica, sans-serif",
            "segmentLineColor": "#242833",
            "segmentLineStyle": "solid",
            "segmentLineWeight": "1px",
            "paddingLeft": "10px",
            "paddingRight": "10px",
            "justifyContent": "center",
            "paddingTop": "10px",
            "paddingBottom": "10px",
            "paddingCondition": True
            ,
            "containerBackgroundColor": "transparent"
        },
        "children": []
    }
    Image = {
        "id": generate_UUID(9),
        "universalId": None,
        "universalName": None,
        "type": "Image",
        "props": {
            "width": "600px",
            "height": "300px",
            "src": "",
            "href": "[[shopURL]]",
            "align": "left",
            "containerBackgroundColor": "transparent",
            "paddingLeft": "0px",
            "paddingRight": "0px",
            "paddingTop": "0px",
            "paddingBottom": "0px",
            "paddingCondition": True
        },
        "children": []
    }
    ImageSet = {
        "id": generate_UUID(9),
        "universalId": None,
        "universalName": None,
        "type": "ImageSet",
        "props": {
            "list": [
                {
                    "src": "",
                    "width": "300px",
                    "height": "180px",
                    "imgRatio": 0.51,
                    "paddingLeft": "",
                    "paddingRight": "",
                    "paddingTop": "0px",
                    "paddingBottom": "0px",
                    "href": "[[shopURL]]",
                    "selected": False
                },
                {
                    "src": "",
                    "width": "300px",
                    "height": "180px",
                    "imgRatio": 0.51,
                    "paddingLeft": "",
                    "paddingRight": "",
                    "paddingTop": "0px",
                    "paddingBottom": "0px",
                    "href": "[[shopURL]]",
                    "selected": False
                }
            ],
            "layout": "horizontal",
            "layoutPadding": "5px",
            "containerBackgroundColor": "#ffffff",
            "paddingLeft": "5px",
            "paddingRight": "5px",
            "paddingTop": "10px",
            "paddingBottom": "10px",
            "paddingCondition": True
            ,
            "mobileSwitch": [],
            "direction": "rtl"
        },
        "children": []
    }
    Video = {"id": generate_UUID(9),
             "universalId": None,
             "universalName": None,
             "type": "Video",
             "props": {"iconColor": "#ffffff", "iconStyle": 1, "videoImageType": "auto", "videoHref": "",
                       "width": "600px",
                       "height": "300px", "format": "png", "src": "", "loading": False, "showError": False,
                       "originUrl": {"height": 0, "width": 0, "url": ""}, "align": "left",
                       "containerBackgroundColor": "transparent", "paddingLeft": "10px", "paddingRight": "10px",
                       "paddingTop": "10px", "paddingBottom": "10px", "paddingCondition": True
                       }, "children": []}
    TimerCountdown = {"id": generate_UUID(9),
                      "universalId": None,
                      "universalName": None,
                      "type": "TimerCountdown",
                      "props": {"gifColor": "#FA7124", "gifLoading": False, "selected": False, "day": 2, "hour": 0,
                                "minute": 0, "width": "600px", "height": "156px",
                                "src": "https://client-test.smartpushedm.com/sp-media-support/gif/0894dd7053af4b189f665dd2ddb54606.gif?v=1762701524060",
                                "imgRatio": 0.26, "timerType": 1, "endTime": "1762874323452",
                                "timerZone": "America/New_York", "expire": False,
                                "expireText": "The current activity.py has expired", "duration": "", "layout": 1,
                                "numberFontFamily": "Arial Bold", "numberSize": "40px", "numberColor": "#FFFFFF",
                                "timeUnitFontFamily": "Arial Bold", "timeUnitSize": "16px", "timeUnitColor": "#FFFFFF",
                                "align": "center", "paddingLeft": "10px", "paddingRight": "10px", "paddingTop": "10px",
                                "paddingBottom": "10px", "paddingCondition": True
                          ,
                                "containerBackgroundColor": "transparent", "gifId": "246f5df56e674676add060956fac7b3f"},
                      "children": []}
    Commodity = {"id": generate_UUID(9),
                 "universalId": None,
                 "universalName": None,
                 "type": "Commodity",
                 "props": {"source": None, "limit": 6, "justifyContent": "center", "imgRatio": "3:4",
                           "imgFillType": "cover", "isProductTitle": True
                     ,
                           "isProductActionButton": True
                     , "isSpecialOffer": True
                     ,
                           "SpecialOfferFontSize": "20px",
                           "SpecialOfferFontFamily": "arial,helvetica,sans-serif,Arial, Helvetica, sans-serif",
                           "SpecialOfferColor": "#000000", "OriginalPriceFontSize": "16px",
                           "OriginalPriceFontFamily": "arial,helvetica,sans-serif,Arial, Helvetica, sans-serif",
                           "OriginalPriceColor": "#000000", "isOriginalPrice": True
                     ,
                           "ProductTitleColor": "#000000", "showLineRule": 0, "moduleList": [],
                           "layout": "TwoHorizontalColumns", "productEle": [1, 3],
                           "productActionButton": 2, "content": "BUY NOW", "color": "#ffffff",
                           "backgroundColor": "#000000", "btnImgSrc": 1,
                           "containerBackgroundColor": "transparent", "paddingLeft": "10px",
                           "paddingRight": "10px", "paddingTop": "10px", "paddingBottom": "10px",
                           "buttonFontSize": "16px",
                           "buttonFontFamily": "arial,helvetica,sans-serif,Arial, Helvetica, sans-serif",
                           "borderRadius": "0px", "buttonBorderStyle": "none", "borderWidth": "1px",
                           "borderColor": "#000000", "mobileSwitch": [], "hotspotIds": [],
                           "currency": 1, "currencyFormat": True
                     , "currencyDecimalPoint": 2,
                           "segmentTypeConfig": 1}, "children": []}
    Discount = {"id": generate_UUID(9),
                "universalId": None,
                "universalName": None,
                "type": "Discount",
                "props": {"discountTermsFontFamily_SHOPIFY": "arial,helvetica,sans-serif,Arial, Helvetica, sans-serif",
                          "discountTermsFontFamily_EC1": "arial,helvetica,sans-serif,Arial, Helvetica, sans-serif",
                          "discountCodeSize_SHOPIFY": "16px", "discountCodeSize_EC1": "20px",
                          "discountCodeColor_EC1": "#E02020", "discountCodeColor_SHOPIFY": "#E02020",
                          "discountCodeBackgroundColor": "#FFFFFF", "discountCodeBackgroundColor_SHOPIFY": "#FFFFFF",
                          "discountCodeBackgroundColor_EC1": "#FFFFFF", "discountCodeBorderStyle": "none",
                          "discountCodeBorderStyle_SHOPIFY": "none", "discountCodeBorderStyle_EC1": "none",
                          "discountCodeBorderWidth": "1px", "discountCodeBorderWidth_SHOPIFY": "1px",
                          "discountCodeBorderWidth_EC1": "1px", "discountCodeBorderColor": "#000000",
                          "discountCodeBorderColor_SHOPIFY": "#000000", "discountCodeBorderColor_EC1": "#000000",
                          "discountCodeContent_EC1": None, "discountShowList_EVENT": [3],
                          "effectiveTimeColor_SHOPIFY": "#7A8499",
                          "btnFontFamily_SHOPIFY": "arial,helvetica,sans-serif,Arial, Helvetica, sans-serif",
                          "btnTextSize_SHOPIFY": "16px", "btnTextColor_SHOPIFY": "#FFFFFF",
                          "btnBacdgroundColor_SHOPIFY": "#000000", "buttonRadius_SHOPIFY": "0px",
                          "buttonBorderStyle_SHOPIFY": "none", "borderWidth_SHOPIFY": "1px",
                          "borderColor_SHOPIFY": "#000000",
                          "btnFontFamily_EC1": "arial,helvetica,sans-serif,Arial, Helvetica, sans-serif",
                          "btnTextSize_EC1": "16px", "btnTextColor_EC1": "#FFFFFF", "btnBacdgroundColor_EC1": "#000000",
                          "buttonRadius_EC1": "0px", "buttonBorderStyle_EC1": "none", "borderWidth_EC1": "1px",
                          "borderColor_EC1": "#000000", "insideBackgroundColor_SHOPIFY": "#FFFFFF",
                          "containerBackgroundColor_EC1": "transparent", "paddingLeft_EC1": "10px",
                          "paddingRight_EC1": "10px", "paddingTop_EC1": "10px", "paddingBottom_EC1": "10px",
                          "paddingCondition_EC1": True
                    , "containerBackgroundColor_SHOPIFY": "transparent",
                          "paddingLeft_SHOPIFY": "10px", "paddingRight_SHOPIFY": "10px", "paddingTop_SHOPIFY": "10px",
                          "paddingBottom_SHOPIFY": "10px", "paddingCondition_SHOPIFY": True
                    ,
                          "discountType_SHOPIFY": "percentage", "discountTypePercentageValue_SHOPIFY": None,
                          "discountTypeFixedAmountValue_SHOPIFY": None, "discountType_EC2": "percentage",
                          "discountTypePercentageValue": None, "discountTypeFixedAmountValue": None,
                          "preferentialConditionsType_SHOPIFY": 0, "preferentialConditionsType": 0,
                          "preferentialConditionsSpecifiedAmount_SHOPIFY": None,
                          "preferentialConditionsSpecifiedQuantity_SHOPIFY": None,
                          "preferentialConditionsSpecifiedAmount": None,
                          "preferentialConditionsSpecifiedQuantity": None,
                          "discountUsageRestrictions_SHOPIFY": [], "discountUsageRestrictions": [],
                          "discountTotalUsageLimit_SHOPIFY": None, "discountTotalUsageLimit": None,
                          "discountUserUsageLimit": None, "discountUserUsageLimit_SHOPIFY": 1,
                          "effectiveTimeType_SHOPIFY": 0, "effectiveTimeType": 0, "effectiveTimeDay_SHOPIFY": None,
                          "effectiveTimeDay": None, "effectiveTimeFormat_SHOPIFY": "mm/dd/yyyy",
                          "effectiveTimeFormat": "mm/dd/yyyy", "couponCodeType": 0, "couponCodeType_SHOPIFY": 0,
                          "discountCode": "",
                          "discountCodeSource": {"valueType": "string", "startsAt": "", "code": "", "customerGets": [],
                                                 "endsAt": "", "title": ""},
                          "insideTitle": "<p style=\"font-family: arial,helvetica,sans-serif,Arial, Helvetica, sans-serif; font-size: 24px; text-align: center;\" class=\"sp-font-24\"><strong>Welcome</strong></p><p\n    style=\"font-family: arial,helvetica,sans-serif,Arial, Helvetica, sans-serif; text-align: center;\" class=\"sp-font-18\">Thanks for your joining! To express our gratitude, please receive this coupon as a gift, enjoy your stay here!</p>",
                          "discountCodeColor": "#E02020", "discountCodeSize": "16px",
                          "discountTermsFontFamily": "arial,helvetica,sans-serif,Arial, Helvetica, sans-serif",
                          "btnTextSize": "16px", "btnTextColor": "#FFFFFF",
                          "btnFontFamily": "arial,helvetica,sans-serif,Arial, Helvetica, sans-serif",
                          "buttonRadius": "0px",
                          "btnBacdgroundColor": "#000000", "buttonBorderStyle": "none", "borderWidth": "1px",
                          "borderColor": "#000000", "displayEffectiveTime": True
                    , "effectiveTimeColor": "#7A8499",
                          "insideBackgroundWay": 1, "insideBackgroundColor": "#FFFFFF", "insideBackgroundIcon": "",
                          "outsideDisplay": "POPUP",
                          "outsideTitle": "<p><span style=\"font-family: arial,helvetica,sans-serif,Arial, Helvetica, sans-serif; font-size: 18px;\" class=\"sp-font-18\">Don't forget to use your coupon code</span></p>",
                          "outsideBtnTextContent": "Copy", "outsideBackgroundBar": 1, "outsideBackgroundPop": 11,
                          "outsideBackgroundColorBar": "#FFCA3D", "outsideBackgroundColorPop": "#FFCA3D",
                          "outsideBackgroundIconPop": "", "outsideBorderStyle": "none", "outsideBorderRadius": "0px",
                          "outsideBtnBackgroundColor": "#000000",
                          "outsideFontFamily": "arial,helvetica,sans-serif,Arial, Helvetica, sans-serif",
                          "outsideBtnTextSize": "16px", "outsideBtnTextColor": "#FFFFFF", "outsideBorderWidth": "1px",
                          "outsideBorderColor": "#000000", "discountTab": 0, "paddingLeft": "10px",
                          "paddingRight": "10px",
                          "paddingTop": "10px", "paddingBottom": "10px", "paddingCondition": True
                    ,
                          "containerBackgroundColor": "transparent", "platform": "EC2", "isShowDiscountButton_EC2": True
                    ,
                          "isShowDiscountButton_CUSTOM": True
                    , "isShowDiscountButton_EC1": True
                    ,
                          "isShowDiscountButton_SHOPIFY": True
                    , "discountConditionType": "discount_condition",
                          "displayEffectiveTimeType": "mm/dd/yyyy", "displayEffectiveTimeType_code": "mm/dd/yyyy",
                          "displayEffectiveTime_code": True
                    , "btnLinkType": "custom", "href": "",
                          "btnText_EC2": "Use discount now", "btnText_SHOPIFY": "Use discount now",
                          "btnText_CUSTOM": "Use discount now", "btnText_EC1": "Use discount now", "btnUrl_EC2": "",
                          "btnUrl_SHOPIFY": "", "btnUrl_CUSTOM": "", "btnUrl_EC1": "", "isShowPreviewForm": False},
                "children": []}
    TextSet = {"id": generate_UUID(9),
               "universalId": None,
               "universalName": None,
               "type": "TextSet", "props": {"list": [{
            "content": "<p style=\"font-family: arial,helvetica,sans-serif,Arial, Helvetica, sans-serif\">在此处输入文本，支持按需调整字体大小、行距、对齐方式等样式</p>",
            "paddingLeft": "10px", "paddingRight": "10px", "paddingTop": "0px",
            "paddingBottom": "0px", "borderStyle": "none",
            "borderColor": "#000", "borderWidth": "1px"}],
            "containerBackgroundColor": "transparent", "paddingLeft": "10px",
            "paddingRight": "10px", "paddingTop": "10px", "paddingBottom": "10px",
            "paddingCondition": True
        }, "children": []}
    ImageText = {"id": generate_UUID(9),
                 "universalId": None,
                 "universalName": None,
                 "type": "ImageText", "props": {"list": [{"src": "", "width": "290", "height": "150", "imgRatio": 0.51,
                                                          "content": "<p style=\"font-family: arial,helvetica,sans-serif,Arial, Helvetica, sans-serif\">在此处输入文本，支持按需调整字体大小、行距、对齐方式等样式</p>",
                                                          "layout": "rightText", "borderWidth": "1px",
                                                          "borderColor": "#000000", "borderStyle": "none",
                                                          "href": "[[shopURL]]", "selected": False}],
                                                "containerBackgroundColor": "transparent", "paddingLeft": "10px",
                                                "paddingRight": "10px", "paddingTop": "10px", "paddingBottom": "10px",
                                                "paddingCondition": True
            , "layoutItem": "rightText", "segmentTypeConfig": 1}, "children": []}
    Button = {"id": generate_UUID(9),
              "universalId": None,
              "universalName": None,
              "type": "Button",
              "props": {"content": "Button", "color": "#ffffff", "fontSize": "18px", "fontWeight": 500,
                        "fontFamily": "arial,helvetica,sans-serif,Arial, Helvetica, sans-serif",
                        "href": "[[shopURL]]", "backgroundColor": "#000000", "width": "20%",
                        "borderRadius": "0px", "borderStyle": "none", "borderColor": "#000000",
                        "borderWidth": "1px", "align": "center",
                        "containerBackgroundColor": "transparent", "paddingLeft": "10px",
                        "paddingRight": "10px", "paddingTop": "10px", "paddingBottom": "10px",
                        "paddingCondition": True
                        }, "children": []}
    Divider = {"id": generate_UUID(9),
               "universalId": None,
               "universalName": None,
               "type": "Divider",
               "props": {"borderColor": "#000000", "borderStyle": "solid", "borderWidth": "1px", "paddingLeft": "20px",
                         "paddingRight": "20px", "paddingTop": "20px", "paddingBottom": "20px", "paddingCondition": True
                         }, "children": []}
    Social = {"id": generate_UUID(9),
              "universalId": None,
              "universalName": None,
              "type": "Social", "props": {
            "list": [{"name": "facebook-noshare", "iconSize": "36px", "src": "", "iconStyle": 1, "href": ""},
                     {"name": "instagram", "iconSize": "36px", "src": "", "iconStyle": 1, "href": ""},
                     {"name": "web", "iconSize": "36px", "src": "", "iconStyle": 1, "href": ""}],
            "containerBackgroundColor": "transparent", "iconStyle": 1}, "children": []}
    HTMLCode = {"id": generate_UUID(9),
                "universalId": None,
                "universalName": None,
                "type": "HTMLCode", "props": {"list": [
            {"content": "使用你自定义的代码段", "paddingLeft": "0px", "paddingRight": "0px", "paddingTop": "0px",
             "paddingBottom": "0px", "borderStyle": "none", "borderColor": "#ffffff", "borderWidth": "1px"}],
            "containerBackgroundColor": "TRANSPARENT", "paddingLeft": "0px",
            "paddingRight": "0px", "paddingTop": "0px", "paddingBottom": "0px",
            "paddingCondition": True
        }, "children": []}
    Section = {
        "id": generate_UUID(9),
        "universalId": None,
        "universalName": None,
        "type": "Section",
        "props": {
            "backgroundColor": "#f1e6e6",
            "borderLeft": "1px none #ffffff",
            "borderRight": "1px none #ffffff",
            "borderTop": "1px none #ffffff",
            "borderBottom": "1px none #ffffff",
            "paddingTop": "0px",
            "paddingBottom": "0px",
            "paddingLeft": "0px",
            "paddingRight": "0px",
            "cols": [
                12
            ]
        },
        "children": [
            {
                "id": "8cab9aa48",
                "type": "Column",
                "props": {},
                "children": [
                    {
                        "id": "a398fa9db",
                        "universalId": "3a8b79e8-b400-43d4-8d4c-c70969284a24",
                        "universalName": "Auto-Logo-2025-11-14 00:33:28",
                        "type": "Logo",
                        "props": {
                            "width": "120",
                            "height": "120",
                            "imgRatio": 1,
                            "src": "https://cdn.smartpushedm.com/frontend/smart-push/staging/1741054956275/1758595834300_74d62ae6.png?width=120&height=120",
                            "href": "https://smartpush4.myshoplinestg.com",
                            "align": "center",
                            "containerBackgroundColor": "transparent",
                            "paddingLeft": "20px",
                            "paddingRight": "20px",
                            "paddingTop": "20px",
                            "paddingBottom": "20px",
                            "paddingCondition": True,
                            "segmentTypeConfig": 1
                        },
                        "children": []
                    }
                ]
            }
        ]
    }
    Subscribe = {
        "id": generate_UUID(9),
        "type": "Subscribe",
        "props": {
            "content": "<div  class='sp-font-12'><p style=\"text-align: center; \" data-mce-style=\"text-align: "
                       "center; \"><em><span class='sp-font-12' style=\"font-size: 12px; color: rgb(122, 132, "
                       "153);\" data-mce-style=\"font-size: 12px; color: #7a8499;\">Please add us to your email "
                       "contacts list to receive exclusive recommendations!</span></em></p><p style=\"text-align: "
                       "center; \" data-mce-style=\"text-align: center; \"><em><span class='sp-font-12' "
                       "style=\"font-size: 12px; color: rgb(122, 132, 153);\" data-mce-style=\"font-size: 12px; "
                       "color: #7a8499;\">You are receiving this message from [[shopName]] because you have signed up "
                       "for subscriptions to receive information about products, services, "
                       "and campaigns.</span></em></p></div><div class=\"sp-font-12\" style=\"color: rgb(122, 132, "
                       "153); font-family: arial, helvetica, sans-serif, Arial, Helvetica, sans-serif;  font-size: "
                       "12px; text-align: center; margin-top: 12px;padding-left: 10px; padding-right: 10px; "
                       "padding-bottom: 20px;\"><div>Questions? Please <span "
                       "style=color:#479EEF;text-decoration:underline>contact us</span>, we are glad to "
                       "help.</div><div>If you don't want to receive our message, just <span "
                       "style=color:#479EEF;text-decoration:underline>click here</span> to cancel the "
                       "subscription.</div></div><div class=\"sp-font-12\" style=\"color: rgb(122, 132, "
                       "153); font-size: 12px; text-align: center; font-style: oblique;\">Questions? Please <a href=["
                       "[customerEmail]]  style=\"color:#479EEF;text-decoration:underline\" "
                       "rel=\"noreferrer\">contact us</a>, we are glad to help.</div><div class=\"sp-font-12\" "
                       "style=\"color: rgb(122, 132, 153); font-size: 12px; text-align: center; font-style: "
                       "oblique;\">If you don't want to receive our message, just <a href=[[unsubscribe.url]] "
                       "target=\"_blank\" style=\"color:#479EEF;text-decoration:underline\" rel=\"noreferrer\">click "
                       "here</a> to cancel the subscription.</div>",
            "containerBackgroundColor": "transparent"
        },
        "children": []
    }
    Header = {
        "id": generate_UUID(9),
        "type": "Header",
        "props": {
            "backgroundColor": "#ffffff",
            "borderLeft": "1px none #ffffff",
            "borderRight": "1px none #ffffff",
            "borderTop": "1px none #ffffff",
            "borderBottom": "1px none #ffffff",
            "paddingTop": "0px",
            "paddingBottom": "0px",
            "paddingLeft": "0px",
            "paddingRight": "0px",
            "cols": [
                12
            ]
        },
        "children": [
            {
                "id": "98d909a48",
                "type": "Column",
                "props": {},
                "children": [
                    {
                        "id": "8298cb99a",
                        "type": "TextSet",
                        "props": {
                            "list": [
                                {
                                    "borderWidth": "1px",
                                    "borderStyle": "none",
                                    "content": "<p style=\"line-height: 3; text-align: right;\"><span style=\"color: #000000; font-size: 12px; font-family: arial, sans-serif;\"><a style=\"color: #000000;\" href=\"${viewInWebApiUrl}\">Can't see the email? Please <span style=\"color: #3598db;\">click here</span></a></span></p>",
                                    "paddingLeft": "10px",
                                    "paddingRight": "10px",
                                    "paddingTop": "0px",
                                    "paddingBottom": "0px",
                                    "borderColor": "#ffffff"
                                }
                            ],
                            "containerBackgroundColor": "transparent",
                            "paddingLeft": "10px",
                            "paddingRight": "10px",
                            "paddingTop": "10px",
                            "paddingBottom": "10px"
                        },
                        "children": []
                    }
                ]
            }
        ]
    }
    Footer = {
        "id": generate_UUID(9),
        "type": "Footer",
        "props": {
            "backgroundColor": "#ffffff",
            "borderLeft": "1px none #ffffff",
            "borderRight": "1px none #ffffff",
            "borderTop": "1px none #ffffff",
            "borderBottom": "1px none #ffffff",
            "paddingTop": "0px",
            "paddingBottom": "0px",
            "paddingLeft": "0px",
            "paddingRight": "0px",
            "cols": [
                12
            ]
        },
        "children": [
            {
                "id": "b3bcabad7",
                "type": "Column",
                "props": {},
                "children": [
                    Subscribe
                ]
            }
        ]
    }

    @staticmethod
    def genSection(block_list: list):
        """
            根据Block生成Section结构体
            :param block_list:
            :return:
            """
        section = BlockSchema.Section
        if section.value['children'][0]['type'] == 'Column':
            section.value['children'][0]['children'] = block_list
        return section

    @staticmethod
    def genSchemaAnalysis(schema):
        """
            递归遍历嵌套字典结构，提取所有层级的type和对应的id
            相同type的id将以列表形式汇总（按遍历顺序追加）

            Args:
                data: 嵌套字典/列表结构（支持单节点字典或children列表）

            Returns:
                dict: key为type值，value为id列表（即使只有一个id也保持列表格式）
                :param schema:
            """
        result = {}

        def recursive_parse(node):
            if isinstance(node, dict):
                if 'type' in node and 'id' in node:
                    type_val = node['type']
                    id_val = node['id']
                    result.setdefault(type_val, []).append(id_val)

                if 'children' in node and isinstance(node['children'], list):
                    for child in node['children']:
                        recursive_parse(child)
            elif isinstance(node, list):
                for item in node:
                    recursive_parse(item)

        recursive_parse(schema if isinstance(schema, dict) else schema.value)
        schemaAnalysis = {"schema": result}
        return json.dumps(schemaAnalysis)

    @staticmethod
    def genAllBlockSchema():
        """
        获取所有的BlockSchema
        :return:
        """
        temp_list = [i.value for i in BlockSchema if
                     i not in (BlockSchema.Section, BlockSchema.Footer, BlockSchema.Header)]
        return temp_list

    @staticmethod
    def genAllBlockSchemaList():
        """
        获取所有的BlockSchema
        :return:
        """
        temp_list = [i.name for i in BlockSchema if
                     i not in (BlockSchema.Section, BlockSchema.Footer, BlockSchema.Header)]
        return temp_list


if __name__ == '__main__':
    # print(BlockSchema.Footer.value)
    # print(genAllBlockSchemaList())
    # [BlockSchema.Logo, BlockSchema.Social]
    # [BlockSchema.Logo, BlockSchema.Link, BlockSchema.Image, BlockSchema.ImageSet, BlockSchema.Video,
    #  BlockSchema.TimerCountdown, BlockSchema.Commodity, BlockSchema.Discount, BlockSchema.TextSet,
    #  BlockSchema.ImageText,
    #  BlockSchema.Button, BlockSchema.Divider, BlockSchema.Social, BlockSchema.HTMLCode]

    print(BlockSchema.genSchemaAnalysis(BlockSchema.Section))
