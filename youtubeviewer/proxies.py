"""
MIT License

Copyright (c) 2021-2023 MShawon

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""
import sys
from random import shuffle

import requests

from .colors import *


def gather_proxy():
    proxies = []
    print(bcolors.OKGREEN + 'Scraping proxies ...' + bcolors.ENDC)

    link_list = ['https://proxy.webshare.io/api/v2/proxy/list/download/tyaysfmzmufgwhwpdialgvsswkbeifmetzledige/-/any/sourceip/direct/-/']

    for link in link_list:
        try:
            response = requests.get(link, timeout=20)
            if response.status_code == 200:
                output = response.content.decode('utf-8', errors='ignore')

                if '\r\n' in output:
                    proxy = output.split('\r\n')
                else:
                    proxy = output.split('\n')

                # Clean and validate proxies
                for lines in proxy:
                    if lines.strip():  # Skip empty lines
                        # Basic proxy format validation
                        if ':' in lines:
                            try:
                                ip, port = lines.split(':')[:2]
                                # Basic IP validation
                                if ip.count('.') == 3 and all(0 <= int(i) <= 255 for i in ip.split('.')):
                                    if 0 <= int(port) <= 65535:  # Valid port range
                                        proxies.append(lines.strip())
                            except:
                                continue

                print(bcolors.BOLD + f'{len(proxy)}' + bcolors.OKBLUE +
                      ' proxies gathered from ' + bcolors.OKCYAN + f'{link}' + bcolors.ENDC)
        except Exception as e:
            print(bcolors.FAIL + f'Error gathering from {link}: {str(e)}' + bcolors.ENDC)
            continue

    proxies = list(set(filter(None, proxies)))  # Remove duplicates and empty entries
    shuffle(proxies)

    return proxies


def load_proxy(filename):
    proxies = []

    if not os.path.isfile(filename) and filename[-4:] != '.txt':
        filename = f'{filename}.txt'

    try:
        with open(filename, encoding="utf-8") as fh:
            loaded = [x.strip() for x in fh if x.strip() != '']
    except Exception as e:
        print(bcolors.FAIL + str(e) + bcolors.ENDC)
        input('')
        sys.exit()

    for lines in loaded:
        try:
            if lines.count(':') == 3:
                # Handle username:password@ip:port format
                split = lines.split(':')
                lines = f'{split[2]}:{split[-1]}@{split[0]}:{split[1]}'
            elif lines.count(':') == 1:
                # Validate ip:port format
                ip, port = lines.split(':')
                if ip.count('.') == 3 and all(0 <= int(i) <= 255 for i in ip.split('.')) and 0 <= int(port) <= 65535:
                    proxies.append(lines)
                continue
            proxies.append(lines)
        except:
            continue

    proxies = list(set(filter(None, proxies)))  # Remove duplicates and empty entries
    shuffle(proxies)

    if not proxies:
        print(bcolors.FAIL + 'No valid proxies found in file!' + bcolors.ENDC)
        input('')
        sys.exit()

    return proxies


def scrape_api(link):
    proxies = []

    try:
        response = requests.get(link)
        output = response.content.decode()
    except Exception as e:
        print(bcolors.FAIL + str(e) + bcolors.ENDC)
        input('')
        sys.exit()

    if '\r\n' in output:
        proxy = output.split('\r\n')
    else:
        proxy = output.split('\n')

    for lines in proxy:
        if lines.count(':') == 3:
            split = lines.split(':')
            lines = f'{split[2]}:{split[-1]}@{split[0]}:{split[1]}'
        proxies.append(lines)

    proxies = list(filter(None, proxies))
    shuffle(proxies)

    return proxies


def check_proxy(category, agent, proxy, proxy_type):
    if category == 'f':
        headers = {
            'User-Agent': f'{agent}',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }

        proxy_dict = {
            "http": f"{proxy_type}://{proxy}",
            "https": f"{proxy_type}://{proxy}",
        }

        try:
            # Simple connection test first
            test_urls = [
                'https://www.google.com',
                'https://www.youtube.com',
                'https://www.cloudflare.com'
            ]
            
            for url in test_urls:
                try:
                    response = requests.get(url, 
                                         headers=headers, 
                                         proxies=proxy_dict, 
                                         timeout=10,
                                         allow_redirects=True,
                                         verify=False)
                    
                    if response.status_code == 200:
                        # If we get a successful response from any test URL, consider the proxy good
                        return 200
                except:
                    continue
            
            # If we get here, none of the test URLs worked
            return 404
            
        except Exception as e:
            print(f"Proxy check error: {str(e)}")
            return 500
    else:
        return 200