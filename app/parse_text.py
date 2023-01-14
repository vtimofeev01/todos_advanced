import re
from datetime import date
from pprint import pprint
from collections import namedtuple

G_REGEX_2 = re.compile(
    r"@(?<!\d)(?:0?[1-9]|[12][0-9]|3[01])[.|-](?:0?[1-9]|1[0-2])[.|-](?:19[0-9][0-9]|20[0123][0-9])(?!\d)")
TAG_REGEX = re.compile(r"\#\#([А-Яа-яЁё a-zA-Z0-9№.\-_]*)\#")
TAG_REGEX2 = re.compile(r"\[([А-Яа-яЁё a-zA-Z0-9№.\-_]*)\]")
TAG_REGEX3 = re.compile(r"\%\%([А-Яа-яЁё a-zA-Z0-9№.\-_]*)\%")
TAG_REGEX4 = re.compile(r'<span class="tag">([А-Яа-яЁё a-zA-Z0-9№.\-_]*)</span>')
TAG_TO_MARK = r'<b>\1</b>'

TAG_URL = re.compile(r'(https?:\/\/|www)([a-zA-Z0-9а-яА-Я\.\-_]{1,256}\.[a-zA-Z0-9а-яА-Я]{1,9}[a-zA-Z0-9\/\\\?\#=_\-\!\"\$\%\&\'\(\)\*\+\,\.\:\;\<\>\?\@\]\^\`\{\|\}\~]*)')
TAG_TO_URL_GOAL = '<a href="\g<0>"> www </a>'

TAG_GOAL1 = re.compile(
    r' @((?<!\d)(?:0?[1-9]|[12][0-9]|3[01])[.|-](?:0?[1-9]|1[0-2])[.|-](?:19[0-9][0-9]|20[0123][0-9])(?!\d))')
TAG_GOAL2 = re.compile(
    r' срок ((?<!\d)(?:0?[1-9]|[12][0-9]|3[01])[.|-](?:0?[1-9]|1[0-2])[.|-](?:19[0-9][0-9]|20[0123][0-9])(?!\d))')
TOG_TO_GOAL = r" до \1"

TAG_LINE_BREAK = re.compile('\n')
TAG_TO_LINE_BREAK = '<br>'

TagCode = namedtuple('TagCode', "tag code")

CONVERT_DICT_DIRECT = {
    # LABELS
    TAG_REGEX: TagCode(TAG_TO_MARK, None),
    TAG_REGEX2: TagCode(TAG_TO_MARK, None),
    TAG_REGEX3: TagCode(TAG_TO_MARK, None),
    TAG_REGEX4: TagCode(TAG_TO_MARK, None),
    # URL
    # TAG_URL: TagCode(TAG_TO_URL_GOAL, None),
    # GOAL
    TAG_GOAL1: TagCode(TOG_TO_GOAL, 'goal'),
    TAG_GOAL2: TagCode(TOG_TO_GOAL, 'goal'),

    # TAG_LINE_BREAK: TagCode(TAG_TO_LINE_BREAK, None)
}


def msg_mark(row_s: str, analytics=None):
    s1 = row_s[:]
    for rule, (pattern, code) in CONVERT_DICT_DIRECT.items():
        s1 = rule.sub(pattern, s1)
    return s1



R_TAG_EOS = '<br>'
P_TAG_EOS = '\n'
R_TAG_TAG = re.compile(r'<span class="tag">([^<]*)<\/span>')
P_TAG_TAG = r'[\1]'

R_TAG_HREF = re.compile(r'<a href="([^ ]*)"> link <\/a>')
R_TAG_HREF2 = re.compile(r'<a href="([^ ]*)"> www <\/a>')
P_TAG_HREF = r"\1"

def msg_unmark(row_s: str):
    s1 = R_TAG_HREF.sub(P_TAG_HREF, row_s)
    s1 = R_TAG_HREF2.sub(P_TAG_HREF, s1)
    s1 = R_TAG_TAG.sub(P_TAG_TAG, s1)
    s1 = s1.replace(R_TAG_EOS, P_TAG_EOS)
    return s1

SPAN_TAG_REGEX = re.compile(r'<span class="tag"[\w="]*\>(?P<tag>[А-Яа-яЁё a-zA-Z0-9№.\-_\*\"\']+)<\/span>')
SPAN_TAG_REGEX2 = re.compile(r'<b>(?P<tag>[^\<\>])<\/b>')
SPAN_TAG_REGEX3 = re.compile(r'<strong>[А-Яа-яЁё a-zA-Z0-9№.\-_\*\"\']+<\/strong>')

def extract_tags(s):
    return SPAN_TAG_REGEX.findall(s) + SPAN_TAG_REGEX2.findall(s)


G_REGEX_DO = re.compile(
    r"до (?<!\d)(?:0?[1-9]|[12][0-9]|3[01])[.|-](?:0?[1-9]|1[0-2])[.|-](?:19[0-9][0-9]|20[0123][0-9])(?!\d)")
G_HMS = re.compile(r"до (?P<D>\d+)[.|-](?P<M>\d+)[.|-](?P<Y>\d+)")


def msg_parse(s: str):
    out = dict()
    # print(f'[PARSE] <{s}>')
    t_goal = G_REGEX_DO.findall(s)
    # print(f'[PARSE] <{t_goal}>')
    if len(t_goal):
        mo = G_HMS.match(t_goal[0])
        out['goal'] = date(int(mo.group('Y')), int(mo.group('M')), int(mo.group('D')))
    return out


if __name__ == "__main__":
    msgs = ["Выполнить контракт ##01-14 от 16.01.2001# @12.11.2011",
            "Выполнить контракт ##01-14 от 16.01.2001# 12.11.2011",
            "Выполнить контракт ##01-14 от 16.01.2001 12.11.2011"]

    for m in msgs:
        print(f'[{m}]')
        pprint(msg_parse(m))
