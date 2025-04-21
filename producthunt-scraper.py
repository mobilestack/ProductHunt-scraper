#!/usr/bin/env python3.5

# Copyright (c) 2019 Fernando
# Url: https://github.com/fernandod1/
# License: MIT

from bs4 import BeautifulSoup
import requests
import re
import time
import xlwt 
from xlwt import Workbook


EXCEL_FILE = "sample.xls"
TOTALPOSTSTOGET = 50
FROM = 50
TRACK404 = 0 # not modify this var

# ---------------- Do not modify under this line ------------------------- #

def parse_html(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Connection': 'keep-alive',
    }
    html_doc = requests.get(url, headers=headers)
    soup = BeautifulSoup(html_doc.text, "html.parser")
    return soup

def scrap_all_posts_links(soup):
    all_links = []
    links=soup.find_all("a")
    for link in links:
        if "/posts/" in link.attrs['href']:
            if link.attrs['href'] not in all_links :
                all_links.append(str(link.attrs['href']))
    return all_links

def list_clean(txt):
    txt = txt.replace('["','')
    txt = txt.replace('"]','')
    txt = txt.split('","')
    return txt

def scrap_post_content(post_id, ii, sheet):
    global TRACK404
    post_data = {}
    try:
        soup0 = parse_html("https://www.producthunt.com/posts/"+str(post_id))
        soup = str(soup0)
        
        if "flagged for removal" in soup or "Page Not Found" in soup:
            print("Info: this post DOES NOT EXISTS") 
            TRACK404 += 1
            return
            
        # Initialize all fields with empty strings
        post_data.update({
            "title": "", "short_description": "", "categories": "",
            "logo": "", "images": "", "upvotes": "", "description": "",
            "postdate": "", "product_web": "", "badge": "", "badge_date": "",
            "reviews": "", "n_reviews": "", "hunter_url": "", "maker_url": "",
            "product_hunt_url": ""
        })
        
        # Basic metadata
        title = soup0.find("meta", property="og:title")
        if title:
            title_parts = title["content"].split(" - ")
            post_data["title"] = title_parts[0]
            if len(title_parts) > 1:
                desc_parts = title_parts[1].split("| ")
                post_data["short_description"] = desc_parts[0]
        
        # Product Hunt URL
        url = soup0.find("meta", property="og:url")
        if url:
            post_data["product_hunt_url"] = url["content"]
            
        # Hunter and Maker URLs
        hunter_urls = re.findall('<a class="card_(.*?)" href="/@(.*?)"><div class="userImage', soup)
        if hunter_urls:
            try:
                post_data["hunter_url"] = f"https://www.producthunt.com/@{hunter_urls[0][1]}"
                maker_urls = [f"https://www.producthunt.com/@{url[1]}" for url in hunter_urls[1:]]
                post_data["maker_url"] = ",".join(maker_urls)
            except IndexError:
                print("Info: Could not process hunter/maker URLs completely")
        
        # Rest of your existing data extraction code...
        
        print(f"{post_id} - {post_data['product_hunt_url']} -> DONE")
        pointer = ii - TRACK404
        fill_excel(post_data, pointer, sheet)
        
    except Exception as e:
        print(f"ERROR: {str(e)}")
        TRACK404 += 1


def get_first_post_link(soup):
    try:
        # Try multiple selectors to find posts
        selectors = [
            'a[href^="/posts/"]',  # Original selector
            'div[data-test="post-item"] a',  # New possible selector
            'div[class*="post"] a[href*="/posts/"]',  # Generic post selector
        ]
        
        for selector in selectors:
            links = soup.select(selector)
            if links:
                for link in links:
                    href = link.get('href')
                    if href and '/posts/' in href:
                        print(f"Found post link: {href}")
                        return href
        
        # If we get here, no links were found
        print("DEBUG: Page content snippet:")
        print(soup.prettify()[:500])  # Print first 500 chars of HTML for debugging
        raise Exception("No post links found")
        
    except Exception as e:
        print(f"Error finding post links: {str(e)}")
        return None

def get_post_ID(url):
    content=str(parse_html(url))
    idpost = re.search('post_id=(.*?)&amp;theme=light', content)
    if idpost is not None:
        id_post=idpost.group(1)   
    else:
        id_post=""
        print("ERROR: NOT POST ID FOUND.")
    return id_post

def fill_excel(d,i,sheet):    
    if i==0:
        style = xlwt.easyxf('font: bold 1')
        sheet.write(0, 0, 'Title', style) 
        sheet.write(0, 1, 'Short Description', style) 
        sheet.write(0, 2, 'Category', style) 
        sheet.write(0, 3, 'Logo URL', style) 
        sheet.write(0, 4, 'Gallery Image URLs', style) 
        sheet.write(0, 5, 'Upvote', style) 
        sheet.write(0, 6, 'description', style) 
        sheet.write(0, 7, 'Post Date', style) 
        sheet.write(0, 8, 'Product website URL', style) 
        sheet.write(0, 9, 'Badge', style) 
        sheet.write(0, 10, 'Badge Date', style) 
        sheet.write(0, 11, 'No. of reviews', style) 
        sheet.write(0, 12, 'Reviews', style) 
        sheet.write(0, 13, 'Hunter URL', style) 
        sheet.write(0, 14, 'Marker URL', style) 
        sheet.write(0, 15, 'Product Hunt URL', style)
    row = 1+i
    col = 0
    itemplus = ""
    for key in d.keys():
        for item in d[key]:
            itemplus=""+itemplus+""+item+""
        sheet.write(row, col, itemplus)
        itemplus = ""
        col += 1


try:
    # Initialize workbook first
    workbook = xlwt.Workbook()
    sheet = workbook.add_sheet("Sheet 1")

    soup = parse_html("https://www.producthunt.com/newest")
    first_link = get_first_post_link(soup)
    
    if not first_link:
        raise Exception("Could not find any posts to scrape")
        
    post_id = int(get_post_ID("https://www.producthunt.com"+first_link+"/embed"))
    if not post_id:
        raise Exception("Could not get post ID")

    i = 0
    if FROM > 0:
        post_id = post_id - FROM
    while i != TOTALPOSTSTOGET:
        try:
            print("-----------------------------------------------------")
            scrap_post_content(post_id, i, sheet)
            post_id = post_id - 1
            i = i + 1
            time.sleep(0.5)  # Increased delay to avoid rate limiting
        except Exception as e:
            print(f"Error processing post {post_id}: {str(e)}")
            post_id = post_id - 1
            continue

    workbook.save(EXCEL_FILE)
    print(f"Successfully saved {i} posts to {EXCEL_FILE}")

except Exception as e:
    print(f"ERROR: {str(e)}")
    try:
        workbook.save(EXCEL_FILE)
        print(f"Saved partial results to {EXCEL_FILE}")
    except:
        print("ERROR: Could not save workbook")




