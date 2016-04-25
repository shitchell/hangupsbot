import hangups

from hangupsbot.handlers import handler

import requests
import re

@handler.register(priority=7, event=hangups.ChatMessageEvent)
def _watch_image_link(bot, event):
    regex = re.compile(r'(http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+\.(png|jpe?g|webp|gif|crw|cr2|nef|dng|orf|raf|pef|srw|rw2|bmp|ico|tiff))')
    
    for image_link in regex.findall(event.text):
        image_link = image_link[0]
        
        print("Handling image", image_link)
        # Ignore other uploaded images
        if "googleusercontent.com" in image_link:
            print("Ignoring ", image_link)
            continue
        
        req = requests.head(image_link)
        print("Got head request", image_link)
        if req.ok:
            print("Got the OK", image_link)
            # Try to make sure we found an image
            if not req.headers.get("content-type", "").startswith("image"):
                return
            
            print("Uploading", image_link)
            image_id = yield from bot.upload_images([image_link])
            print("Uploaded", image_link)

            yield from event.conv.send_message([], image_id=image_id[0])
