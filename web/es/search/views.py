import math
from datetime import datetime
import json
import os

from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.views import generic
from django.template import loader
from elasticsearch import Elasticsearch


class Params:
    def __init__(self):
        self.search_text = ""
        self.search_text_2 = ""
        self.results = []
        self.search_type = ""
        self.search_text_type = ""
        self.results_len = 0


class Result:
    def __init__(self):
        self.id = ""
        self.url = ""
        self.score = 0
        self.title = ""
        self.content = ""
        self.content_all = ""


def add_search_log(search_text, search_type):
    with open("search_log.json", 'r', encoding="utf-8") as file:  # 加载搜索历史
        search_log = json.load(file)
        file.close()
    with open("search_log.json", 'w+', encoding="utf-8") as file:  # 添加当前搜索到搜索历史
        search_log.append({"search_text": search_text, "search_type": search_type, "time": datetime.now().strftime("%Y:%m:%d:%H:%M:%S")})
        json.dump(search_log, file)
        file.close()


def search_result(request):
    # template = loader.get_template('search/search.html')
    search_text = request.POST.get('search_text')  # 获得搜索词条
    search_phrase = request.POST.get('search_phrase')
    search_regexp = request.POST.get('search_regexp')

    es = Elasticsearch()
    params = Params()
    results = []

    if search_regexp is not None:
        res = es.search(index="test", query={"bool": {
            "should": [{"wildcard": {'title': {"wildcard": search_regexp, "boost": 2}}},
                       {"wildcard": {'content': {"wildcard": search_regexp, "boost": 1}}}],
            "minimum_should_match": "50%"}}, size=10)
        params.search_text = search_regexp
        params.search_type = "Search Regexp"
        params.search_text_type = "search_regexp"
        params.results_len = res['hits']['total']['value']
        add_search_log(search_regexp, "Search Regexp")
    if search_phrase is not None:
        res = es.search(index="test", query={"bool": {
            "should": [{"match_phrase": {'title': {"query": search_phrase, "boost": 2}}},
                       {"match_phrase": {'content': {"query": search_phrase, "boost": 1}}}],
            "minimum_should_match": "50%"}}, size=10)
        params.search_text = search_phrase
        params.search_type = "Search Phrase"
        params.search_text_type = "search_phrase"
        params.results_len = res['hits']['total']['value']
        add_search_log(search_phrase, "Search Phrase")
    if search_text is not None:
        res = es.search(index="test", query={"bool": {
            "should": [{"match": {'title': {"query": search_text, "boost": 2}}},
                       {"match": {'content': {"query": search_text, "boost": 1}}}],
            "minimum_should_match": "50%"}})
        params.search_text = search_text
        params.search_type = "Search it"
        params.search_text_type = "search_text"
        params.results_len = res['hits']['total']['value']
        add_search_log(search_text, "Search text")
    # res有未定义的风险，但是逻辑上不会出现

    print("Got %d Hits" % res['hits']['total']['value'])
    # print(res)
    for hit in res['hits']['hits']:
        # print("%(timestamp)s %(author)s: %(text)s" % hit["_source"])
        # print("%(X-FileName)s" % hit["_source"])
        # print(hit["_score"])
        # print(hit["_source"])
        result = Result()
        result.url = hit["_source"]["url"]
        result.score = hit["_score"]
        result.title = hit["_source"]["title"]
        content = hit["_source"]["content"]
        result.content_all = content
        if len(content) > 100:
            result.content = content[0: 99] + "..."
        else:
            result.content = content
        results.append(result)

    with open("pr_results.json", 'r', encoding="utf-8") as file:  # 加载pr结果
        page_rank_results = json.load(file)
        file.close()
    with open("url_open_history.json", 'r', encoding="utf-8") as file:  # 加载用户浏览历史
        url_open_history = json.load(file)
        file.close()

    for result in results:
        result.score += math.log(page_rank_results[result.url] * 1000 + url_open_history[result.url] + 1)  # 将pr结果经过一定变换(ln(x+1))加到网页得分里
        # print(math.log(page_rank_results[result.url] * 1000 + 1))
        # print(url_open_history[result.url])
    results.sort(key=lambda result: result.score, reverse=True)
    params.results = results

    # return HttpResponse(results)
    return render(request, 'search/search_result.html', {'params': params})


def search_result_document(request):
    search_document_name = request.POST.get('search_document_name')
    search_document_suffix = request.POST.get('search_document_suffix')

    es = Elasticsearch()

    if search_document_name is None:
        search_document_name = ""
    if search_document_suffix is None:
        search_document_suffix = ""
    res = es.search(index="test_document", query={"bool": {
        "should": [{"wildcard": {'url': {"wildcard": "*." + search_document_suffix, "boost": 2}}},
                   {"match": {'text': {"query": search_document_name, "boost": 1}}}],
        "minimum_should_match": "50%"}}, size=10)
    results = []
    for hit in res['hits']['hits']:
        result = {"url": hit["_source"]["url"], "score": hit["_score"], "text": hit["_source"]["text"]}
        results.append(result)
    params = {"search_document_name": search_document_name, "search_document_suffix": search_document_suffix,
              "results_len": res['hits']['total']['value'], "results": results}
    add_search_log(search_document_name + "(" + search_document_suffix + ")", "Search Document")
    return render(request, 'search/search_result_document.html', {'params': params})


def search(request):
    return render(request, 'search/search.html')


def test(request):
    return render(request, 'search/test.html')


def search_log(request):
    with open("search_log.json", 'r', encoding="utf-8") as file:
        search_log = json.load(file)
        file.close()
    params = {"search_log": search_log, "search_log_len": len(search_log)}
    return render(request, 'search/search_log.html', {'params': params})


def search_log_clear(request):
    with open("search_log.json", 'w+', encoding="utf-8") as file:
        search_log = []
        json.dump(search_log, file)
        file.close()
    with open("search_log.json", 'r', encoding="utf-8") as file:
        search_log = json.load(file)
        file.close()
    params = {"search_log": search_log, "search_log_len": len(search_log)}
    return render(request, 'search/search_log.html', {'params': params})


def search_result_open(request):
    result_title = request.POST.get('result_title')
    result_content_all = request.POST.get('result_content_all')
    params = {"result_title": result_title, "result_content_all": result_content_all}
    return render(request, 'search/search_result_open.html', {'params': params})

def search_result_url_open(request):
    result_url = request.GET.get('result_url')  # 获得访问的url
    with open("url_open_history.json", 'r', encoding="utf-8") as file:  # 加载用户浏览历史
        url_open_history = json.load(file)
        file.close()
    url_open_history[result_url] += 1
    with open("url_open_history.json", 'w', encoding="utf-8") as file:  # 添加用户浏览历史
        json.dump(url_open_history, file)
        file.close()
    return HttpResponseRedirect(result_url)

