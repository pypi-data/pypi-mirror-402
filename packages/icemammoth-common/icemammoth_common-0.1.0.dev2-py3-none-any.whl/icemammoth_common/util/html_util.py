# -*- coding: utf-8 -*-

from bs4 import BeautifulSoup

def fetchImageSrcs(html) -> list[str]:
    soup = BeautifulSoup(html, "lxml")
    # Find all images element using find_all()
    images = soup.find_all("img")
    return [
        image.get('src')
        for image in images
    ]

def replaceImageSrc(html,oriSrc,destSrc) -> str:
    soup = BeautifulSoup(html, "lxml")
    # Find all images element using find_all()
    images = soup.find_all("img")
    for image in images:
        if image.get('src') == oriSrc:
            image['src'] = destSrc
    return soup.prettify()

def removeImageBySrc(html,src) -> str:
    soup = BeautifulSoup(html, "lxml")
    # Find all images element using find_all()
    images = soup.find_all("img")
    for image in images:
        if image.get('src') == src:
            image.replace_with()
    return soup.prettify()

