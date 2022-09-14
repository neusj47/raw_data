from dateutil.relativedelta import relativedelta
import warnings
warnings.filterwarnings(action='ignore')
import numpy as np
import requests
import pandas as pd
from pykrx import stock
from datetime import datetime
import math

def get_bdate_info(start_date, end_date) :
    date = pd.DataFrame(stock.get_previous_business_days(fromdate=start_date, todate=end_date)).rename(columns={0: '일자'})
    prevbdate = date.shift(1).rename(columns={'일자': '전영업일자'})
    date = pd.concat([date, prevbdate], axis=1).fillna(datetime.strftime(datetime.strptime(
        stock.get_nearest_business_day_in_a_week(
            datetime.strftime(datetime.strptime(start_date, "%Y%m%d") - relativedelta(days=1), "%Y%m%d")), "%Y%m%d"),
                                                                         "%Y-%m-%d %H:%M:%S"))
    date['주말'] = ''
    for i in range(0, len(date) - 1):
        if abs(datetime.strptime(datetime.strftime(date.iloc[i + 1].일자, "%Y%m%d"), "%Y%m%d") - datetime.strptime(
                datetime.strftime(date.iloc[i].일자, "%Y%m%d"), "%Y%m%d")).days > 1:
            date['주말'].iloc[i] = 1
        else:
            date['주말'].iloc[i] = 0
    month_list = date.일자.map(lambda x: datetime.strftime(x, '%Y-%m')).unique()
    monthly = pd.DataFrame()
    for m in month_list:
        try:
            monthly = monthly.append(date[date.일자.map(lambda x: datetime.strftime(x, '%Y-%m')) == m].iloc[-1])
        except Exception as e:
            print("Error : ", str(e))
        pass
    date['연도'] = date.일자.map(lambda x: datetime.strftime(x, '%Y'))
    date['월'] = date.일자.map(lambda x: datetime.strftime(x, '%m'))
    date['분기'] = ''
    date['반기'] = ''
    date['주기'] = date.일자.map(lambda x: x.week)
    date['Quarterly'] = ''
    date['분기말'] = ''
    date['Biannually'] = ''
    date['반기말'] = ''
    for i in range(0, len(date)):
        date['연도'].iloc[i] = str(date['연도'].iloc[i])
        date['분기'].iloc[i] = str(math.ceil(int(date['월'].iloc[i]) / 3))
        date['반기'].iloc[i] = str(math.ceil(int(date['월'].iloc[i]) / 6))

        date['Quarterly'].iloc[i] = date['연도'].iloc[i] + date['분기'].iloc[i]
        date['Biannually'].iloc[i] = date['연도'].iloc[i] + date['반기'].iloc[i]

    for t in range(0, len(date) - 1):
        if date.Quarterly.iloc[t + 1] != date.Quarterly.iloc[t]:
            date['분기말'].iloc[t] = 1
        else:
            date['분기말'].iloc[t] = 0
    for t in range(0, len(date) - 1):
        if date.Biannually.iloc[t + 1] != date.Biannually.iloc[t]:
            date['반기말'].iloc[t] = 1
        else:
            date['반기말'].iloc[t] = 0
    date['월말'] = np.where(date['일자'].isin(monthly.일자.tolist()), 1, 0)
    date = date[date.일자 <= datetime.strftime(datetime.strptime(end_date, "%Y%m%d"), "%Y-%m-%d")]
    date['주말'].iloc[len(date) - 1] = 1
    date['분기말'].iloc[len(date) - 1] = 1
    date['반기말'].iloc[len(date) - 1] = 1
    date['월말'].iloc[len(date) - 1] = 1
    return date

def get_sector_info(stddate):
    tgtdate = stock.get_nearest_business_day_in_a_week(datetime.strftime(datetime.strptime(stddate, "%Y%m%d"),"%Y%m%d"))
    # sector = {10: '에너지',
    #           15: '소재',
    #           20: '산업재',
    #           25: '경기관련소비재',
    #           30: '필수소비재',
    #           35: '건강관리',
    #           40: '금융',
    #           45: 'IT',
    #           50: '커뮤니케이션서비스',
    #           55: '유틸리티'}
    sector = {1010: '에너지',
              1510: '소재',
              2010: '자본재',
              2020: '상업서비스와공급품',
              2030: '운송',
              2510: '자동차와부품',
              2520: '내구소비재와의류',
              2530: '호텔,레스토랑,레저 등',
              2550: '소매(유통)',
              2560: '교육서비스',
              3010: '식품과기본식료품소매',
              3020: '식품,음료,담배',
              3030: '가정용품과개인용품',
              3510: '건강관리장비와서비스',
              3520: '제약과생물공학',
              4010: '은행',
              4020: '증권',
              4030: '다각화된금융',
              4040: '보험',
              4050: '부동산',
              4510: '소프트웨어와서비스',
              4520: '기술하드웨어와장비',
              4530: '반도체와반도체장비',
              4535: '전자와 전기제품',
              4540: '디스플레이',
              5010: '전기통신서비스',
              5020: '미디어와엔터테인먼트',
              5510: '유틸리티'}
    df = pd.DataFrame(columns=['Code', 'Name', 'Sector','Industry'])
    for i, sec_code in enumerate(sector.keys()):
        response = requests.get(
            'http://www.wiseindex.com/Index/GetIndexComponets?ceil_yn=0&dt=' + tgtdate + '&sec_cd=G' + str(sec_code))
        if (response.status_code == 200):
            json_list = response.json()
            for json in json_list['list']:
                code = 'A' + json['CMP_CD']
                name = json['CMP_KOR']
                Sector = json['SEC_NM_KOR']
                Industry = json['IDX_NM_KOR'][5:]
                df = df.append(
                    {'Code': code, 'Name': name, 'Sector': Sector, 'Industry': Industry}, ignore_index=True)
    return df

def get_sector_valuation(end_date) :
    end_date = stock.get_nearest_business_day_in_a_week(datetime.strftime(datetime.strptime(end_date, "%Y%m%d"), "%Y%m%d"))
    start_date = stock.get_nearest_business_day_in_a_week(datetime.strftime(datetime.strptime(end_date, "%Y%m%d") - relativedelta(months=1),"%Y%m%d"))
    bdate = get_bdate_info(start_date, end_date)['일자'].sort_values(ascending=False)
    start_date = datetime.strftime(bdate.iloc[len(bdate)-1], "%Y-%m-%d")
    end_date = datetime.strftime(bdate.iloc[0], "%Y-%m-%d")
    # idx = {'G1010': '에너지',
    #        'G1510': '소재',
    #        'G2010': '자본재',
    #        'G2020': '상업서비스와공급품',
    #        'G2030': '운송',
    #        'G2510': '자동차와부품',
    #        'G2520': '내구소비재와의류',
    #        'G2530': '호텔,레스토랑,레저 등',
    #        'G2550': '소매(유통)',
    #        'G2560': '교육서비스',
    #        'G3010': '식품과기본식료품소매',
    #        'G3020': '식품,음료,담배',
    #        'G3030': '가정용품과개인용품',
    #        'G3510': '건강관리장비와서비스',
    #        'G3520': '제약과생물공학',
    #        'G4010': '은행',
    #        'G4020': '증권',
    #        'G4030': '다각화된금융',
    #        'G4040': '보험',
    #        'G4050': '부동산',
    #        'G4510': '소프트웨어와서비스',
    #        'G4520': '기술하드웨어와장비',
    #        'G4530': '반도체와반도체장비',
    #        'G4535': '전자와 전기제품',
    #        'G4540': '디스플레이',
    #        'G5010': '전기통신서비스',
    #        'G5020': '미디어와엔터테인먼트',
    #        'G5510': '유틸리티'}
    idx = {'WI100': '에너지',
           'WI110': '화학',
           'WI200': '비철금속',
           'WI210': '철강',
           'WI220': '건설',
           'WI230': '기계',
           'WI240': '조선',
           'WI250': '상사,자본재',
           'WI260': '운송',
           'WI300': '자동차',
           'WI310': '화장품,의류',
           'WI320': '호텔,레저',
           'WI330': '미디어,교육',
           'WI340': '소매(유통)',
           'WI400': '필수소비재',
           'WI410': '건강관리',
           'WI500': '은행',
           'WI510': '증권',
           'WI520': '보험',
           'WI600': '소프트웨어',
           'WI610': '하드웨어',
           'WI620': '반도체',
           'WI630': 'IT가전',
           'WI640': '디스플레이',
           'WI700': '전기통신서비스',
           'WI800': '유틸리티'
           }
    df = pd.DataFrame(columns=['일자', '업종코드', '업종명', 'EPS', 'BPS', 'SPS', 'PER', 'PBR', 'PSR', 'EVEBITDA', '매출성장률', '영업이익성장률', '배당수익률'])
    for keys, values in enumerate(idx.items()):
        response = requests.get('https://www.wiseindex.com/DataCenter/GridData?currentPage=1&endDT=' + end_date + '&fromDT=' + start_date + '&index_ids='+str(values[0])+'&isEnd=1&itemType=3&perPage=2000&term=1')
        if (response.status_code == 200):
            json_list = response.json()
            for i in json_list:
                일자 = datetime.strftime(bdate.iloc[i['ROW_IDX']-1], "%Y-%m-%d")
                업종코드 = values[0]
                업종명 = values[1]
                EPS = i['IDX1_VAL1']
                BPS = i['IDX1_VAL2']
                SPS = i['IDX1_VAL3']
                PER = i['IDX1_VAL4']
                PBR = i['IDX1_VAL5']
                PSR = i['IDX1_VAL6']
                EVEBITDA = i['IDX1_VAL7']
                매출성장률 = i['IDX1_VAL8']
                영업이익성장률 = i['IDX1_VAL9']
                배당수익률 = i['IDX1_VAL10']
                df = df.append(
                    {'일자': 일자, '업종코드': 업종코드, '업종명': 업종명, 'EPS': EPS, 'BPS': BPS, 'SPS': SPS, 'PER': PER, 'PBR': PBR, 'PSR': PSR, 'EVEBITDA': EVEBITDA, '매출성장률': 매출성장률, '영업이익성장률': 영업이익성장률, '배당수익률': 배당수익률,}, ignore_index=True).dropna()
    return df



end_date = '20220913'
sector = get_sector_info(end_date)
sector_value = get_sector_valuation(end_date)
sector_value = sector_value[sector_value.일자 == sector_value.iloc[0].일자].reset_index(drop=True).rename(columns ={'업종명':'Industry'})
sector = pd.merge(sector, sector_value[['Industry','EPS','PER','매출성장률','영업이익성장률','배당수익률']], on = 'Industry', how = 'inner')\
                    .rename(columns ={'EPS':'EPS(업종)','PER':'PER(업종)','매출성장률':'매출성장률(업종)','영업이익성장률':'영업이익성장률(업종)','배당수익률':'배당수익률(업종)'})



url = 'https://asp01.fnguide.com/SVO2/ASP/SVD_Main.asp?pGB=1&gicode=A096770&cID=&MenuYn=Y&ReportGB=&NewMenuID=101&stkGb=701'
headers = {"Referer": "HACK"}
html = requests.get(url, headers=headers).text
dfs = pd.read_html(html)
# aaa = dfs[1] # 컨센 실적(QoQ, YoY)
aaa = dfs[8] # 섹터비교 : PER, EPS, ROE, 배당수익률, 베타

url = 'https://comp.wisereport.co.kr/company/c1010001.aspx?cmp_cd=096770'
html = requests.get(url).text
dfs = pd.read_html(html)
asas= dfs[6] # FWD 비교 : PER, EPS
bbb = dfs[9] # 목표가

url = 'https://comp.wisereport.co.kr/company/ajax/cF1001.aspx?cmp_cd=096770&fin_typ=0&freq_typ=Q&encparam=WExFOEpGNGd6MTdSSmNJSXVHek9EZz09&id=VGVTbkwxZ2'
html = requests.get(url).text
dfs = pd.read_html(html)
asdfas = dfs[1] # 분기 재무제표 Long

url = 'https://comp.wisereport.co.kr/company/cF1002.aspx?cmp_cd=096770&finGubun=MAIN&frq=1'
html = requests.get(url).text
dfs = pd.read_html(html)
asse  = dfs[0] # 컨센서스

url = 'https://comp.wisereport.co.kr/include/js?v=6VfuQWAWEeQCb7VAxN907f9SciJwKhCk1pg-2MADuDs1'
html = requests.get(url).text
dfs = pd.read_json(html)


