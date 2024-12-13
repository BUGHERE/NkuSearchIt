## 介绍

NkuSearchIt 是一个Web搜索引擎南开资源站，本项目通过爬虫迭代地获取了南开校内的资源，并搭建网站提供丰富且个性化的检索服务，技术栈使用 Django + ElasticSearch

![image](https://github.com/BUGHERE/NkuSearchIt/assets/55886903/22e20646-7f51-4115-a6e8-d1184879044f)

## 内容

1. 网页抓取

   1. 网页爬虫使用requests库进行处理
   	  ```python
        response = requests.get(url, timeout=crawl_timeout, headers=headers_parameters, allow_redirects=False)  # allow_redirects是否允许网址跳转
        response.encoding = response.apparent_encoding  # 设置编码为网页编码，否则容易乱码
      ```
      
   2. 在当前爬取网页找到更多的网页

      ```python
        for item in bs.find_all("a"):  # 当前网页html的所有a标签
            href = item.get("href")  # 找到链接
      ```

   3. 过滤无效网页

      （1）404、302、301网页无法访问的网页

      （2）校外网址

      （3）过滤某些特殊网址，例如公安备案网址

   4. 单独处理下载链接

       ```python
         index_suffix = href.rfind(".")  # 下载类型后缀（如果有）
         if href[index_suffix + 1:] in download_suffix_list:  # 如果是下载地址，则存到es的document索引
             json_data_document = {"url": href, "text": item.get_text()}
             res = es.index(index="test_document", document=json_data_document)  # 建立索引
       ```

2. 文本索引

   1. 使用BeautifulSoup库处理html

       ```python
         html = get_html(url)  # 获得网页html
         bs = BeautifulSoup(html, "html.parser")  # 获得bs解析包
       ```

       ```python
         bs.title.get_text()  # 获得title
         content = ""
         for item in bs.findAll():  # 找到所有标签的内容
             content += item.get_text()  # 获得content网页内容
       ```

   2. 保存每个链接url对应的title和content

      ```python
        json_data = {"url": url, "title": title, "content": content}
        with open(os.path.join(dirname, index.__str__() + ".json"), 'w', encoding="utf-8") as file:  # 保存url、title和content
        	json.dump(json_data, file, ensure_ascii=False)
      ```
      
   3. 构建索引
   
       ```python
         with open(os.path.join(path, file), encoding="utf-8") as file:
             json_data = json.load(file)
             res = es.index(index="test", document=json_data)  # 建立索引
       ```
   
3. 链接分析

   1. 使用有向有权图来构建链接分析，用了pygraph库的digraph

      ```python
        if url_expand not in urls_taken:  # 链接未访问
            page_rank_digraph.add_node(url_expand)  # 添加page_rank图节点
            page_rank_digraph.add_edge((url, url_expand))  # 新添加的节点肯定不存在相关边，直接添加
        else:  # 链接已访问
            if not page_rank_digraph.has_edge((url, url_expand)):  # 若不存在边，则添加
                page_rank_digraph.add_edge((url, url_expand))
            else:  # 若存在边，则设置边的权重+1
                page_rank_digraph.set_edge_weight((url, url_expand),page_rank_digraph.edge_weight((url, url_expand)) + 1)
      ```

   2. 计算链接分析，使用上一步生成的图进行计算（迭代法）

      ```python
        for i in range(self.max_iterations):
            change = 0
            for node in nodes:
                rank = 0
                for incident_page in self.graph.incidents(node):  # 遍历所有“入射”的页面
                    rank += self.damping_factor * (page_rank[incident_page] / len(self.graph.neighbors(incident_page)))
                rank += damping_value
                change += abs(page_rank[node] - rank)  # 绝对值
                page_rank[node] = rank
      ```

4. 查询服务

   1. 站内查询

      爬取的链接进行了过滤，所以所有的查询都是站内查询，这里使用了title和content加权排名的方式进行查询

      ```python
        res = es.search(index="test", query={"bool": {
            "should": [{"match": {'title': {"query": search_text, "boost": 2}}},
                       {"match": {'content': {"query": search_text, "boost": 1}}}],
            "minimum_should_match": "50%"}})
      ```

   2. 文档查询

      链接使用通配查询，文本用普通match查询

      ```python
        res = es.search(index="test_document", query={"bool": {
            "should": [{"wildcard": {'url': {"wildcard": "*." + search_document_suffix, "boost": 2}}},
                       {"match": {'text': {"query": search_document_name, "boost": 1}}}],
            "minimum_should_match": "50%"}}, size=10)
      ```

      

   3. 短语查询

      使用match_phrase实现短语查询

      ```python
        res = es.search(index="test", query={"bool": {
            "should": [{"match_phrase": {'title': {"query": search_phrase, "boost": 2}}},
                       {"match_phrase": {'content': {"query": search_phrase, "boost": 1}}}],
            "minimum_should_match": "50%"}}, size=10)
      ```

   4. 通配查询

      使用wildcard实现统配查询

      ```python
        res = es.search(index="test", query={"bool": {
            "should": [{"wildcard": {'title': {"wildcard": search_regexp, "boost": 2}}},
                       {"wildcard": {'content': {"wildcard": search_regexp, "boost": 1}}}],
            "minimum_should_match": "50%"}}, size=10)
      ```

   5. 查询日志

      ```python
        def add_search_log(search_text, search_type):
            with open("search_log.json", 'r', encoding="utf-8") as file:  # 加载搜索历史
                search_log = json.load(file)
                file.close()
            with open("search_log.json", 'w+', encoding="utf-8") as file:  # 添加当前搜索到搜索历史
                search_log.append({"search_text": search_text, "search_type": search_type, "time": datetime.now().strftime("%Y:%m:%d:%H:%M:%S")})
                json.dump(search_log, file)
                file.close()
      ```

   6. 网页快照

      ```python
        def search_result_open(request):  # 在django的views中添加这个新的动作，添加网页快照的功能
            result_title = request.POST.get('result_title')
            result_content_all = request.POST.get('result_content_all')
            params = {"result_title": result_title, "result_content_all": result_content_all}
            return render(request, 'search/search_result_open.html', {'params': params})
      ```

5. 个性化服务

   记录用户打开的网页，添加到用户的浏览历史里，保存到一个json文件，下次查询搜索的这个网址会有相应的加分

   ```python
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
   ```

6. Web页面

   使用Django搭建网站，并搜索相关词语进行测试：

    ![image](https://github.com/BUGHERE/NkuSearchIt/assets/55886903/f9cbd492-c1d2-407c-bc14-5f3fecca3558)

    ![image](https://github.com/BUGHERE/NkuSearchIt/assets/55886903/93cf1939-da34-4744-9d67-9b91604df821)

    ![image](https://github.com/BUGHERE/NkuSearchIt/assets/55886903/5a1a933b-c192-4796-ac14-3fdc4ac19c7f)

