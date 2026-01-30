from lxml import html


def get_order_track_number_list(html_str: str):
    tree = html.fromstring(html_str)
    track_number_element_list = tree.xpath('//div[@class="pageContent"]//tbody/tr[@target="sid_serialid"]/td[4]/text()')
    track_number_list = []
    for track_number_element in track_number_element_list:
        track_number = track_number_element.strip()
        if track_number:
            track_number_list.append(track_number)
    return track_number_list


def get_order_page(html_str: str):
    tree = html.fromstring(html_str)
    return {
        'total': int(tree.xpath('//div[@class="pagination"]/@totalcount')[0]),
        'page_size': int(tree.xpath('//div[@class="pagination"]/@numperpage')[0])
    }
