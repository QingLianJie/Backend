import requests, re
from bs4 import BeautifulSoup as soup


def verify(username: str, password: str):
    if username == "" or password == "":
        return False
    try:
        Crawler().login(username, password)
    except:
        return False
    return True


def stringify_tag(tag):
    res = ""
    if "contents" in dir(tag):
        for son in tag.contents:
            res = res + stringify_tag(son)
    else:
        res = str(tag)
    return res


class Crawler:
    def __init__(self):
        self.session = requests.session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.87 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9'
        })

    def login(self, username: str, password: str):
        text = self.session.get("https://cas-443.wvpn.hrbeu.edu.cn/cas/login#/").text
        lt = re.compile(r'type="hidden" name="lt" value="(.*?)"').findall(text)[0]
        execution = re.compile(r'type="hidden" name="execution" value="(.*?)"').findall(text)[0]
        data = {
            'username': username,
            'password': password,
            '_eventId': 'submit',
            'lt': lt,
            'source': 'cas',
            'execution': execution,
        }
        res = self.session.post("https://cas-443.wvpn.hrbeu.edu.cn/cas/login", data=data)
        if username not in self.session.get("https://edusys.wvpn.hrbeu.edu.cn/jsxsd/framework/main.jsp").text:
            raise Exception("Incorrect username or password!")

        return self
		
    def login_one(self, username, password):
        text = self.session.get("https://cas.hrbeu.edu.cn/cas/login#/").text
        lt = re.compile(r'type="hidden" name="lt" value="(.*?)"').findall(text)[0]
        execution = re.compile(r'type="hidden" name="execution" value="(.*?)"').findall(text)[0]
        data = {
        'username': username,
        'password': password,
        '_eventId': 'submit',
        'lt': lt,
        'source': 'cas',
        'execution': execution,
        }
        res = self.session.post("https://cas.hrbeu.edu.cn/cas/login", data=data)
        #if username not in self.session.get("https://edusys.wvpn.hrbeu.edu.cn/jsxsd/framework/main.jsp").text:
        #    raise Exception("Incorrect username or password!")

        return self
    
    def getScores(self):
        scores = []
        res = self.session.post(
            url="https://edusys.wvpn.hrbeu.edu.cn/jsxsd/kscj/cjcx_list",
            data={"xsfs": "all"}
        )
        s = soup(res.text, features="html.parser")
        # print(s)
        for row in s.find(id="dataList").find_all("tr"):
            contents = []
            for td in row.find_all('td'):
                temp = td.contents if td.a is None else td.a.contents
                contents.append(temp[0] if len(temp) > 0 else "")
            if len(contents) > 0:
                scores.append(contents)
        return scores

    def getTermTimetable(self, term:str):
        result = []
        for week in range(1,31):
            result.append(self.getTimetable(term,str(week)))
        return result

    def getTimetable(self, term: str, week: str):
        timetable = []
        res = self.session.post(
            url="https://edusys.wvpn.hrbeu.edu.cn/jsxsd/xskb/xskb_list.do",
            data={
                "xnxq01id": term,
                "zc": week,
            }
        )
        s = soup(res.text, features="html.parser")
        if s.find(id='Form1') is None:
            return []

        for row in s.find(id="Form1").find_all("tr")[1:]:
            rows = []
            for td in row.find_all('td'):
                col = []
                kbcontent = td.find(class_="kbcontent")
                if "contents" in dir(kbcontent):
                    classInfo = []
                    for line in kbcontent.contents:
                        temp = stringify_tag(line).strip()
                        if temp != "":
                            if temp == "---------------------":
                                col.append(classInfo)
                                classInfo.clear()
                            else:
                                classInfo.append(temp)
                    if len(classInfo) > 0:
                        col.append(classInfo)
                    rows.append(col)
                else:
                    if not len(td.contents) == 0:
                        rows = [x.strip().replace("\xa0", "") for x in str(td.contents[0]).split(';')]
                        while len(rows) > 0 and rows[-1] == "":
                            rows.pop()
            timetable.append(rows)
        """
        for i in range(len(timetable)):
            if i!=5:
                for j in range(len(timetable[i])):
                    print(i,j,timetable[i][j])
            else:
                print(timetable[i])
        """
        return timetable


if __name__ == "__main__":
    #print(verify("2018065608", "114514"))
    #t = Crawler()
    #t.login("", "")
    #print(t.getTimetable("2020-2021-1", "5"))
    #print(t.getTermTimetable("2020-2021-2"))
    #print(t.getScores())
    exit(0)