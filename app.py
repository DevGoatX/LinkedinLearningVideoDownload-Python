import requests 

import os
from dotenv import load_dotenv
from selenium import webdriver

import asyncio
from selenium.webdriver.common.by import By

''' 
URL of the archive web-page which provides link to 
all video lectures. It would have been tiring to 
download each video manually. 
In this example, we first crawl the webpage to extract 
all the links and then download videos. 
'''
   
downloadFolder = 'download'
linkedInUrl = 'https://linkedin.com'
learningURLs = [
]
  
async def downloadVideo(videoLink, filePath):   
  
    '''iterate through all links in video_links 
    and download them one by one'''
        
    # obtain filename by splitting url and getting 
    # last string 
    # file_name = videoLink.split('/')[-1] 

    print( "Downloading file:%s"%filePath) 
        
    # create response object 
    r = requests.get(videoLink, stream = True) 
        
    # download started 
    with open(filePath, 'wb') as f: 
        for chunk in r.iter_content(chunk_size = 1024*1024): 
            if chunk: 
                f.write(chunk) 
        
    print( "%s downloaded!\n"%filePath )
  
    return

async def loginLinkedin(driver):
    load_dotenv()
    email = os.getenv('EMAIL')
    password = os.getenv('PASSWORD')

    driver.get(linkedInUrl)    
    print('linkedin opened')

    await asyncio.sleep(3)

    emailElement = driver.find_element(By.ID, 'session_key')
    emailElement.send_keys(email)
    print('session key inputed')

    pwdElement = driver.find_element(By.ID, 'session_password')
    pwdElement.send_keys(password)
    print('password inputed')

    pwdElement.submit()
    await asyncio.sleep(10)
    return

async def downloads(driver, title, navigation):
    print('section length: ', len(navigation))
    path = os.path.join(downloadFolder, title)
    try:
        os.mkdir(path)
    except:
        print("Already created directory - ", title)

    for section in navigation:
        path = os.path.join(downloadFolder, title, section["title"])
        print('directory: ', path)

        try:
            os.mkdir(path)
        except:
            print("Already created directory - ", section["title"])

        print('section item length: ', len(section["items"]))
        for item in section["items"]:
            print('title: ', item["title"])
            print('url: ', item["url"])
            driver.get(item["url"])

            await asyncio.sleep(2)
            videoURL = driver.find_element(By.TAG_NAME, 'video').get_attribute('src').replace('#.mp4', '')
            filePath = os.path.join(path, item["title"]) + '.mp4'

            print('video url: ', videoURL)
            print('file path: ', filePath)
            await downloadVideo(videoURL, filePath)
    return

def makeDownloadDirectory():
    try:
        os.mkdir(downloadFolder)
    except:
        print("Already created download directory")
    return

async def getDownloads():
    makeDownloadDirectory()
    
    driver = webdriver.Firefox()
    await loginLinkedin(driver)

    while "checkpoint" in driver.current_url:
        await asyncio.sleep(1)    
        
    for url in learningURLs:
        learningURL = url.replace('autoplay=true', 'autoplay=false')
        driver.get(learningURL)
        await asyncio.sleep(5)

        sections = driver.find_elements(By.CLASS_NAME, 'classroom-toc-section')
        while len(sections) == 0 or driver.current_url != learningURL:
            sections = driver.find_elements(By.CLASS_NAME, 'classroom-toc-section')    

        await asyncio.sleep(3)
        sections = driver.find_elements(By.CLASS_NAME, 'classroom-toc-section') 

        navigation = []    
        for i in range(len(sections) - 1):        
            section = { "title": "", "items": []}
            section.update({"title": sections[i].find_element(By.CLASS_NAME, 'classroom-toc-section__toggle-title').text.replace('\n', '').replace('/', ' ').strip()})
            
            itemElements = sections[i].find_elements(By.TAG_NAME, 'li')
            items = []
            j = 1
            for element in itemElements:
                item = {
                    "title": element.find_element(By.CLASS_NAME, 'classroom-toc-item__title').text.replace('\n', '').replace('/', ' ').replace('(In progress)', '').replace('?', '').replace('(Viewed)', '').strip(),
                    "url": element.find_element(By.TAG_NAME, 'a').get_attribute('href')
                }

                if item["title"] == 'Welcome' or item["title"] == 'Chapter Quiz':
                    continue
                
                if len(itemElements) > 9 and j < 10:
                    item["title"] = "0" + str(j) + ". " + item["title"]
                else:
                    item["title"] = str(j) + ". " + item["title"]

                items.append(item)
                j += 1
                

            section.update({"items": items})
            navigation.append(section)

        title = driver.find_element(By.CLASS_NAME, 'classroom-nav__title').text.replace('\n', '').replace('/', ' ').strip()
        print('Title: ', title)

        await downloads(driver, title, navigation)
    return
  
if __name__ == "__main__": 
    
    loop = asyncio.get_event_loop()
    loop.run_until_complete(getDownloads())
