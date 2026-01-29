import os
from code.utils.url import get_response
from code.spider.for_cvf import in_root_page, in_conf_page, in_home_page, in_item_page
from code.utils.file import my_abspath, read, write
import threading
import math


def parse_from_item_page(item_ls, i):
    """
        到对应的 item=item_ls[i] 中，访问 item["source_online"]["item_url"] 来获取相关信息，并补充至 item
    """
    item_url = item_ls[i]["source_online"]["item_url"]
    print(i, item_url)
    text = get_response(url=item_url)
    # 获取 abstract
    item_ls[i]["abstract"] = in_item_page.find_abstract(text)
    # 获取 paper_url
    item_ls[i]["source_online"]["paper_url"] = f'{root_url}/{in_item_page.find_paper(text)}'
    # 获取 authors
    item_ls[i]["authors"] = in_item_page.find_authors(text)


if __name__ == '__main__':
    # root
    root_url = "https://openaccess.thecvf.com"
    text = get_response(url=root_url)
    conference_ls = in_root_page.find_conferences(text)
    print(f"from root {root_url} \n"
          f"we get: conference_ls {conference_ls}")
    # conference_ls=conference_ls[7:]

    for conference in conference_ls:
        publisher = conference[:-4]
        year = conference[-4:]

        # conf
        conference_url = f"{root_url}/{conference}"
        text = get_response(url=conference_url)
        homepage_ls = in_conf_page.find_homepages(text, head=conference)
        if len(homepage_ls) == 0:
            homepage_ls = [conference]
        #
        print(f"from conference {publisher, year} \n"
              f"we get: homepage_ls {homepage_ls}")

        # home
        item_ls = []
        for homepage in homepage_ls:
            homepage_url = f"{root_url}/{homepage}"
            text = get_response(url=homepage_url)
            item_ls.extend(in_home_page.find_items(text))
        for item in item_ls:
            item["source_online"]["item_url"] = f'{root_url}/{item["source_online"]["item_url"]}'
        #
        temp = '\n'.join([f'{key}: {value}' for key, value in item_ls[0].items()])
        print(f"from homepage {homepage_ls} \n"
              f"we get: {len(item_ls)} items\n"
              f"for example one of them is:\n"
              f"{temp}")

        # item
        thread_nums = 400
        for i in range(math.ceil(len(item_ls) / thread_nums)):
            thread_ls = []
            for j in range(i * thread_nums, min((i + 1) * thread_nums, len(item_ls))):
                thread_ls.append(threading.Thread(target=parse_from_item_page, kwargs=dict(item_ls=item_ls, i=j)))
            for t in thread_ls:
                t.start()
            for t in thread_ls:
                t.join()

        # 补充 publisher year
        for item in item_ls:
            item["publisher"] = publisher
            item["year"] = year

        # 保存
        file_path = my_abspath(path=f"../../meta_data/{publisher}/{year}.json",
                               base=os.path.split(os.path.abspath(__file__))[0])
        os.makedirs(os.path.split(file_path)[0], exist_ok=True)
        write(path=file_path, content=item_ls, verbose=True)

        print(f"end --- {publisher} --- {root_url} --- {year}")
