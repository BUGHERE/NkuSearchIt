import json
import os

dirname = "crawl_iteration_3"
with open(os.path.join(dirname + "_pr_results.json"), 'r', encoding="utf-8") as file:  # 加载pr结果
    page_rank_results = json.load(file)
    file.close()

for result in page_rank_results:
    page_rank_results[result] = 0

with open(os.path.join(dirname + "_url_open_history.json"), 'w', encoding="utf-8") as file:  # 加载pr结果
    json.dump(page_rank_results, file)
    file.close()


