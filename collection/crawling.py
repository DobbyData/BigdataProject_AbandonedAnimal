from bs4 import BeautifulSoup
from urllib.parse import urlencode
import sys
from urllib.request import Request, urlopen
from datetime import datetime
import math
import json
import pandas as pd
import os
import xmltodict

RESULT_DIRECTORY = '../__result__/crawling'

#동물관리보호소  공공데이터 API 서비스키
# SURVICE_KEY = 'kjzgwf40zX1dWlcX1PKEw2r%2BUfP1YbASnaMYa5dQ6aOr9mFJOi%2FcDQB%2FRlvaWdCVVQ5uSS%2BWwXU1WJYDAFmmBA%3D%3D'    # 김민규
SURVICE_KEY = 'EdieVeGWBCgcq7f02Z4gpx%2FEssqE8l151SGr%2FHYps1SvWYKgXvpn35kSxTQUhMkxyf9yOrp2SU%2Fr9xZjf7aWQA%3D%3D'    # 송수진
# SURVICE_KEY = 'FXCllNPKHcV69y%2FBSMoNxmHKoCNvPRagdDMlScSRSsNJLbGqp12VchucwYzzGf1jWKNrbyi%2BBDF0zJSL%2Bi4K3Q%3D%3D'  # 김신애
base_url='http://openapi.animal.go.kr/openapi/service/rest/abandonmentPublicSrvc/abandonmentPublic'


def animal_url(base=base_url, **params):
    url = '%s?%s&ServiceKey=%s' % (base, urlencode(params), SURVICE_KEY)
    return url

def animal_crawling():
    for year in range(2009, 2019):  # 년도가 바뀔 때마다, pageNo, isnext 초기화
        bgnde = '%s0101' % (year)
        endde = '%s1231' % (year)
        pageNo = 1
        isnext = True
        datalist = []
        encoding = 'utf-8'

        while isnext:
            url = animal_url(bgnde=bgnde, endde=endde, pageNo=pageNo, numOfRows=1000)
            res = urlopen(url=url)

            if res is None:
                break

            xml_result = res.read().decode(encoding)

            xml_data = xmltodict.parse(xml_result)
            xml_dict = json.dumps(xml_data)
            dict_result = json.loads(xml_dict)
            xml_body = dict_result.get('response').get('body')

            xml_nor = None if dict_result is None else xml_body.get('numOfRows')
            xml_tc = None if dict_result is None else xml_body.get('totalCount')

            lostData = xml_body.get('items').get('item')

            for data in lostData:
                datalist.append(data)

            cnt = math.ceil(int(xml_tc)/int(xml_nor))   # 크롤링 횟수 확인

            if pageNo == cnt:
                isnext = False
            else:
                pageNo += 1

            df = pd.DataFrame(datalist)     # Dict -> DataFrame
            print(xml_tc)
            print(df)

        filename = '{0}/lostAnimal_{1}_{2}.csv'.format(RESULT_DIRECTORY,bgnde,endde)
        df.to_csv(filename, mode='w', encoding='euc-kr', index=True)


def crawler(
        url='',
        encoding='euc-kr',
        proc=lambda html:html, #통과코드 #처리 # 실행되는지 안되는지 확인
        store=lambda html:html, #저장
        err=lambda e: print('%s : %s' % (e, datetime.now()), file=sys.stderr)):
    try:
        request = Request(url) #url 요청
        resp = urlopen(request) #url open

        try:
            receive = resp.read() #url 읽어서
            result = store(proc(receive.decode(encoding))) #decode시킴

        except UnicodeDecodeError:
            result = receive.decode(encoding, 'replace')
        print('%s : success for request [%s]' % (datetime.now(), url))
        return result

    except Exception as e:
        err(e)


def shelter_crawling():
    results = []
    for page in range(34):
        url = 'http://www.animal.go.kr/portal_rnl/map/mapInfo2.jsp'
        content= '?s_date=&e_date=&s_upr_cd=&s_org_cd=&s_up_kind_cd=&s_kind_cd=&s_name=&pagecnt=%d' % page
        urlcont = url+content
        #print(urlcont)
        html = crawler(url=urlcont)
        #print(html) # 해당페이지의 전체코드가 그대로보임.

        bs = BeautifulSoup(html, 'html.parser')
        tag_tbody = bs.find('tbody')

        tags_tr = tag_tbody.findAll('tr')
        #print(tags_tr)

        for tag_tr in tags_tr:
            strings = list(tag_tr.strings)
            if len(strings) is not 2:
                #print(strings)
                area = strings[1]
                name = strings[3]
                number = strings[5]
                address = strings[7].replace('\t\xa0\xa0','').replace('\n              ','').replace('\n\t\t\t','')
                results.append((area, name, number, address))
    print(results)

    #if not os.path.exists(RESULT_DIRECTORY):
    #     os.makedirs(RESULT_DIRECTORY)

    table = pd.DataFrame(results, columns=['area','name','number','address'])
    #print(table)
    # table.to_csv('shelter.csv', encoding='utf-8', mode='w',index=True)
    table.to_csv('{0}/shelter.csv'.format(RESULT_DIRECTORY),encoding='utf-8',mode='w',index=True)


if not os.path.exists(RESULT_DIRECTORY):
    os.makedirs(RESULT_DIRECTORY)


if __name__ == '__main__':
    shelter_crawling()
    # animal_crawling()