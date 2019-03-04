# -*- coding: utf-8 -*-
from HouseWorld.items import HouseworldItem, ESFHouseItem
import scrapy
import re 


class FindhouseSpider(scrapy.Spider):
    name = 'findHouse'
    allowed_domains = ['fang.com']
    start_urls = ['https://www.fang.com/SoufunFamily.htm']

    def parse(self, response):
        trs = response.xpath("//div[@class='outCont']//tr")
        # 设置一个空值用于接收省份
        province = None
        for tr in trs:
            tds = tr.xpath(".//td[not(@class)]")
            province_td = tds[0]
            province_text = province_td.xpath(".//text()").extract_first()
            province_text = re.sub(r"\s", "", province_text)
            if province_text:
                province = province_text
            #不爬去海外的信息
            if province == '其它':
                continue
            city_td = tds[1]
            #　city链接列表
            city_links = city_td.xpath(".//a")
            for city_link in city_links: 
                city = city_link.xpath(".//text()").extract_first()
                #　城市的ＵＲＬ
                city_url = city_link.xpath(".//@href").extract_first()
                #　构建新房的ｕｒｌ链接
                url_module = city_url.split('//')
                scheme = url_module[0]
                domain = url_module[1]
                if 'bj' in domain:
                    newhouse_url = 'https://newhouse.fang.com/house/s/'
                    esf_url = 'https://esf.fang.com/'   
                else:
                    #　构建新房的ｕｒｌ链接
                    newhouse_url = scheme+'//'+"newhouse."+domain+"house/s/"
                    #　构建旧房的ｕｒｌ链接
                    esf_url = scheme+'//'+"esf."+domain
                yield scrapy.Request(url=newhouse_url,callback=self.parse_newhouse,meta={"info":(province,city)})
                yield scrapy.Request(url=esf_url,callback=self.parse_esf,meta={"info":(province,city)})
    def parse_newhouse(self,response):
        province,city = response.meta.get('info')
        lis = response.xpath("//div[contains(@class,'nl_con')]/ul/li")
        for li in lis:
            name = li.xpath(".//div[@class='nlcd_name']/a/text()").extract_first()
            if not name:
                continue
            name = name.strip()
            house_type_list = li.xpath(".//div[contains(@class,'house_type')]/a/text()").extract()
            house_type_list = list(map(lambda x :re.sub(r"\s","",x),house_type_list))
            rooms = list(filter(lambda x:x.endswith("居"),house_type_list))
            if not rooms:
                rooms = house_type_list            
            # import ipdb as pd ; pd.set_trace()
            area = "".join(li.xpath(".//div[contains(@class,'house_type')]/text()").extract())
            area =re.sub(r"\s|－|/", "", area)
            if not area:
                area = '暂无数据'
            # import ipdb as pd ; pd.set_trace()
            adress = li.xpath(".//div[@class='address']/a/@title").extract_first()
            district_text = "".join(li.xpath(".//div[@class='address']/a/text()").extract())
            if not district_text:
                continue
            else:
                district_text = district_text.strip()
                if district_text.find(']')>-1:
                    district = district_text.split(']')[1]
                    district = district.strip()
                else:
                    district = district_text
                district = district.strip()

            sale = li.xpath(".//div[contains(@class,'fangyuan')]/span/text()").extract_first()
            price = "".join(li.xpath(".//div[@class='nhouse_price']//text()").extract())
            price = re.sub(r"\s|广告", "", price)
            origin_url = li.xpath(".//div[@class='nlcd_name']/a/@href").extract_first()
            item = HouseworldItem(name=name,rooms=rooms,area=area,adress=adress,district=district,sale=sale,price=price,origin_url=origin_url,province=province)
            yield item
            # except Exception as e:
            #     # import ipdb as pd; pd.set_trace()
            #     print(e)
        next_url = response.xpath("//div[@class='page']//a[@class='next']/@href").extract_first()
        if next_url:
            yield scrapy.Request(url=response.urljoin(next_url),callback=self.parse_newhouse,meta={"info":(province,city)})

    def parse_esf(self,response):
        province,city = response.meta.get('info')
        dls = response.xpath("//div[@class='houseList']/dl")
        for dl in dls:
            item = ESFHouseItem(province=province,city=city)
            name = response.xpath(".//p[@class='mt10']/a/span/text()").extract_first()
            infos = dls.xpath(".//p[@class='mt12']/text()").extract()
            infos = list(map(lambda x:re.sub(r"\s","",x), infos))
            for info in infos:
                if "厅" in info:
                    item['rooms'] = info
                elif '层' in info:
                    item['floor'] = info
                elif '向' in info:
                    item['toward'] = info
                else:
                    item['year'] = info.replace("建筑年代","")
            item['adress'] = dl.xpath(".//p[@class='mt10']/span/@title").extract_first()
            item['area'] = dl.xpath(".//div[contains(@class,'area')]/p/text()").extract_first()
            item['price'] = "".join(dl.xpath(".//div[@class='moreInfo']/p[1]//text()")).extract()
            item['unit'] ="".join(dl.xpath(".//div[class='moreInfo']/p[2]//text()")).extract()
            detail_url = dl.xpath(".//p[@class='title']/a/@href").extract_first()
            item['origin_url'] = response.urljoin(detail_url)
            yield item
        next_url = response.xpath(".//a[@id='PageControll_hlk_next']/@href")
        yield scrapy.Request(url=response.urljoin(next_url), callback=self.parse_esf,meta={"info":(province,city)})