#!/usr/bin/env python

import argparse
from selenium import webdriver
from selenium.webdriver.common.by import By
from PIL import Image
import requests
from io import BytesIO
import time
import numpy as np
import urllib.parse


def paraweb(url, channels=[True, False, False], local=False):
    
    driver = webdriver.Chrome()
    driver.get(url)

    time.sleep(2)

    # Locate the image with a width of 1024px using the updated Selenium API
    image_element = driver.find_element(By.XPATH, '//img')

    # Extract the image URL
    image_url = image_element.get_attribute('src')

    # Use requests to get the image content
    if not local:
        response = requests.get(image_url)
        image = Image.open(BytesIO(response.content))
    else:
        with Image.open(url) as file:
            image = file.load()
            width, height = file.size

    binary_messages = ["", "", ""]
    # Extract binary data from the image
    for y in range(height):
        for x in range(width):
            for channel in range(3):  # Assuming RGB channels
                if channels[channel]:
                    # Get the last two bits from each channel and add to the binary message
                    binary_messages[channel] += bin(image[x, y][channel])[2:].rjust(8, '0')[-2:]

    # TODO protect against bad utf (encountered in unencoded files)
    for channel in range(3):  # Assuming RGB channels
        if channels[channel]:
            # Extract the length of the actual message from the first 32 bits
            length_bits = binary_messages[channel][:32]
            message_length = int(length_bits, 2)  # Convert binary to int
            print(message_length)

            # Calculate the end index of the message bits, adjusting for the length prefix and bit repetition
            message_end_index = 32 + message_length * 2  # Each bit is doubled

            # Extract the message bits, taking every second bit to account for bit repetition
            actual_message_bits = binary_messages[channel][32:message_end_index:2]

            # Reconstruct the byte sequence from the binary data
            message_bytes = bytearray()
            for i in range(0, len(actual_message_bits), 8):
                byte = actual_message_bits[i:i+8]
                if len(byte) == 8:
                    message_bytes.append(int(byte, 2))

            # Decode the byte sequence back into a string using UTF-8
            message = message_bytes.decode('utf-8')
            #encoded_html = urllib.parse.quote(message)

            # driver.get(f"data:text/html,{encoded_html}")
            print(message)

    print("Press Enter to exit...")
    input()


def main():
    parser = argparse.ArgumentParser(description="Extract hidden messages from web pages")
    parser.add_argument("url", type=str, help="The URL of the web page with a Paraweb image.")
    args = parser.parse_args()

    paraweb(args.url, local=True)


if __name__ == "__main__":
    main()
