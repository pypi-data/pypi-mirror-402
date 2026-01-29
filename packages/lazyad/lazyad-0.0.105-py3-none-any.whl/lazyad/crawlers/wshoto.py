# 微盛，企业管家 https://platform.wshoto.com

from lazysdk import lazyrequests
from lazysdk import lazytime
import showlog
import copy


default_headers = {
        "Accept": "application/json, text/plain, */*",
        "Accept-Encoding": "gzip, deflate, zstd",
        "Accept-Language": "en-US,en;q=0.5",
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        "Host": "platform.wshoto.com",
        "Origin": "https://platform.wshoto.com",
        "Pragma": "no-cache",
        "Referer": "https://platform.wshoto.com/index/dashboard",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
        "TE": "trailers",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:139.0) Gecko/20100101 Firefox/139.0",
        "x-admin-header": "1",
        "x-clientType-header": "pc",
        "x-header-host": "platform.wshoto.com",
    }


def dashboard(
        authorization: str
):
    url = "https://platform.wshoto.com/bff/index/private/pc/dashboard?saMode=SECRET"
    headers = copy.deepcopy(default_headers)
    headers["Authorization"] = authorization
    return lazyrequests.lazy_requests(
        method="POST",
        url=url,
        headers=headers
    )


def material_package(
        authorization: str,
        search_package_name: str = ""
):
    """
    【内容中心】/【组合素材】/【配置素材合集】/查询
    :param authorization:
    :param search_package_name: 被查询的素材合集名称
    :return:
    """
    url = "https://platform.wshoto.com/bff/content/private/pc/material/package/packageQuery"
    headers = copy.deepcopy(default_headers)
    headers["Authorization"] = authorization
    data = {
        "pageSize": 1000,
        "pageIndex": 1,
        "searchPackageName": search_package_name,
        "isManager": 1,
        "isContainsNoUse": True,
        "isContainsStop": True,
        "businessType": 14,
        "isShowRecommend": True,
        "isScope": False
    }
    return lazyrequests.lazy_requests(
        method="POST",
        url=url,
        headers=headers,
        json=data
    )


def create_material_package(
        authorization: str,
        name: str
):
    """
    【内容中心】/【组合素材】/【配置素材合集】/【+添加素材合集】
    :param authorization:
    :param name: 素材合集名称
    :return: {"code":"00000","msg":"OK","data":{"id":"2000222213115036674"}}
    """
    url = "https://platform.wshoto.com/bff/content/private/pc/materialCategory/create"
    headers = copy.deepcopy(default_headers)
    headers["Authorization"] = authorization
    data = {
        "name": name,
        "businessType":14,
        "editStatus":0
    }
    return lazyrequests.lazy_requests(
        method="POST",
        url=url,
        headers=headers,
        json=data
    )


class WshotoCrawler:
    def __init__(
            self,
            authorization: str,
            headers: dict = None,
    ):
        if headers is None:
            headers = default_headers
        self.authorization = authorization
        self.headers = headers
        self.headers["Authorization"] = authorization

    def dashboard(
            self,
    ):
        url = "https://platform.wshoto.com/bff/index/private/pc/dashboard?saMode=SECRET"
        headers = copy.deepcopy(default_headers)
        headers["Authorization"] = self.authorization
        return lazyrequests.lazy_requests(
            method="POST",
            url=url,
            headers=headers
        )

    def upload_file(
            self,
            file_path: str,
    ):
        """
        上传文件
        :param file_path: 文件路径
        :return:
        """
        url = "https://platform.wshoto.com/bff/content/private/pc/file/upload"
        headers = copy.deepcopy(self.headers)

        # 以二进制模式打开图片文件
        files = {'file': open(file_path, 'rb')}
        return lazyrequests.lazy_requests(
            method="POST",
            url=url,
            headers=headers,
            files=files
        )

    def material_create(
            self,
            business_type,
            category_id: str = None,
            cover_image_url: str = None,
            is_package_child_temporary: bool = None,
            is_private = None,
            title: str = None,

            operation: int = None,

            summary: str = None,
            original_link: str = None,

            app_id: str = None,
            app_path: str = None,
            app_original_id: str = None,

            material_id_list:list = None,
            tag_id_list: list = None,
            visible_dept_ids: list = None,
            visible_user_ids: list = None,
            root_parent_id: str = None,
            is_temporary: bool = None,

    ):
        """
        添加一条素材
        :param business_type: 【必填】8:小程序，9:网页，"14":创建组合素材
        :param category_id: 默认是0，在发送页面创建的时候不存在
        :param cover_image_url: 封面图（已上传的图片链接）
        :param is_package_child_temporary: 默认为True，在临时创建的时候不存在
        :param is_private:
        :param title: 小程序标题/组合标题/网页标题

        :param operation: 默认值为1，在临时创建的时候不传入

        :param summary: 摘要 (business_type=9)
        :param original_link: 外链网页 (business_type=9)

        :param app_id: 小程序ID
        :param app_path: 小程序页面路径
        :param app_original_id: 小程序原始ID

        :param material_id_list: 所提交的素材的id列表[str](business_type=14)
        :param tag_id_list: (business_type=14)
        :param visible_dept_ids: (business_type=14)
        :param visible_user_ids: (business_type=14)
        :param root_parent_id: 素材合集id (business_type=14)
        :param is_temporary: 在发送页面创建的时候，要为True
        :return:
        """
        url = "https://platform.wshoto.com/bff/content/private/pc/material/create"
        headers = copy.deepcopy(self.headers)

        data = {
            "businessType": business_type,
            "title": title,  # 标题
        }
        if category_id is not None:
            data["categoryId"] = category_id
        if is_temporary is not None:
            data["isTemporary"] = is_temporary
        if operation is not None:
            data["operation"] = operation
        if is_package_child_temporary is not None:
            data["isPackageChildTemporary"] = is_package_child_temporary

        if business_type == 8:
            # 小程序
            data["coverImageUrl"] = cover_image_url
            # data["isPackageChildTemporary"] = is_package_child_temporary

            data["contentApp"] = {
                    "appId": app_id,  # 小程序ID
                    "appPath": app_path,  # 小程序页面路径
                    "appOriginalId": app_original_id  # 小程序原始ID
                }
            if is_private is None:
                data["isPrivate"] = 1
            else:
                data["isPrivate"] = is_private

        elif business_type == 9:
            # 网页，【已支持临时创建】
            data["contentLink"] = {"originalLink": original_link}
            data["coverImageUrl"] = cover_image_url
            data["summary"] = summary  # 摘要

            if is_private is None:
                data["isPrivate"] = True
            else:
                data["isPrivate"] = is_private

        elif str(business_type) == "14":
            # 创建素材组合，若只有一条内容，这条内容的标题和这条内容的标题一致，否则需要定义
            data["contentPackage"] = {
                "tagIdList":[],
                "visibleDeptIds":[],
                "visibleUserIds":[]
            }
            if material_id_list:
                data["contentPackage"]["materialIdList"] = material_id_list
            if tag_id_list:
                data["contentPackage"]["tagIdList"] = tag_id_list
            if visible_dept_ids:
                data["contentPackage"]["visibleDeptIds"] = visible_dept_ids
            if visible_user_ids:
                data["contentPackage"]["visibleUserIds"] = visible_user_ids
            data["rootParentId"] = str(root_parent_id)
            data["extensionMap"] = {
                "riskLevel": "R1",
                "sceneSwitch": 1,
                "sendEnable": 1,
                "browseEnable": 1
            }
            data["publishStatus"] = 0
            data["startTime"] = ""  # 有效期
            data["endTime"] = ""  # 有效期

        return lazyrequests.lazy_requests(
            method="POST",
            url=url,
            headers=headers,
            json=data
        )

    def get_tags(
            self,
            key_value: str = "",
    ):
        """
        获取标签信息
        :param key_value: 搜索值
        :return:
        """
        url = "https://platform.wshoto.com/bff/tag/private/pc/tag/getSelector"
        headers = copy.deepcopy(self.headers)

        data = {
            "target": "CUSTOMER_RELATION",
            "keyValue": key_value,
            "isToppingAuto": False,
            "businessTagRange": 4,
            "filterTagTypes": [],
            "scene": "customer-marketing-group-send-task-create-groups-business",
            "usage": "SEARCH",
            "platform": "",
            "upTenantFilterUpDownTag": True
        }
        return lazyrequests.lazy_requests(
            method="POST",
            url=url,
            headers=headers,
            json=data
        )

    def get_plan_send_qty(
            self,
            is_judge_exists: bool = None,
            template_type: int = 1,
            filter_type: str = None,
            is_all_customer: bool = False,
            send_range_condition_name: str = None,
            send_range_condition_data: dict = None,
    ):
        """
        获取计划发送人数
        返回案例：
            is_judge_exists=True 返回：{"code":"00000","msg":"OK","data":1}
            is_judge_exists=None 返回：{"code":"00000","msg":"OK","data":5875}
        :param send_range_condition_name:
        :param send_range_condition_data:
        :param is_judge_exists: True/None，前台接口是做了2次访问校验，第一次是True，第二次是None，应该是先检测了条件是否存在，再查询的数量，可以直接用None
        :param template_type: 【发送方式】/1:【员工一键发送】，4:【通知员工转发】
        :param filter_type:
            AllCustomer：【发送范围】/全部客户
            CorpSend2Customer:【员工一键发送】/【发送范围】/按条件筛选客户
            StaffSend2Customer:【通知员工转发】/【发送范围】/按条件筛选客户
        :param is_all_customer: 【发送范围】，【全部客户】：True，【其他】：False
        :return:
        """
        url = "https://platform.wshoto.com/bff/marketing/private/pc/groupmsg/task/getPlanSendQty"
        headers = copy.deepcopy(self.headers)

        data = {
            "sendRange":{
                "filterType": filter_type,
                "isAllCustomer": is_all_customer,
            },
            "templateType": template_type
        }
        if is_judge_exists is not None:
            data["isJudgeExists"] = is_judge_exists
        if send_range_condition_name and send_range_condition_data:
            data["sendRange"][send_range_condition_name] = send_range_condition_data
        return lazyrequests.lazy_requests(
            method="POST",
            url=url,
            headers=headers,
            json=data
        )

    def group_msg_task_add(
            self,
            attachments: list,
            template_name: str = None,
            template_type: int = 1,
            filter_type: str = None,
            is_all_customer: bool = False,
            allow_select: bool = False,
            send_time: str = None,
            end_time: str = None,
            remind_minutes: int = 30,
            include_tags_operator: int = 0,
            tag_list: list = None,
            delay_send: int = 1,

            manager_notice: int = 0,
            user_id_list: list = None

    ):
        """
        【客户营销】/【营销任务】/【群发客户】/【+新建群发客户】
        :param attachments: 发送内容
        例如：
            [
                {
                    "actChildType": None,  # 一般好像是 None
                    "contentKey": "",  # 创建的素材的 contentKey
                    "id": "2010017325491559490",  # 创建的素材的 id
                    "sendType": 2,  # 小程序是2，网页分2种，轨迹形式是1，普通形式是2，默认选2
                    "status": 0,  # 一般是0
                    "title": "🌟【萧凌】最新章节已送到！",  # 素材的 title
                    "type": 8,  # 素材创建时的 business_type

                    "combinationId": "2010025494745814529",  # 应该是预制素材的资料，临时素材没有
                    "packageConfigId": "2000237794375335553"  # 应该是预制素材的资料，临时素材没有
                }
            ]
        :param template_name: 任务名称
        :param template_type: 【发送方式】/1:【员工一键发送】，4:【通知员工转发】
        :param filter_type:
            AllCustomer：【发送范围】/全部客户
            CorpSend2Customer:【员工一键发送】/【发送范围】/按条件筛选客户
            StaffSend2Customer:【通知员工转发】/【发送范围】/按条件筛选客户

        :param is_all_customer: 【发送范围】，【全部客户】：True，【其他】：False
        :param allow_select: 【发送范围】/【员工可调整发送范围】，默认：False
        :param send_time: 【定时发送】/定时发送的时间，注意，需要小于结束时间，例如：2026-01-15 01:00:00，如果不是定时发送，可不传
        :param end_time: 【结束时间】，注意，需要大于定时发送时间，例如：2026-01-20 00:00:00
        :param remind_minutes: 【自动提醒】/任务结束前 多少分钟 提醒未执行任务的员工完成任务，默认值：30
        :param include_tags_operator: 【标签】0:不限，此时tagList=[]，1:满足任意一个标签，2:同时满足所选标签，3:无标签客户，此时tagList=[]
        :param tag_list: 【标签】所选标签列表，形如：
            [{
                "tagId": "etDkH9EAAA4MgGUFctYkZYd18jpfCELw",
                "wsTagId": "cp1462aa6766ac4b1d9421badfdab7c9d2",
                "tagName": "测试",
                "order": None,
                "createUserId": None,
                "createSource": None,
                "tagType": 1,  # 应该是固定值？
                "strategyId": None  # 应该是固定值？
            }]
        :param delay_send: 是否延迟发送，默认值为1；【立即发送】：0，【定时发送】：1
        :param manager_notice:【通知管理员】，0:不勾选，1:勾选，默认值：0
        :param user_id_list: 【发送范围】/【添加人】组织架构中的具体员工列表

        """
        url = "https://platform.wshoto.com/bff/marketing/private/pc/groupmsg/task/add"
        headers = copy.deepcopy(self.headers)

        if not template_name:
            template_name = f"[未定义名称]{lazytime.get_datetime()}"
        if not tag_list:
            tag_list = []
        if not user_id_list:
            user_id_list = []

        data = {
            "templateName": template_name,  # 任务名称
            "templateType": template_type,  # 【发送方式】/1:【员工一键发送】，4:【通知员工转发】
            "sendRangeCondition": {  # 发送范围
                "filterType": filter_type,  # StaffSend2Customer:【通知员工转发】/按条件筛选客户，AllCustomer：全部客户
                "allowSelect": allow_select,  # 员工可调整发送范围
                "isAllCustomer": is_all_customer,
            },
            "content":{"plainText": ""},  # 发送内容的文本部分【固定】
            "attachments": attachments,  # 发送的内容
            "delaySend": delay_send,  # 【立即发送】：0，【定时发送】：1
            "source": 1,  # 好像是固定值
            "bizNo": "",  # 好像是固定值
            "endTime": end_time,  # 结束时间，要大于发送时间
            "remindTimeConfig": {
                "timeConfigList": [
                    {"unit": "MINUTES", "value": remind_minutes}
                ]
            },  # 【自动提醒】/任务结束前 多少分钟 提醒未执行任务的员工完成任务，默认值：30
            "managerNotice": manager_notice  # 通知管理员
        }
        if delay_send == 1:
            data["sendTime"] = send_time  # 定时发送时间

        if filter_type == "AllCustomer":
            # 【发送范围】/全部客户
            get_plan_send_qty_res = self.get_plan_send_qty(
                template_type=template_type,
                filter_type=filter_type,
                is_all_customer=is_all_customer
            )
            plan_send_qty = get_plan_send_qty_res["data"]

        elif filter_type == "CorpSend2Customer":
            # 【员工一键发送】/【发送范围】/按条件筛选客户
            send_range_condition_name = "corpSend2CustomerCondition"
            send_range_condition_data = {
                    "addUserRange": {
                        "userIdList": user_id_list,  # 组织架构中的具体员工列表
                        "deptIdList": [],  # 组织架构中的部门列表
                        "userTagList": []
                    },   # 【发送范围】/【添加人】
                    "addTimeRange": {
                        "startTime": "",
                        "endTime": ""
                    },  # 【发送范围】/【添加时间】
                    "includeTags": {
                        "operator": include_tags_operator,  # 1:满足任意一个标签，2:同时满足所选标签，3:无标签客户，此时tagList=[]
                        "tagList": tag_list
                    },  # 【发送范围】/标签，多个标签：测试/幽灵文楼/落枫文楼，可以搜索得到

                    "excludeTags": {
                        "operator": 0,
                        "tagList": []
                    },  # 剔除标签

                    "location": [],  # 【发送范围】/【更多筛选】/所在区域
                    "chatList": [],  # 【发送范围】/【更多筛选】/所在群聊
                    "sex": "ALL",  # 【发送范围】/【更多筛选】/客户性别
                    "ageRange": "",  # 【发送范围】/【更多筛选】/客户年龄
                    "remarkKeyWords": [],  # 【发送范围】/【更多筛选】/备注名关键词
                    "descriptionKeyWords": []  # 【发送范围】/【更多筛选】/描述关键词
                }
            data["sendRangeCondition"][send_range_condition_name] = send_range_condition_data
            get_plan_send_qty_res = self.get_plan_send_qty(
                template_type=template_type,
                filter_type=filter_type,
                is_all_customer=is_all_customer,
                send_range_condition_name=send_range_condition_name,
                send_range_condition_data=send_range_condition_data
            )
            plan_send_qty = get_plan_send_qty_res["data"]

        elif filter_type == "StaffSend2Customer":
            # 【通知员工转发】/【发送范围】/按条件筛选客户
            showlog.warning("暂不支持：【通知员工转发】/【发送范围】/按条件筛选客户")
            plan_send_qty = None
            return None

        data["planSendQty"] = plan_send_qty  # 计划发送人数
        return lazyrequests.lazy_requests(
            method="POST",
            url=url,
            headers=headers,
            json=data
        )

    def material_package(
            self,
            search_package_name: str = None,
            page: int = 1,
            page_size: int = 1000,
            business_type: int = 14,
            is_manager: int = None,
            isContainsNoUse:bool = None,
            isContainsStop:bool = None,
            isShowRecommend:bool = None,
            isScope:bool = False,
    ):
        """
        【内容中心】/【组合素材】/【配置素材合集】/查询
        :param search_package_name: 被查询的素材合集名称
        :return:
        """
        url = "https://platform.wshoto.com/bff/content/private/pc/material/package/packageQuery"
        headers = copy.deepcopy(default_headers)
        headers["Authorization"] = self.authorization
        data = {
            "pageSize": page_size,
            "pageIndex": page,
            "businessType": business_type,
            "isScope": isScope,
        }
        if search_package_name:
            data["searchPackageName"] = search_package_name
        if is_manager is not None:
            data["isManager"] = is_manager
        if isContainsNoUse is not None:
            data["isContainsNoUse"] = isContainsNoUse
        if isContainsStop is not None:
            data["isContainsStop"] = isContainsStop
        if isShowRecommend is not None:
            data["isShowRecommend"] = isShowRecommend
        return lazyrequests.lazy_requests(
            method="POST",
            url=url,
            headers=headers,
            json=data
        )

    def material_category(
            self,
            parent_id: str = "",
            business_type: int = 14,
            isScope:bool = False,
            isEntrance:bool = True,
            isIgnoreDefault:bool = False,
    ):
        """
        【内容中心】/【组合素材】/【配置素材合集】/【素材分类】/查询
        :param parent_id: 上级的id
        :return:
        """
        url = "https://platform.wshoto.com/bff/content/private/pc/materialCategory/query"
        headers = copy.deepcopy(default_headers)
        headers["Authorization"] = self.authorization
        data = {
            "businessType": business_type,
            "isIgnoreDefault":isIgnoreDefault,
            "isEntrance":isEntrance,
            "parentId":parent_id,
            "isScope":isScope
        }
        return lazyrequests.lazy_requests(
            method="POST",
            url=url,
            headers=headers,
            json=data
        )
