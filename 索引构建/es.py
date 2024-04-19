# 建立索引 搭建ES框架
import json
import os

from elasticsearch import Elasticsearch


def es_build(dirname):
    # 参数    dirname: es构建使用的目录名称
    # 功能    构建es索引
    # 返回值   无
    es.delete_by_query(index="test", body={'query': {"match_all": {}}})  # 清空test index的数据
    for path, dirs, files in os.walk(dirname):
        for file in files:
            # print(os.path.join(path, file))
            with open(os.path.join(path, file), encoding="utf-8") as file:
                try:  # 异常处理，比如读文件异常
                    json_data = json.load(file)
                    print_json_data(json_data)
                except Exception as e:
                    print(file)
                    print(e)
                    continue
                res = es.index(index="test", document=json_data)  # 建立索引
                print(res['result'])


def print_json_data(json_data):
    # 参数    json_data: 要打印的数据
    # 功能    打印json_data
    # 返回值   无
    # print("%(timestamp)s %(author)s: %(text)s" % hit["_source"])
    # print("%(X-FileName)s" % hit["_source"])
    print("url: " + json_data["url"])
    print("title: " + json_data["title"])
    content = json_data["content"]
    content = str(content).replace('\n', '')
    content = str(content).replace('\t', '')
    if len(content) > 100:
        print("content: " + content[0: 99] + "...")
    else:
        print("content: " + content)
    print()


def print_hit(hit):
    # 参数    hit: 要打印的数据（搜索结果）
    # 功能    打印hit
    # 返回值   无
    # print("%(timestamp)s %(author)s: %(text)s" % hit["_source"])
    # print("%(X-FileName)s" % hit["_source"])
    print("url: " + hit["_source"]["url"])
    print("score: " + hit["_score"].__str__())
    print("title: " + hit["_source"]["title"])
    content = hit["_source"]["content"]
    content = str(content).replace('\n', '')
    content = str(content).replace('\t', '')
    if len(content) > 100:
        print("content: " + content[0: 99] + "...")
    else:
        print("content: " + content)
    print(page_rank_results[hit["_source"]["url"]] * 1000)
    print()


es = Elasticsearch()
dirname = "crawl_iteration_3"
# es_build(dirname)

with open(os.path.join(dirname + "_pr_results.json"), 'r', encoding="utf-8") as file:  # 加载pr结果
    page_rank_results = json.load(file)
    file.close()

# 匹配测试
# res = es.search(index="test", query={"match_all": {}})  # 匹配所有
# print("搜索所有")
# print("Got %d Hits:" % res['hits']['total']['value'])  # 似乎上限是10000
# for hit in res['hits']['hits']:  # 打印所有，但是只显示10条
#     print_hit(hit)

# bool 复合匹配   利用boost给标题分配更高的权重
query = "南开 新闻"
# res = es.search(index="test", query={"bool": {
#     "should": [{"match": {'title': {"query": query, "boost": 2}}},
#                {"match": {'content': {"query": query, "boost": 1}}}],
#     "minimum_should_match": "100%"}})

query = "南开 新闻"
# match_phrase 词组匹配
res = es.search(index="test", query={"bool": {
    "should": [{"match_phrase": {'title': {"query": query, "boost": 2}}},
               {"match_phrase": {'content': {"query": query, "boost": 1}}}],
    "minimum_should_match": "100%"}}, size=20)

# wildcard 通配查询
query = "*开"
res = es.search(index="test", query={"bool": {
    "should": [{"wildcard": {'title': {"wildcard": query, "boost": 2}}},
               {"wildcard": {'content': {"wildcard": query, "boost": 1}}}],
    "minimum_should_match": "50%"}}, size=10)

# 文档查询
query = "南开"
res = es.search(index="test", query={"bool": {
    "should": [{"match": {'title': {"query": query, "boost": 1}}},
               {"wildcard": {'url': {"wildcard": "*.doc", "boost": 1}}}],
    "minimum_should_match": "100%"}}, size=10)

print("'" + query + "'的搜索结果")
print("Got %d Hits:" % res['hits']['total']['value'])
for hit in res['hits']['hits']:
    print_hit(hit)
