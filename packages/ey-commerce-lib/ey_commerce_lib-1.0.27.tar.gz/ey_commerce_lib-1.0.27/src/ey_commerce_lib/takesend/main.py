from httpx import AsyncClient, Timeout

from ey_commerce_lib.takesend.config import LOGIN_HEADERS, EDIT_HEADERS, LIST_HEADS
from ey_commerce_lib.takesend.parser.order import get_order_page, get_order_track_number_list


class TakeSendClient(object):

    def __init__(self, username: str, password: str):
        timeout = Timeout(connect=60.0, read=60.0, write=60.0, pool=30.0)
        self.__async_client = AsyncClient(
            base_url="http://k5.takesend.com:8180",
            timeout=timeout,
            verify=False
        )
        self.__username = username
        self.__password = password

    async def login(self):
        """
        自动登录
        :return:
        """
        # 访问首页
        await self.__async_client.get("/c_index.jsp")
        # 登录
        params = {
            'action': 'logon'
        }
        data = {
            'userid': self.__username,
            'password': self.__password
        }
        # 请求登录接口
        await self.__async_client.post(".//client/Logon", params=params, data=data, headers=LOGIN_HEADERS)

    async def client_cc_order(self, excel_data: list | str):
        """
        修改泰嘉产品上传重量数据
        :param excel_data:
        :return:
        """

        params = {
            'action': 'updateDweight',
        }
        data = {
            'excel[]': excel_data,
        }

        response = await self.__async_client.post('/Client/CCOrder', params=params, data=data, headers=EDIT_HEADERS)
        return response.json()

    async def client_cc_order_list_by_pre_date(self, pageNum: int, pageSize: int, begeditdate: str, endeditdate: str):
        """
        泰嘉已预报根据制单日期查询全部订单
        :param pageNum:
        :param pageSize:
        :param begeditdate: 制单日期开始
        :param endeditdate: 制单日期结束
        :return:
        """

        # 访问首页刷新token
        await self.__async_client.get('/client/Logon?action=initMenu')
        params = {
            'action': 'list',
        }
        data = {
            'flag': '3',
            'pageNum1': '1',
            'numPerPage': '200',
            'orderField': '1',
            'orderDirection': 'asc',
            'corpbillid': '',
            'channelid': '',
            'orgLookup.country': '',
            'orgLookup.chinese': '',
            'printnum': '',
            'ordertype': 'CORDER',
            'buyerid': '',
            'mbflag': '',
            'houseid': '',
            'begeditdate': '2025-10-24 00:00:00',
            'endeditdate': '2025-10-24 23:50:50',
        }
        response = await self.__async_client.post('/Client/CCOrder', params=params, data=data)
        return response.text

    async def list_track_number_client_cc_order_list_by_pre_date(self, begeditdate: str, endeditdate: str):
        """
        泰嘉已预报根据制单日期查询全部订单
        :param begeditdate:
        :param endeditdate:
        :return:
        """
        # 遍历页码
        page_info = get_order_page(
            await self.client_cc_order_list_by_pre_date(pageNum=1, pageSize=200, begeditdate=begeditdate,
                                                        endeditdate=endeditdate))
        total = page_info['total']
        # 计算总页数
        total_page = total // 200 + 1
        track_number_list = []
        for page in range(1, total_page + 1):
            # 获取订单列表
            page_html = await self.client_cc_order_list_by_pre_date(pageNum=page, pageSize=200, begeditdate=begeditdate,
                                                                    endeditdate=endeditdate)
            # 解析
            track_number_list.extend(get_order_track_number_list(page_html))
        return track_number_list

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.__async_client.aclose()
