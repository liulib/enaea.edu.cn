import hashlib
import time
import random
import re
import json
import copy

from lxml import etree
import requests


def get_timestamp():
	"""
	构造时间戳，后面三位数字不知道是啥，随机生成
	返回值：str类型的时间戳
	"""
	return str(int(time.time())) + ''.join(str(i) for i in random.sample(range(0,9),3))

def get_headers(referer):
	"""
	构造headers
	referer:str类型的url
	返回值:字典类型的headers
	"""
	headers={'Accept-Language':'zh-CN,zh;q=0.9','User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.108 Safari/537.36'}
	if referer == '':
		return headers
	else:
		headers['referer'] = referer
		return headers

	
def login(username, password):
	"""
	登录函数，用于获取cookies
	username:用户名
	password:密码（MD5加密）
	请求方式:GET
	返回值:str类型的cookies
	"""
	# md5加密密码
	m = hashlib.md5()
	b = password.encode(encoding='utf-8')
	m.update(b)
	md5_password = m.hexdigest()
	timestamp = get_timestamp()
	# 构造headers
	headers = get_headers('http://study.enaea.edu.cn/login.do')
	url = 'http://passport.enaea.edu.cn/login.do?ajax=true&jsonp=ablesky_{}&j_username={}&j_password={}&_acegi_security_remember_me=false&_={}'.format(timestamp, username, md5_password, timestamp)
	res = requests.post(url=url, headers=headers)
	status = json.loads(res.text[22:-2])['success']
	if status == True:
		print('登录成功')
		# cookies = requests.utils.dict_from_cookiejar(res.cookies)
		# print('获取cookies:{}'.format(cookies))
		return res.cookies
	else:
		print('登录失败，请重试')
		return None

def get_progress_status(cookies):
	"""
	获取当前进度
	cookies:登录后的cookies值
	"""
	url = 'http://study.enaea.edu.cn/circleIndexRedirect.do?action=toCircleIndex&circleId=39321&ct='+get_timestamp()
	headers = get_headers('')
	res = requests.get(url=url, headers=headers, cookies=cookies)
	html = etree.HTML(res.text)
	time_data = html.xpath('/html/body/div[4]/div[2]/div[4]/div/strong/text()')
	process_data = html.xpath('/html/body/div[4]/div[2]/div[4]/div/div[1]/div[2]/text()')
	print(time_data[0], '总进度{}'.format(process_data[0]))


def get_myclass(cookies):
	"""
	获取课程id
	cookies:登录后的cookies值
	返回值；list 内含课程id 课程名 进度
	"""
	timestamp = get_timestamp()
	url = 'http://study.enaea.edu.cn/circleIndex.do?action=getMyClass&start=0&limit=100&isCompleted=&circleId=39321&syllabusId=207109&categoryRemark=all&_={}&_={}'.format(timestamp, timestamp)
	headers = get_headers('http://study.enaea.edu.cn/circleIndexRedirect.do?action=toNewMyClass&type=course&circleId=39321&syllabusId=207109&isRequired=true&studentProgress=1')
	res = requests.get(url=url, headers=headers, cookies=cookies)
	if res.status_code == 200:
		json_res = json.loads(res.text)
		results = json_res['result']['list']
		result_list = []
		for result in results:
			dic = dict(
				course_id = result['studyCenterDTO']['courseId'], 
				course_title = result['studyCenterDTO']['courseTitle'], 
				study_progress = result['studyCenterDTO']['studyProgress'])
			result_list.append(dic)
		return result_list
	else:
		print('出错请重试')

def get_coursecontentlist(course_id, cookies):
	"""
	获取详细课程视频信息
	course_id：课程id
	cookies:登录后的cookies值
	返回值:list 内含课程视频id 视频id 进度 视频名
	"""
	timestamp = get_timestamp()
	headers = get_headers('http://study.enaea.edu.cn/viewerforccvideo.do?courseId={}&circleId=39321'.format(course_id))
	url = 'http://study.enaea.edu.cn/course.do?action=getCourseContentList&courseId={}&circleId=39321&_={}'.format(course_id, timestamp)
	res = requests.get(url=url, headers=headers, cookies=cookies)
	if res.status_code == 200:
		json_res = json.loads(res.text)
		results = json_res['result']['list']
		result_list = []
		for result in results:
			dic = dict(
			coursecontent_id = result['id'],
			ccvideoid = result['ccvideoId'],
			studyprogress = result['studyProgress'],
			filename = result['filename'],)
			result_list.append(dic)
		return result_list


def statisticforccvideo(course_id, coursecontent_id, cookies):
	"""
	获取观看视频所需要的cookies
	course_id：课程id
	coursecontent_id：课程视频id
	cookies:登录后的cookies值
	返回值:用于观看视频的cookies
	"""
	timestamp = get_timestamp()
	headers = get_headers('http://study.enaea.edu.cn/viewerforccvideo.do?courseId={}&circleId=39321'.format(course_id))
	url = 'http://study.enaea.edu.cn/course.do?action=statisticForCCVideo&courseId={}&coursecontentId={}&circleId=39321&_={}'.format(course_id, coursecontent_id, timestamp)
	res = requests.get(url=url, headers=headers, cookies=cookies)
	cookies.update(res.cookies)
	return cookies


def study_log(coursecontent_id, cookies):
	"""
	观看视频
	coursecontent_id：课程视频id
	cookies:用于观看视频的cookies
	返回值:观看结果
	"""
	url = 'http://study.enaea.edu.cn/studyLog.do'
	timestamp = get_timestamp()
	data = {
	"id":coursecontent_id,
	"circleId":"39321",
	"finish":"false",
	"ct":timestamp
	}
	res = requests.post(url=url, cookies= cookies, data=data)
	json_res = json.loads(res.text)
	if json_res['success'] == True:
		return json_res['progress']
	else:
		return None


if __name__ == '__main__':
	username = input('请输入账号：')
	password = input('请输入密码：')
	cookies = login(username, password)
	
	class_list = get_myclass(cookies)
	for class_detail in class_list:
		get_progress_status(cookies)
		if class_detail['study_progress'] == '100':
			print('{}已经学习完成,进入下一门学习'.format(class_detail['course_title']))
		else:
			coursecontentlist = get_coursecontentlist(class_detail['course_id'], cookies=cookies)
			for coursecontent in coursecontentlist:
				if coursecontent['studyprogress'] == '100':
					print('{}已经学习完成,进入下一门学习'.format(coursecontent['filename']))
				else:
					# 对cookies进行深拷贝,以免cookies越来越大
					newcookies = copy.deepcopy(cookies)
					newcookies = statisticforccvideo(class_detail['course_id'], coursecontent['coursecontent_id'], newcookies)
					while True:
						time.sleep(65)
						progress = study_log(coursecontent['coursecontent_id'], newcookies)
						if progress == None:
							time.sleep(60)
							continue
						print('当前正在学习{}下的{},进度为{}%'.format(class_detail['course_title'], coursecontent['filename'], progress))
						if progress == 100:
							break



					
					





