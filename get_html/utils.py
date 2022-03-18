import time
import re

def safe_find(browser, by, value, num_results, retries=2, delay=1):
    for r in range(retries + 1):
        elements = browser.find_elements(by=by, value=value)
        
        if len(elements) > 0:
            if num_results:
                return elements[:num_results]
            return elements
        print("Retrying for value", value)
        time.sleep(delay)
    return None

def find_value_in_html(html, left, right, width=50):
    return [[html[i.end():i.end()+j.start()] for j in re.finditer(right, html[i.end(): i.end() + width])][0] for i in re.finditer(left, html)]

def pad_or_trunc_list(arr, target_len):
    return arr[:target_len] + ['-']*(target_len - len(arr))

def apply_scratched(arr, scratched):
    i = 0
    result = []
    for s in scratched:
        if not s:
            result.append(arr[i])
            i += 1
        else:
            result.append('-')
    return result

def find_scratched(html, query):
    return [len([k for k in re.finditer('class="h5 text-scratched"', j)]) for j in [html[i.start():i.end()] for i in re.finditer(query, html)]]
