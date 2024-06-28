#!/usr/bin/env python

import feedparser
import json
import urllib
import re
import os
import shutil
import errno
import time
from BeautifulSoup import BeautifulSoup


def create_directory(path):
    try:
        os.makedirs(path)
        print "[+] Creating directory " + path
    except OSError as exception:
        if exception.errno != errno.EEXIST:
            raise


def get_feed_urls_from_file(path):
    with open(path) as f:
        lost_of_feed_urls = f.read().splitlines()
        return lost_of_feed_urls 


def convert_from_unicode(input):
    if isinstance(input, dict):
        return {convert_from_unicode(key): convert_from_unicode(value) for key, value in input.iteritems()}
    elif isinstance(input, list):
        return [convert_from_unicode(element) for element in input]
    elif isinstance(input, unicode):
        return input.encode('utf-8')
    else:
        return input


def get_feed_metadata(feed_url):
    unicode_feed = feedparser.parse(feed_url)
    feed = convert_from_unicode(unicode_feed)
    feed_metadata = {
                      'title': feed['feed']['title'],
                      'subtitle': feed['feed']['subtitle'],
                      'link': feed['feed']['link'],
                      'n_entries': len(feed['entries']),
                      'headers': feed['headers'],
                      'last_updated': time.mktime(feed['feed']['updated_parsed'])
                     }
    entries = []
    for index, entry in enumerate(feed['entries']): 
        if 'updated_parsed' in entry:  
            t = time.mktime(feed['entries'][index]['updated_parsed'])
            entries.append({'last_updated': t, 'title': entry['title']})
        else:
            entries.append({'last_updated': 0, 'title': entry['title']})
      
    feed_metadata['entries'] = entries       
                                                  
    return feed, feed_metadata
    

def write_json_file(data, path):
    with open(path, 'w') as f:
        json.dump(data, f)  


def read_json_file(path):
    with open(path, 'r') as f:
        return json.load(f)  


def get_feed_image(feed, feed_directory):
    if("image" in feed['feed']):
        feed_image_url = str(feed['feed']['image']['href'])
        feed_image_path = feed_directory + feed_image_url.split('/')[-1]
        try:
            urllib.urlretrieve(feed_image_url, feed_image_path)
        except OSError as exception:
            if exception.errno != errno.EEXIST:
                raise
                

def download_entry_images(entry_directory, entry_soup, feed_url):
    image_extensions = ['jpg', 'jpeg', 'png', 'gif']
    
    entry_image_directory = entry_directory + "images/"
    create_directory(entry_image_directory)     
    
    entry_image_list = entry_soup.findAll('img')
    
    for image_index, image in enumerate(entry_image_list):
        image_url = str(image.get('src'))
        
        if "http" not in image_url:
            feed_url_base = feed_url.split(feed_url.split("/")[-1])[0]
            image_url = feed_url_base + image_url       
            
        extension = str(image_url).split('/')[-1].split('.')[-1]
        
        if extension in image_extensions:
            image_path = entry_image_directory + "image_" + str(image_index) + "." + extension 
            try:
                print "[+] Downloading " + image_url + " --> " + image_path 
                urllib.urlretrieve(image_url, image_path)
            except OSError as exception:
                if exception.errno != errno.EEXIST:
                    raise


def get_visible_text(element):
    if element.parent.name in ['style', 'script', '[document]', 'head', 'title']:
        return ''
    result = re.sub('<!--.*-->|\r|\n', '', str(element), flags=re.DOTALL)
    result = re.sub('\s{2,}|&nbsp;', ' ', result)
    return result


def get_entry_text(entry_soup):
    texts = entry_soup.findAll(text=True)   
    
    visible_elements = [get_visible_text(elem) for elem in texts]
    visible_text = ''.join(visible_elements)
    return visible_text
    

def parse_entry(entry, entry_directory):
    create_directory(entry_directory)
 
    entry_url = str(entry['link'])
    entry_data = urllib.urlopen(entry_url).read()
    entry_soup = BeautifulSoup(entry_data)

    download_entry_images(entry_directory, entry_soup, feed_url)            

#    for link_index, link in enumerate(entry_soup.findAll('a')):
#        print(link.get('href'))

    entry_text = get_entry_text(entry_soup)  
    entry_text_file = entry_directory + "text.txt"
        
    f = open(entry_text_file,'w')
    f.write(entry_text)
    f.close()


def get_entry_times(new_feed, old_feed=None):
    entry_times = []
    
    if old_feed == None:
    
        for entry in new_feed['entries']:
            if 'updated_parsed' in entry:
                t = time.mktime(entry['updated_parsed'])
                entry_times.append({'last_updated': t, 'title': entry['title']})
            else:
                entry_times.append({'last_updated': 0, 'title': entry['title']})
    
    else:
           
        for entry in old_feed['entries']:
            entry_times.append({'last_updated': entry['last_updated'], 'title': entry['title']})  
             
        entry_times.sort()   
        
        for entry in new_feed['entries']:
            if 'updated_parsed' in entry:
                t = time.mktime(entry['updated_parsed'])
                entry_times.append({'last_updated': t, 'title': entry['title']})
            else:
                entry_times.append({'last_updated': 0, 'title': entry['title']})
           
    entry_times.sort(reverse=True) 
    return entry_times



def parse_feed(feed_url):
    old_feed = 0

    # Get the feed's metadata.
    feed, feed_metadata = get_feed_metadata(feed_url)
    
    # Create a directory for this feed, if one doesn't exist aready.
    feed_directory = feed_metadata['title'].replace (" ", "_") + "/"   
    
    if not os.path.exists(feed_directory):
        create_directory(feed_directory)
    
    update_feed = False
    feed_metadata_path = feed_directory + "feed.json"    
        
    # Is there isn't a feed_x.json file then update.
    if not os.path.isfile(feed_metadata_path):
        update_feed = True
        print "[+] Feed has not been downloaded previously."
        
    # If there is a feed_x.json file, only update if the feed
    # has been changed since the last time we checked.
    else:        
        # Get last update as seconds since last epoch
        feed_updated_at = time.mktime(feed['feed']['updated_parsed'])

        # Get existing last update as seconds since last epoch
        old_feed = read_json_file(feed_metadata_path)
        old_feed = convert_from_unicode(old_feed)
        old_feed_updated_at = old_feed['last_updated'] 
        
        if feed_updated_at > old_feed_updated_at:
            update_feed = True
            print "[+] Feed '" + feed['feed']['title'] + "' is out of date."
        else:
            print "[+] Feed '" + feed['feed']['title'] + "' is up-to-date."
    
    # Update the feed if necessary.
    if update_feed:   
        write_json_file(feed_metadata, feed_metadata_path)
        get_feed_image(feed, feed_directory)    

        # If we have existing feed data then compare against what
        # we already have.        
        if old_feed != 0:
            entry_times = get_entry_times(feed, old_feed) 
            cutoff = min(len(entry_times), 9)
            oldest_time = entry_times[cutoff]['last_updated']                
            print "Oldest entry post posted at " + str(oldest_time) 
            n = 0
        
            for entry in feed['entries']:
                if 'updated_parsed' in entry:
                    t = time.mktime(entry['updated_parsed'])
                else:
                    t = 0
            
                entry_directory = feed_directory + entry['title'].replace (" ", "_") + "/"
               
                # Get entry if its in the top 10 most recent    
                if (t > oldest_time) or (n < 10):
                
                    # AND if we don't already have it.
                    if not os.path.exists(entry_directory):
                        print "[+] Found new entry posted at " + str(t)
                        parse_entry(entry, entry_directory)
                        n += 1              
                
                # Otherwise delete it if we already have it
                elif (t > oldest_time) and os.path.exists(entry_directory):
                    print "[+] Deleting directory " + entry_directory
                    shutil.rmtree(entry_directory)
                    
        # Otherwise just get the 10 most recent.
        else:
            entry_times = get_entry_times(feed)               
            cutoff = min(len(entry_times), 9)
            oldest_time = entry_times[cutoff]['last_updated']
            n = 0
        
            for entry in feed['entries']:

                if 'updated_parsed' in entry:
                    t = time.mktime(entry['updated_parsed'])
                else:
                    t = 0
               
                # Get entry if its in the top 10 most recent    
                if (t > oldest_time) or (n < 10):
                    print "[+] Found new entry posted at " + str(t)
                    entry_directory = feed_directory + entry['title'].replace (" ", "_") + "/" 
                    parse_entry(entry, entry_directory)
                    n += 1
               

if __name__ == "__main__":
    feeds_file = "feed_list.txt"

    list_of_feed_urls = get_feed_urls_from_file(feeds_file)       

    for feed_url in list_of_feed_urls:
        parse_feed(feed_url)
        
            

