import lxml, requests
from bs4 import BeautifulSoup
def subway_erica():
    response = requests.get('http://swopenapi.seoul.go.kr/api/subway/sample/xml/realtimeStationArrival/0/5/%ED%95%9C%EB%8C%80%EC%95%9E')
    soup = BeautifulSoup(response.content,'lxml-xml')
    minute_list = {'한대앞':0,'중앙':2,'고잔':4,'초지':6,'안산':9,'신길온천':12,'정왕':16,'오이도':18,'상록수':2,'반월':6,'대야미':8,'수리산':10,'산본':12,'금정':16,'범계':19}
    status_list = {'0':'진입','1':'도착','2':'전역 출발','3':'전역 도착','4':'전역 진입','5':'전역 접근','99':'운행'}
    string = ''
    for x in soup.findAll('row'):
        updn = x.find('updnLine').string
        location = x.find('arvlMsg3').string
        if updn == "상행":
            string += x.find('bstatnNm').string + '행\n'
            string += x.find('arvlMsg3').string + '역 '
            string += status_list[x.find('arvlCd').string] + '\n'
            string += str(minute_list[location]) + '분 후 도착' + '\n'
            break
    string += '\n'
    for x in soup.findAll('row'):
        updn = x.find('updnLine').string
        location = x.find('arvlMsg3').string
        if updn == "하행":
            string += x.find('bstatnNm').string + '행\n'
            string += x.find('arvlMsg3').string + '역 '
            string += status_list[x.find('arvlCd').string] + '\n'
            string += str(minute_list[location]) + '분 후 도착'
            break
    return string

def subway_seoul():
    response = requests.get('http://swopenapi.seoul.go.kr/api/subway/sample/xml/realtimeStationArrival/0/5/%ED%95%9C%EC%96%91%EB%8C%80')
    soup = BeautifulSoup(response.content,'lxml-xml')
    status_list = {'0':'진입','1':'도착','2':'전역 출발','3':'전역 도착','4':'전역 진입','5':'전역 접근','99':'운행'}
    string = ''
    for x in soup.findAll('row'):
        updn = x.find('updnLine').string
        location = x.find('arvlMsg3').string
        if updn == "내선":
            string += x.find('bstatnNm').string + '행\n'
            string += x.find('arvlMsg3').string + '역 '
            string += status_list[x.find('arvlCd').string] + '\n'
            string += str(int(x.find('barvlDt').string) // 60) + '분 '+ str(int(x.find('barvlDt').string) % 60) +'초 후 도착\n'
            break
    string += '\n'
    for x in soup.findAll('row'):
        updn = x.find('updnLine').string
        location = x.find('arvlMsg3').string
        if updn == "외선":
            string += x.find('bstatnNm').string + '행\n'
            string += x.find('arvlMsg3').string + '역 '
            string += status_list[x.find('arvlCd').string] + '\n'
            string += str(int(x.find('barvlDt').string) // 60) + '분 '+ str(int(x.find('barvlDt').string) % 60) +'초 후 도착'
            break
    return string