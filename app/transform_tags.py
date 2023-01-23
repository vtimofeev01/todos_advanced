import re

re_tags = re.compile(r'<(?P<open_tag>[^\/][^ ]*)?(?P<attrib>[^>]*)>(?P<body>[^<]*)<\/(?P<end_tag>[^<]*)>')
re_mail = re.compile(r'^[\w-]+@([\w-]+\.)+[\w-]{2,8}')

if __name__ == '__main__':
    test_str = 'жОПА КАКАЯ-ТО НО ТОЖЕ ВАЖНО </td> <td class="assigned">Центр согласование</td>  <td class="goal_at is_near">21.1.23</td>  <td class="finished_at"> <a href="/set_todo_done/1/74/">&check; </a>  </td>'
    print(f'findall/ {re_tags.findall(test_str)}')
    print(f'split/ {re_tags.split(test_str)}')
    print(f'search/ {re_tags.search(test_str).groupdict()}')
    print(f'search/ {re_tags.finditer(test_str)}')
    print(f'search/ {re_tags.search(test_str)}')
    print(f'search/ {re_tags.match(test_str)}')

