import requests
import re
from bs4 import BeautifulSoup
import pandas as pd 


headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/104.0.0.0 Safari/537.36',
}

# 根据网址获取网页源代码并用beautifulsoup解析
def get_soup(url):
    response = requests.get(url, headers=headers)
    content = response.text
    soup = BeautifulSoup(content,'html.parser')
    return soup

# 提前准备好data数据用于输出
data_set = {
    "一级分类":[],
    "二级分类":[],
    "疾病":[],
    "挂什么科":[],
    "哪些症状":[],
    "好发人群":[],
    "治疗方法":[],
    "治疗费用":[],
    "是否传染":[],
    "患病比例":[],
    "治愈率":[],
    "治疗周期":[],
    "html":[]
    }


# 当前爬取数据量
crawled_count = 0
# 初始网站用于开始爬虫
soup = get_soup('https://tag.120ask.com/jibing/ks/xxgnk.html')
# 寻找网页中一级分类的部分
pattern = re.compile("一级分类：")
element = soup.find('var', text=pattern)
# 循环一级分类下的所有数据
for first_subject in element.find_next_sibling('p').findAll('a'):
    # 获取每一个一级分类的名字和链接
    first_subject_string = first_subject.string
    first_subject_href = "https:" + first_subject.attrs["href"]
    # 使用链接获取该一级分类对应的网页
    soup2 = get_soup(first_subject_href)
    # 寻找该网页中二级分类的部分
    pattern2 = re.compile("二级分类：")
    element2 = soup2.find('var', text=pattern2)
    # 循环二级分类下的所有数据
    for second_subject in element2.find_next_sibling('p').findAll('a'):
        # 获取二级分类的名字和链接
        second_subject_string = second_subject.string
        second_subject_href = "https:" + second_subject.attrs["href"]
        # 使用链接获取二级分类的网页
        ill_soup = get_soup(second_subject_href)
        for ill in  ill_soup.find_all("div",{'class':'sick_tag'})[1].find('div',{'class':'tag_li'}).find('p').findAll('a'):
            # 获取疾病的名字和链接
            ill_string = ill.string
            ill_href = "https:" + ill.attrs["href"]
            # 进入单个疾病的网页
            ill_soup2 = get_soup(ill_href)
            # 打印当前的一级分类,二级分类,疾病名
            print(first_subject_string,second_subject_string,ill_string)
            # 判断是否存在表格
            if ill_soup2.find('span', text=re.compile("挂什么科：")) is not None :
                # 获取表格数据
                data1 = ill_soup2.find('span', text=re.compile("挂什么科：")).find_next_sibling('var').text
                data2 = ill_soup2.find('span', text=re.compile("哪些症状：")).find_next_sibling('var').text
                data3 = ill_soup2.find('span', text=re.compile("好发人群：")).find_next_sibling('var').text
                data4 = ill_soup2.find('span', text=re.compile("治疗方法：")).find_next_sibling('var').text
                data5 = ill_soup2.find('span', text=re.compile("治疗费用：")).find_next_sibling('var').text
                data6 = ill_soup2.find('span', text=re.compile("是否传染：")).find_next_sibling('var').text
                data7 = ill_soup2.find('span', text=re.compile("患病比例：")).find_next_sibling('var').text
                data8 = ill_soup2.find('span', text=re.compile("治愈率：")).find_next_sibling('var').text
                data9 = ill_soup2.find('span', text=re.compile("治疗周期：")).find_next_sibling('var').text
                # 保存数据到内存中
                data_set["一级分类"].append(first_subject_string)
                data_set["二级分类"].append(second_subject_string)
                data_set["疾病"].append(ill_string)
                data_set["挂什么科"].append(data1)
                data_set["哪些症状"].append(data2)
                data_set["好发人群"].append(data3)
                data_set["治疗方法"].append(data4)
                data_set["治疗费用"].append(data5)
                data_set["是否传染"].append(data6)
                data_set["患病比例"].append(data7)
                data_set["治愈率"].append(data8)
                data_set["治疗周期"].append(data9)
                data_set["html"].append(ill_href)
                crawled_count +=1
                print(f"第{crawled_count}条数据已被存入文件")
                
# 保存数据为csv文件
df = pd.DataFrame(data_set)
df.to_csv('data.csv',encoding='utf-8',index=0)            