import scrapy
import json
from qichezhijia.items import QichezhijiaItem
import jsonpath


class Qichezhijiano1Spider(scrapy.Spider):


    name = "qichezhijiaNo1"
    cat_data = []

    def __init__(self, *args, **kwargs):
        super(Qichezhijiano1Spider, self).__init__(*args, **kwargs)
        # 从命令行参数中获取seriesid
        self.seriesid = kwargs.get('seriesid', 6606)  # 默认值6606

    def start_requests(self):
        # 动态生成起始请求
        url = f"https://carif.api.autohome.com.cn/dealer/LoadDealerPrice.ashx?_callback=LoadDealerPrice&type=1&seriesid={self.seriesid}&city=500100"
        yield scrapy.Request(url=url, callback=self.parse)


    def parse(self, response):
        # 假设获取到了车辆的specid，然后组合进行请求数据
        #去掉请求api的前面返回成功字段
        json_start_index = response.text.find('(') + 1
        json_end_index = response.text.rfind(')')
        response_json = response.text[json_start_index:json_end_index]
        data_dict = json.loads(response_json)  

        specids = {}
        specids = jsonpath.jsonpath(data_dict, '$[*].item[*].SpecId')
        # 如果 spec_ids 的长度大于10，只取前10个,因为汽车之家的这个接口，限定了只能查询10个数据，也可以多次重复请求，兴趣的可以修改
        if len(specids) > 10:
            specids = specids[:10]

        """""
        specids = [
            64056, 67794, 65417, 64115, 64055, 64057, 61741, 65044, 67239, 65934
        ]  # 注意：67794 和 64115 只出现一次，因为集合中的元素是唯一的
        """""

        # 将集合转换为逗号分隔的字符串
        specids_str = ','.join(map(str, specids))
        # 构造 URL
        url = f'https://carif.api.autohome.com.cn/Car/v3/Param_ListBySpecIdList.ashx?speclist={specids_str}'
        yield scrapy.Request(
            url=url,
            meta={
                'specids_str': specids_str,
            },
            callback=self.parse_response
        )

    def parse_response(self, response):
        # 将响应体从字节解码为GB2312编码的字符串
        specids_str = response.meta['specids_str']



        body_unicode = response.body.decode('gb2312')
        cardata = json.loads(body_unicode)
        # 将字符串解析为JSON对象
        self.cat_data = cardata['result']['paramtypeitems']



        url = f'https://carif.api.autohome.com.cn/Car/v2/Config_ListBySpecIdList.ashx?speclist={specids_str}'
        yield scrapy.Request(url=url, callback=self.carConfig_response, meta={'is_first_done': True})

    def carConfig_response(self, response):
        # 将响应体从字节解码为GB2312编码的字符串
        body_unicode = response.body.decode('gb2312')
        cardata = json.loads(body_unicode)
        self.cat_data += cardata['result']['configtypeitems']
        data = {}
        data = self.cat_data

        data = self.empty_json_data(data)
        paramitems = jsonpath.jsonpath(data, '$[*].paramitems[*]')
        configitems = jsonpath.jsonpath(data, '$[*].configitems[*]')

        car_items = QichezhijiaItem()  # 实例化items
        car_items['paramitems'] = paramitems  # 逐个添加到items中
        car_items['configitems'] = configitems
        yield car_items  # 将items提交到管道中

    # 数据清洗代码，删除所为空的数据
    def value_is_not_empty(self, value):
        return value not in ['', None, {}, []]

    def empty_json_data(self, data):
        if isinstance(data, dict):
            temp_data = dict()
            for key, value in data.items():
                if self.value_is_not_empty(value):
                    new_value = self.empty_json_data(value)
                    if self.value_is_not_empty(new_value):
                        temp_data[key] = new_value
            return None if not temp_data else temp_data

        elif isinstance(data, list):
            temp_data = list()
            for value in data:
                if self.value_is_not_empty(value):
                    new_value = self.empty_json_data(value)
                    if self.value_is_not_empty(new_value):
                        temp_data.append(new_value)
            return None if not temp_data else temp_data

        elif self.value_is_not_empty(data):
            return data
