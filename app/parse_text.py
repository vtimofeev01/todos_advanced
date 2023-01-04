import re
from pprint import pprint
from datetime import date

G_REGEX_2 = re.compile(r"@(?<!\d)(?:0?[1-9]|[12][0-9]|3[01])[.|-](?:0?[1-9]|1[0-2])[.|-](?:19[0-9][0-9]|20[0123][0-9])(?!\d)")
G_HMS= re.compile(r"@(?P<D>\d+)[.|-](?P<M>\d+)[.|-](?P<Y>\d+)")
TAG_REGEX = re.compile(r"##[А-Яа-яЁё a-zA-Z0-9№.\-_]*#")
TAG_REGEX2 = re.compile(r"\[[А-Яа-яЁё a-zA-Z0-9№.\-_]*\]")
TAG_REGEX3 = re.compile(r"\%\%[А-Яа-яЁё a-zA-Z0-9№.\-_]*\%")

SPAN_TAG_REGEX = re.compile(r'<span class="tag"[\w="]*\>(?P<tag>[А-Яа-яЁё a-zA-Z0-9№.\-_\*\"\']+)<\/span>')

TAG_STARTS = ('##', '[', '%%')
TAG_FINISHES = ("# ", ']', '% ')
TAG_OPEN = '<span class="tag">'
TAG_CLOSE = '</span>'

def extract_tags(s):
    return SPAN_TAG_REGEX.findall(s)
def msg_mark(s: str):
    s1 = s + " "
    for tag in TAG_STARTS:
        s1 = s1.replace(tag, TAG_OPEN)
    for tag in TAG_FINISHES:
        s1 = s1.replace(tag, TAG_CLOSE)
    return s1

def msg_unmark(s:str):
    s1 = s.replace(TAG_OPEN, '[')
    s1 = s1.replace(TAG_CLOSE, ']')
    return s1



def msg_parse(s: str):
    out = dict()
    #     find goal
    # out['s'] = s
    print(f'[PARSE] <{s}>')
    t_goal = G_REGEX_2.findall(s)
    if len(t_goal):
        mo = G_HMS.match(t_goal[0])
        out['goal'] = date(int(mo.group('Y')), int(mo.group('M')), int(mo.group('D')))

    #     find tag
    out['tags'] = re.findall(TAG_REGEX, s)
    out['tags'] += re.findall(TAG_REGEX2, s)
    out['tags'] += re.findall(TAG_REGEX3, s)

    # TODO Mark tags

    for k, v in out.items():
        print(f"  - {k:5}:[{type(v)}] {v}")
    return out


if __name__ == "__main__":
    msgs = ["Выполнить контракт ##01-14 от 16.01.2001# @12.11.2011",
         "Выполнить контракт ##01-14 от 16.01.2001# 12.11.2011",
         "Выполнить контракт ##01-14 от 16.01.2001 12.11.2011"]

    for m in msgs:
        print(f'[{m}]')
        pprint(msg_parse(m))
