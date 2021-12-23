from colorama import Fore
from colorama import init
from os import system
import threading, requests, time, os, re

init(convert=True) if os.name == 'nt' else init()


website = 'https://yoursite.com'
start_year = 2021

threads = 1
max_attempts = 25


pages = []
pages_downloaded = []

pages_error = []

headers = {
	'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/95.0.4638.69 Safari/537.36 OPR/81.0.4196.61'
}

def download_url(file_url, timestamp, attempts=0):

    if attempts > max_attempts:
        raise TimeoutError('Unable to download file, max attempts reached.')

    try:
        
        url = "http://web.archive.org/web/" + timestamp + "id_/" + file_url
        print(Fore.CYAN + 'Downloading' + Fore.YELLOW, file_url, Fore.CYAN + '@' + Fore.YELLOW, timestamp)

        req = requests.get(url, headers=headers, stream=True)

        url = file_url.replace('http://', '')
        directory = './websites/' + re.sub('[^0-9a-zA-Z/\-\.]+', '_', url)
        
        os.makedirs(os.path.dirname(directory), exist_ok=True)
        
        with open(directory, 'wb') as f:
            for chunk in req.iter_content(chunk_size=1024):
                if chunk:
                    f.write(chunk)

        file = open(directory + '.url.txt', 'w')
        file.write(file_url)
        file.close()

        pages_downloaded.append(file_url)
        
        print(Fore.CYAN + 'Successfully downloaded file' + Fore.GREEN, url)
        return url

    except Exception as e:
        print(Fore.YELLOW + 'Unable to download', Fore.RED + file_url + Fore.YELLOW + ', retrying...')
        print(e)
        return download_url(file_url, timestamp, attempts + 1)


def get_snapshots(url, year=2021, attempts=0):

    if attempts > max_attempts:
        raise TimeoutError('Unable to get snapshots, max attempts reached.')

    try:
        req_url = 'http://web.archive.org/__wb/calendarcaptures?url=' + url + '&selected_year=' + str(year)
        print(Fore.CYAN + 'Loading snapshots from' + Fore.YELLOW, req_url)

        req = requests.get(req_url)
        data = req.json()

        for arr in data:
            for arr2 in arr:
                for arr3 in arr2:
                    if arr3 == None or 'ts' not in arr3:
                        continue

                    ts = str(arr3["ts"][0])
                    return download_url(url, ts)

        print(Fore.YELLOW + 'Unable to find snapshots from' + Fore.RED, str(year) + Fore.YELLOW + ', trying previous year.')
        return get_snapshots(url, year - 1, attempts + 1)

    except TimeoutError as e:
        raise e

    except:
        print(Fore.YELLOW + 'Error retrieving snapshots from', Fore.RED + req_url + Fore.YELLOW + ', retrying...')
        return get_snapshots(url, year, attempts + 1)


def get_archive(url, attempts=0):

    if attempts > max_attempts:
        raise TimeoutError('Unable to get archive, max attempts reached.')

    try:

        resp = requests.get(
            url='http://web.archive.org/cdx/search',
            params={
                'url': url,
                'matchType': 'prefix',
                'collapse': 'urlkey',
                'output': 'json',
                'fl': 'original,statuscode',
                'filter': '!statuscode:[45]..',
                'limit': '100000'
            }
        ).json()
        return resp

    except TimeoutError as e:
        raise e

    except:
        print(Fore.RED + 'Unable to find archive, retrying...')
        return get_archive(url, attempts + 1)


def thread():

    while len(pages) > 0:
        page = pages.pop()

        url, status = page
        
        try:
            get_snapshots(url, start_year)
        except:
            pages_error.append(url)

print(Fore.MAGENTA + '\nWayback Machine Archive Downloader')
print(Fore.WHITE + 'Developed by Samuel Walls\n')


print(Fore.CYAN + 'Website:' + Fore.WHITE)
inp_website = input()
if website: website = inp_website

print(Fore.CYAN + '\nStarting year (2021):' + Fore.WHITE)
inp_start_year = input()
if inp_start_year: start_year = int(inp_start_year)

print(Fore.CYAN + '\nThreads (1):' + Fore.WHITE)
inp_threads = input()
if inp_threads: threads = int(inp_threads)

print(Fore.CYAN + '\nAttempts per request (25):' + Fore.WHITE)
inp_max_attempts = input()
if inp_max_attempts: max_attempts = int(inp_max_attempts)



print(Fore.CYAN + '\n\nFetching all archived pages for' + Fore.YELLOW, website + Fore.CYAN + '...')

pages = get_archive(website)
header = pages.pop()

site = website.replace('http://', '')
site = website.replace('https://', '')

progress_file = './logs/' + site + '.downloaded.txt'
error_file = './logs/' + site + '.error.txt'

print(Fore.CYAN + 'Found' + Fore.YELLOW, len(pages), Fore.CYAN + 'archived pages.')

print(Fore.CYAN + '\nPages which are successfully downloaded will be logged to ' + Fore.YELLOW, progress_file)
print(Fore.CYAN + 'Pages which fail to downloaded will be logged to ' + Fore.YELLOW, error_file)


print(Fore.CYAN + '\nStarting' + Fore.YELLOW, str(threads), Fore.CYAN + 'threads.')

for i in range(threads):
    threading.Thread(target=thread).start()
    time.sleep(0.01)

while True:
    if os.name == 'nt':
        system('title Files remaining: ' + str(len(pages)) + ' ^| Downloaded: ' + str(len(pages_downloaded)) + ' ^| Failed: ' + str(len(pages_error)))

    file = open(progress_file, 'w')
    file.write('\n'.join(pages_downloaded))
    file.close()

    file = open(error_file, 'w')
    file.write('\n'.join(pages_error))
    file.close()

    time.sleep(1)
