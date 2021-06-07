import requests, re, json
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
        # if username not in self.session.get("https://edusys.wvpn.hrbeu.edu.cn/jsxsd/framework/main.jsp").text:
        #    raise Exception("Incorrect username or password!")
        return self

    def login_pingjiao(self, username: str, password: str):
        res = self.session.get(
            "https://cas.hrbeu.edu.cn/cas/login?service=http://pjcs.hrbeu.edu.cn/login/return?type=mobile#/")
        text = res.text
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
        self.pid = self.get_pid(text)
        return self

    def getScores(self):
        scores = []
        res = self.session.post(
            url="https://edusys.wvpn.hrbeu.edu.cn/jsxsd/kscj/cjcx_list",
            data={"xsfs": "all"}
        )
        s = soup(res.text, features="html.parser")
        for row in s.find(id="dataList").find_all("tr"):
            contents = []
            for td in row.find_all('td'):
                temp = td.contents if td.a is None else td.a.contents
                contents.append(temp[0] if len(temp) > 0 else "")
            if len(contents) > 0:
                scores.append(contents)
        return scores

    def getTermTimetable(self, term: str):
        result = []
        for week in range(1, 31):
            result.append(self.getTimetable(term, str(week)))
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

    def get_pid(self, content):
        import re
        # <input class="for-form" type="hidden" name="pid" value="ge9c2yev">
        pattern = re.compile(r'<input class="for-form" type="hidden" name="pid" value="(.*?)"')
        return pattern.findall(content)[0]

    def get_csrf_token(self, content):
        import re
        pattern = re.compile(r'<meta itemscope="csrfToken" content="(.*?)">')
        return pattern.findall(content)[0]

    def report(self):
        import time, json
        from lib.form import report_str

        res = self.session.get("http://one.hrbeu.edu.cn/infoplus/form/JCXBBJSP/start")
        csrf = self.get_csrf_token(res.text)
        res = self.session.post("http://one.hrbeu.edu.cn/infoplus/interface/start", data={
            "csrfToken": csrf,
            "idc": "JCXBBJSP",
            "release": "",
            "formData": r'{"_VAR_URL":"http://one.hrbeu.edu.cn/infoplus/form/JCXBBJSP/start","_VAR_URL_Attr":"{}"}',
        })
        url = json.loads(res.text)["entities"][0]
        report_id = url.split("/")[-2]

        res = self.session.get(url)
        csrf = self.get_csrf_token(res.text)
        cur_time = time.localtime(time.time())
        temp = list(cur_time)
        temp[3] = temp[4] = temp[5] = 0
        today = time.struct_time(temp)
        today = int(time.mktime(today))
        now = int(time.time())

        res = self.session.post(
            url="http://one.hrbeu.edu.cn/infoplus/interface/doAction",
            data={
                'stepId': report_id,
                'actionId': 1,
                'formData': report_str.format(
                    year=cur_time.tm_year,
                    month=cur_time.tm_mon,
                    day=cur_time.tm_mday,
                    today=today,
                    now=now,
                ),
                'timestamp': int(time.time()),
                'rand': "267.09397282941765",
                'boundFields': 'fieldFDYsprq,fieldJBszgy,fieldBBshi,fieldLYqtl,fieldBBsheng,fieldLYqtyc,fieldLYzzl,fieldDel,fieldJBszxy,fieldFSJspsj,fieldLYrqFrom,fieldLYgyl,fieldGYLfjh,fieldFSJspr,fieldQTLmc,fieldLYbgl,fieldBBcxrqFrom,fieldJBjcxlx,fieldJLly,fieldLYzzyc,fieldBBsylb,fieldFDYspyj,fieldLYyc,fieldZMCLUrl,fieldBBcxsjFrom,fieldBBycsj,fieldBBdiqu,fieldJBsqr,fieldLYsjTo,fieldJBlxfs,fieldJBxh,fieldBBcxsy,fieldSPyc,fieldLYyc1,fieldZZLfjh,fieldBBcxsjTo,fieldBGLfjh,fieldFSJspyj,fieldLYrqTo,fieldBByc2,fieldBByc3,fieldQTLfjh,fieldBByc1,fieldJBfdyxm,fieldBBh1,fieldBBcxrqTo,fieldLYbgyc,fieldZZLmc,fieldLYgyyc,fieldLYsjFrom,fieldGYLmc,fieldBBxxdz,fieldJBfdylxdh,fieldBGLmc,fieldFDYspr',
                "csrfToken": csrf,
                "lang": "en",
                "nextUsers": "{}",
                "remark": "",
            }
        )

    def pingjiao(self, check=False):
        token = self.session.cookies['token']
        res = json.loads(self.session.get(
            url="http://pjcs.hrbeu.edu.cn/university-facade/TeachingEvaluation/queryWaitList.shtml?pageIndex=0&pageSize=10000" + "&token=" + token,
        ).text)

        done_list = []
        for record in res['data']['rows']:
            post_str = ""
            course_name = record['obj_name']
            course_id = record['id']
            done_list.append(course_name)
            questions = json.loads(self.session.get(
                "http://pjcs.hrbeu.edu.cn/university-facade//TeachingEvaluation/queryPaperForWait.shtml?token=%s&id=%s"
                % (token, course_id)
                ).text)
            for row in questions['data']['content']:
                question_id = row['id']
                question_type = row['type']
                question_sn = ""
                if question_type == 0:
                    question_sn = "5"
                if question_type == 1:
                    question_sn = "No"
                post_str += "subjectId:%s,type:%s,optionSn:%s;" % (
                    question_id,
                    str(question_type),
                    question_sn
                )

            if not check:
                self.session.post(
                    url="http://pjcs.hrbeu.edu.cn/university-facade//TeachingEvaluation/SaveResultDataH5.shtml",
                    data={
                        'masterid': course_id,
                        'data': post_str,
                    }
                )

        return done_list


if __name__ == "__main__":
    exit(0)
