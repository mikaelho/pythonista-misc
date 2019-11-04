'''
Design goals:
    - No need to prime loops etc.
    - As effortless coexistence between sync and async code as possible
    - Same decorator for simple threads, multiple parallel threads with common completion, with results and without results
    - Timeouts for when things go wrong
'''

import concurrent.futures as cf
from functools import partial, wraps
import threading, inspect, traceback

def threadbare(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        thread = threading.current_thread()
        thread.collector = getattr(thread, 'collector', set())
        executor = cf.ThreadPoolExecutor()
        if inspect.isgeneratorfunction(func):
            gen = func(*args, **kwargs)
            future = executor.submit(_gen_runner, gen)
        else:
            future = executor.submit(func, *args, **kwargs)
        thread.collector.add(future)
        executor.shutdown(wait=False)
        return future
    
    return wrapper

def _gen_runner(gen):
    thread = threading.current_thread()
    thread.collector = getattr(thread, 'collector', set())
    first_round = True
    prev_value = None
    try:
        while True:
            if first_round:
                value = next(gen)
                first_round = False
            else:
                value = gen.send(prev_value)
            for future in cf.as_completed(thread.collector):
                future.result()
            thread.collector.clear()
            if type(value) is cf.Future:
                prev_value = value.result()
            elif (
                type(value) in (tuple, list, set) and
                all((type(elem) is cf.Future for elem in value))
            ):
                prev_value = type(value)([future.result() for future in value])
            else:
                prev_value = value
    except StopIteration as stop:
        for future in cf.as_completed(thread.collector):
            future.result()
        thread.collector.clear()
        return stop.value
    except Exception as e:
        traceback.print_exc()


if __name__ == '__main__':
    
    import time, requests, bs4
    
    @threadbare
    def main():
        login()
        weather = yield get_weather()
        print(f'Weather is {weather}')
        
        results = yield [fetch(url)
            for url in (
                'https://python.org',
                'http://omz-software.com/pythonista/',
                'https://pypi.org'
            )]
        print('Retrieved pages:', results)
        
        logout()
    
    @threadbare
    def login():
        time.sleep(1)
        print('Logged in')
        raise Exception('Testing exception')
        
    @threadbare
    def get_weather():
        time.sleep(0.5)
        return 'fine'
        
    @threadbare
    def fetch(url):
        text = requests.get(url).text
        soup = bs4.BeautifulSoup(text, 'html.parser')
        title = soup.find('title')
        return title.string
        
    @threadbare
    def logout():
        print('Logged out')
        
    login()
