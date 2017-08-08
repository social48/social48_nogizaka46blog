#-------------------------------------------------------------------------------
# Name:        social48_nogizaka46_blog
# Purpose:     archival of blog.nogizaka46.com pages
#
# Author:      wlerin
#
# Created:     13/01/2016
# Copyright:   (c) wlerin 2016
# Licence:     <your licence>
#-------------------------------------------------------------------------------

import json
import os
import urllib
import requests
from fake_useragent import UserAgent
from social48config import CONFIG
from time import sleep


ROOT_DIR = CONFIG['root_directory'] + "/services/nogizaka46-blog"

ua = UserAgent()
ua_header = ua.random

def build_nogi_index():
    starturl='http://blog.nogizaka46.com/hinako.kitano'
    baseurl = starturl.replace('/hinako.kitano', '')
    with open(os.path.normpath(CONFIG['root_directory'] + "/social48_index.json"), mode='r', encoding='utf8') as indexfp:
        master_index = json.load(indexfp)

    page = get_page_text(starturl, None)

    li = page.index('<div id="sidemember">')
    ri = page.index('<div class="unit2">', li) + len('<div class="unit2">')
    ri = page.index('</div>', ri) + len('</div>')
    page = page[li:ri]
    page = page.replace('<div id="sidemember"><h2>MEMBER</h2><div class="clearfix">', '').replace('<div class="unit2">', '\n<div class="unit2">')

    member_list = []
    for line in page.split('\n'):
        new_entry = {'blog':{}}
        if '<div class="unit' not in line:
            # skip over a couple useless lines
            continue
        elif '<div class="unit2">' in line:
            # deal with the staff page
            new_entry['blog']['webUrl'] = baseurl + '/staff'
            new_entry['blog']['apiId'] = 'staff'
            new_entry['blog']['active'] = True # assumption
            new_entry['blog']['service'] = 'nogizaka46-blog'
            new_entry['blog']['type'] = 'staff'
            new_entry['blog']['handle'] = 'nogistaff'
            new_entry['blog']['priority'] = 16
            new_entry['jpnName'] = '乃木坂46 運営'
            new_entry['engName'] = 'Nogizaka46 Staff'
            new_entry['jpnNameKana'] = ''
        elif 'kenkyusei' in line:
            # deal with kks blog
            li = line.index('<a href="..') + len('<a href="..')
            ri = line.index('"><img', li)
            new_entry['blog']['webUrl'] = baseurl + line[li:ri]
            new_entry['blog']['apiId'] = line[li:ri].replace('/', '')
            new_entry['blog']['active'] = True # assumption
            new_entry['blog']['service'] = 'nogizaka46-blog'
            new_entry['blog']['type'] = 'group'
            new_entry['blog']['handle'] = 'nogikenkyuusei'
            new_entry['blog']['priority'] = 16
            new_entry['jpnName'] = '乃木坂46 研究生'
            new_entry['engName'] = 'Nogizaka46 Kenkyuusei'
            new_entry['jpnNameKana'] = ''
        else:
            li = line.index('<a href="..') + len('<a href="..')
            ri = line.index('"><img', li)
            new_entry['blog']['webUrl'] = baseurl + line[li:ri]
            new_entry['blog']['apiId'] = line[li:ri].replace('/', '')
            new_entry['blog']['active'] = True # assumption
            new_entry['blog']['service'] = 'nogizaka46-blog'
            new_entry['blog']['type'] = 'individual'

            li = line.index('<span class="kanji">', ri) + len('<span class="kanji">')
            ri = line.index('</span', ri)
            new_entry['jpnName'] = line[li:ri].replace(' ', '')
            if new_entry['jpnName'] =='北野日奈子':
                new_entry['blog']['priority'] = 7
            else: new_entry['blog']['priority'] = 16
            li = line.index('<span class="sub">', ri) + len('<span class="sub">')
            ri = line.index('</span>', li)
            new_entry['jpnNameKana'] = line[li:ri].replace(' ', '')
            # look up jpnName
            found = [m for m in master_index['members'] if m['jpnName'] == new_entry['jpnName']]
            if len(found) > 0:
                if len(found) > 1:
                    print('Found multiple entries for {}'.format(new_entry['jpnName']))
                found = found[0]
                new_entry['blog']['handle'] = '-'.join(found['engName'].lower().split(' '))
                print('Adding blog {}'.format(new_entry['blog']['handle']))
                new_entry['engName'] = found['engName']
                found['accounts'].append(new_entry['blog'])
            else:
                print('Found no match for {}'.format(new_entry['jpnName']))
        member_list.append(new_entry)

    # todo: sort by post date
    with open(os.path.normpath(ROOT_DIR + "/nogizaka46-blog_index.json"), mode='w', encoding='utf8') as blogindexfp,\
         open(os.path.normpath(CONFIG['root_directory'] + "/social_CONFIGex.json"), mode='w', encoding='utf8') as masterindexfp:
            json.dump(master_index, masterindexfp, ensure_ascii=False, indent=2)
            json.dump(member_list, blogindexfp, ensure_ascii=False, indent=2)

    # url

    # japanese name
    # kana name

def get_page_text(srcurl, paramlist):
    attempts = 0
    max_attempts = 5

    while True:
        try:
            r = requests.get(srcurl, headers={'User-Agent': ua_header}, params=paramlist)
        except requests.exceptions.ConnectionError:
            if attempts < max_attempts:
                attempts += 1
                sleep(attempts*2)
            else:
                raise
        else:
            break

    # should be able to assume every page has the same encoding, but just to be safe
    li = r.text.find('encoding="') + len('encoding="')
    if li >= 0:
        ri = r.text.find('"', li)
    r.encoding = r.text[li:ri].lower()
    # print(r.url)
    if paramlist is not None and r.url.strip('/') == srcurl:
        print("Failed to locate {}?d={}".format(srcurl, paramlist['d']))
        return None
    else:
        return r.text

def get_archive_list(src):
    """
    Returns a list of monthly archive pages
    """
    li = src.index('<div id="sidearchives">')
    ri = src.index('</div>', li) + len('</div>')
    src = src[li:ri].replace('<option value="', '\n<option value="')

    archives = []
    for line in src.split('\n'):
        if 'http:' in line:
            li = line.index('/?d=') + len('/?d=')
            ri = line.index('">', li)
            archives.append(line[li:ri])
    return archives



def update_blog(member, bFull = False):
    destdir = os.path.normpath(ROOT_DIR + '/' + member['blog']['handle'])
    olddir = os.getcwd()
    os.makedirs(destdir, exist_ok=True)
    os.chdir(destdir)
    srcurl = member['blog']['webUrl']


    # open existing data
    posts_file = 'n46blog_{}.json'.format(member['blog']['handle'])
    if os.path.isfile(posts_file):
        with open(posts_file, mode='r', encoding='utf8') as infp:
            posts = json.load(infp)
    else:
        posts = []
        bFull = True

    old_count = len(posts)
    # todo: load existing data, check if blog has been updated since first run

    archives = get_archive_list(get_page_text(srcurl, None))
    

    for month in archives:
        src = get_page_text(srcurl, {"d": month})
        if src == None:
            break # target page redirected us to this member's first page

        li = src.find('<div class="paginate">')
        if li >= 0:
            ri = src.index('</div>', li)
            max_pages = src[li:ri].count('<a href')
        else:
            max_pages = 1

        for pageno in range(1,max_pages+1):
            dup_count = 0
            src = get_page_text(srcurl, {"p": pageno, "d": month})

            # find the start and end of the main blog, ignore the rest
            start = src.find('<div id="sheet">')
            end = src.find('<div class="left2 memberblog">')
            src = src[start:end]

            # read each post, starting at clearfix
            while '<h1 class="clearfix">' in src:
                start = src.index('<h1 class="clearfix">') + len('<h1 class="clearfix">')
                src = src[start:]
                # check if post exists already
                # get date and link from end of entry
                li = src.index('<div class="entrybottom">') + len('<div class="entrybottom">')
                ri = src.index('｜<a href="', li)
                postdate = src[li:ri].replace('/', '-')

                # check that post is not already in posts
                if len([e for e in posts if e['date'] == postdate]) > 0:
                    # print('Post for {} from {} already in database, skipping'.format(member['engName'], postdate))
                    dup_count +=1
                else:
                    posts.append(parse_post(src, member, postdate))
            if not bFull and dup_count > 2:
                break
        if not bFull and dup_count > 2:
            break
    
    count = len(posts) - old_count
    if count > 0:
        print("Found {} new blog posts for {}.".format(count, member['engName']))
    else:
        #print('No new posts for {}.'.format(member['engName']))
        pass
    with open(posts_file, mode='w', encoding='utf8') as outfp:
        json.dump(posts, outfp, ensure_ascii=False, indent=2)

    os.chdir(olddir)

def parse_post(src, member, postdate):
    new_post = {}

    new_post['date'] = postdate
    # get title and author from heading
    li = src.index('<span class="author">') + len('<span class="author">')
    ri = src.index('</span>', li)
    new_post['author'] = src[li:ri]

    # assume that the first url after clearfix (and author) will always be the post url
    # and that it is immediately followed by the title
    li = src.index('<a href="') + len('<a href="')
    ri = src.index('" rel=', li)
    new_post['url']  = src[li:ri]

    li = src.index('rel="bookmark">') + len('rel="bookmark">')
    ri = src.index('</a>', li)
    new_post['title'] = src[li:ri]
    if len(new_post['title']) == 0:
        new_post['title'] = 'Untitled'

    # entry body
    start = src.index('<div class="entrybody">')
    end = src.index('<div class="entrybottom">', start)
    # for now, just save the whole thing
    body = new_post['content'] = src[start:end]


    new_post['media'] = parse_media(body, postdate)

    return new_post

def parse_media(body, postdate):
    media_list = []
    # body = source
    imgcount = 0

    # deal with different image hosts
    # http://dcimg.awalker.jp/img1.php
    # http://img.nogizaka46.com/blog/kana.nakada/img/2016/01/10/3003013/0004.jpeg
    # unfortunately there's no way to distinguish real photos from retarded emotes... except by extension
    # nogizaka hosted large images consistently end with .jpeg
    # while the small ret images end with .gif
    body = body.replace('\n', '').replace('</div>', '</div>\n').replace('</blockquote>', '</blockquote>\n').replace(' />', '>').replace('</span>', '</span>\n').split('\n')
    for line in body:
        if '.jpeg' in line or '.jpg' in line or '.png' in line:
            new_img = {}
            imgcount+=1
            if '.jpeg' in line:
                ext = '.jpg'
            elif '.jpg' in line:
                ext = '.jpg'
            elif '.png' in line:
                ext = '.png'

            destfilename = os.path.normpath('{}/{}_{}.jpg'.format(postdate[:7], postdate.replace(':', ''), imgcount))

            # awalker hosted image
            if 'dcimg.awalker.jp' in line:
                thumbfilename = os.path.normpath('{}/thumbs/th_{}_{}.jpg'.format(postdate[:7], postdate.replace(':', ''), imgcount))
                os.makedirs(os.path.normpath(postdate[:7] + '/thumbs'), exist_ok=True)

                start = line.index("http://dcimg.awalker.jp")
                end = line.index('"', start)
                new_img['url'] = line[start:end]

                # get image
                s = requests.Session()
                r = s.get(new_img['url']) # get the outer url
                if '/img/expired.gif' in r.text:
                    new_img['file'] = 'expired'
                else:
                    r = s.get(new_img['url'].replace('http://dcimg.awalker.jp/img1.php?id=', 'http://dcimg.awalker.jp/img2.php?sec_key=')) # get the real image
                    if r.status_code == requests.codes.ok:
                        with open(destfilename, 'wb') as outfp:
                            new_img['size'] = outfp.write(r.content)
                    new_img['file'] = destfilename

                bThumbFound = False
                # save thumbnail
                if 'http://img.nogizaka46' in line:
                    start = line.index('http://img.nogizaka46')
                    bThumbFound = True
                elif 'http://blog.nogizaka46' in line:
                    start = line.index('http://blog.nogizaka46')
                    bThumbFound = True
                else:
                    new_img['thumbnail'] = None
                if bThumbFound:
                    end = line.index('"', start)
                    thumburl = line[start:end]
                    try:
                        urllib.request.urlretrieve(thumburl, thumbfilename)
                    except Exception as e:
                        new_img['thumbnail'] = None
                        print('Read of {} failed with error: {}'.format(thumburl, e))
                    else:
                        # strip the root directory from the file name
                        new_img['thumbnail'] = thumbfilename
            elif 'img.nogizaka46' in line:
                os.makedirs(postdate[:7], exist_ok=True)

                start = line.index('http://img.nogizaka46.com')
                end = line.index('"', start)
                new_img['url'] = line[start:end]

                try:
                    urllib.request.urlretrieve(new_img['url'], destfilename)
                except urllib.error.HTTPError as e:
                    new_img['file'] = None
                    print('Read of {} failed with error: {}'.format(new_img['url'], e))
                else:
                    new_img['thumbnail'] = new_img['file'] = destfilename

            else:
                print('Found unknown image, printing context:')
                print(line)

            if len(new_img) > 0:
                media_list.append(new_img)

    # checks?
    return media_list


def main():
    # account_list = [{"engName":"Kitano Hinako", "jpnName": "北野日奈子", "apiId": "hinako.kitano", "url":"http://blog.nogizaka46.com/hinako.kitano/", "handle":"kitano-hinako"}]
    with open(os.path.normpath(ROOT_DIR + "/nogizaka46-blog_index.json"), mode='r', encoding='utf8') as indexfp:
        index = json.load(indexfp)
    '''
    target = [e for e in index if e['engName'] == 'Kitano Hinako'][0]
    replace_lost_images(target)
    '''

    for member in index:
        try:
            if member['blog']['active']:
                update_blog(member)
        except requests.exceptions.ConnectionError:
            print('Failed to read {}\'s blog, skipping'.format(member['engName']))
            sleep(5)
        except ValueError as e:
            print('Failed to get archives for {}: {}'.format(member['engName'], e))
        else:
            # print('Finished updating {}\'s blog, sleeping for 20 seconds.'.format(member['engName']))
            sleep(10)


if __name__ == '__main__':
    main()

def replace_lost_images(member):
    """
    If the specified member has images (such as from dcimg.awalker) that have expired, attempts to locate other copies of them online.
    Possible methods:
        search logsoku member threads (probably requires special rules for each member though :/)
        ask google image search (first upload to puush, then go from there)
    Right now only searching logsoku is (being) implemented
    """
    from bs4 import BeautifulSoup
    destdir = os.path.normpath(ROOT_DIR + '/' + member['blog']['handle'])
    olddir = os.getcwd()
    os.chdir(destdir)

    # open existing data
    posts_file = 'n46blog_{}.json'.format(member['blog']['handle'])
    with open(posts_file, mode='r', encoding='utf8') as infp:
        posts = json.load(infp)

    # sort posts oldest to newest
    posts = sorted(posts, key=lambda e: e['date'])
    earliest = posts[0]['date']
    # first, logsoku
    search_term = member['jpnName'] + "応援スレ"
    sort_order = 'asc'
    search_url = "http://www.logsoku.com/search"
    paramlist = {'q': search_term, 'order':sort_order}

    # if I later add a better library, update
    html_lib = "html5lib"
    soup = BeautifulSoup(get_page_text(search_url, paramlist), html_lib)

    # todo: check for more than one page
    results = soup.tbody.extract().select('tr')

    base_url = 'http://www.logsoku.com'
    boards = ('地下アイドル', '乃木坂46')
    search_list = []
    for page in results:
        # check that it is located on a valid board
        if page.select('td.board')[0].get_text() not in boards:
            continue # unrecognized board, skip
        thread_date = page.select('td.date')[0].get_text().strip()
        thread_responses = page.select('td.length')[0].get_text() # this will be a number
        thread_title = page.select('td.title')[0].get_text().strip()
        thread_url = page.select('a.thread')[0]['href']
        search_list.append({'date':thread_date, 'responses':thread_responses, 'title':thread_title, 'url':thread_url})

    # right so basically, load the existing post data
    # get posts that roughly match the thread date
    # find any images in the thread
    # download them to a temp folder
    # compare the images against existing thumbnails for this date range
    # maybe make educated guesses if there's a source link

    # looking manually, kiichan's first thread has nothing on her blog...
    # in fact we can do some very basic elimination right from the start:
    # date is the date of the last post, so discard any threads
    # whose date is before her first post
    temp = []
    for page in search_list:
        if page['date'] >= earliest:
            temp.append(page.copy())
    search_list = temp

    # note that there's a bunch of stuff in some of the earlier threads
    # from before she had her own personal blog
    # but that's not what this function is for



