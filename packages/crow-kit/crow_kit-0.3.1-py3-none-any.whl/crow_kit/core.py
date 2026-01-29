import ssl
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service as BraveService
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.core.os_manager import ChromeType
from selenium.webdriver.chrome.service import Service
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup,  NavigableString
import json
import uuid
import time
from selenium.common.exceptions import TimeoutException

module_dir = os.path.dirname(__file__)
inner_dir = os.path.join(module_dir, "crow_kit_data", "wrappers")  # inside package
os.makedirs(inner_dir, exist_ok=True)



def setTableWrapper(url, wrapper_name='no_name'):
    try:
        create_directory()
    except PermissionDeniedError as e:
        return False, None, None, None, str(e)
        
    try:
        service = Service(executable_path=ChromeDriverManager().install())
        options = webdriver.ChromeOptions()
        options.add_argument("start-maximized")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('excludeSwitches', ['enable-logging'])
        options.add_experimental_option('useAutomationExtension', False)
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36")
        driver = webdriver.Chrome(service=service, options=options)
        driver.maximize_window()
        driver.get(url)

        css_file_path = os.path.join(module_dir+'/external_files/css', 'st.action-panel.css')
        with open(css_file_path, 'r') as css_file:
            css_content = css_file.read()
            driver.execute_script(f'''
                var style = document.createElement('style');
                style.type = 'text/css';
                style.innerHTML = `{css_content}`;
                document.head.appendChild(style);
            ''')

        js_file_path = os.path.join(module_dir+'/external_files/js', 'jquery-3.7.1.min.js')
        with open(js_file_path, 'r') as js_file:
            script = js_file.read()
            driver.execute_script(script)

        js_file_path = os.path.join(module_dir+'/external_files/js', 'sweetalert2.all.min.js')
        with open(js_file_path, 'r') as js_file:
            script = js_file.read()
            driver.execute_script(script)

        js_file_path = os.path.join(module_dir+'/external_files/js', 'st.action-panel.js')
        with open(js_file_path, 'r') as js_file:
            script = js_file.read()
            driver.execute_script(script)

        driver.execute_script('$("html").off("click");')

        js_file_path = os.path.join(module_dir, 'table_wrapper.js')
        with open(js_file_path, 'r') as js_file:
            script = js_file.read()
            driver.execute_script(script)

        while not driver.execute_script("return window.userTasksCompleted"):
            time.sleep(1)

        input_field_values = driver.execute_script("return window.inputFieldValues")

        wrapper_list = []
        for xpath_pair in input_field_values:
            table_path = xpath_pair['table_path']
            next_path = xpath_pair['next_path']
            dics = {}
            dics['url'] = url
            dics['wrapper_type'] = 'table'
            dics['base_path'] = table_path
            dics['next_path'] = next_path
            dics['repeat'] = ''
            wrapper_list.append(dics)

        unique_wrapper_name = wrapper_name + '_table_wrapper_' + str(uuid.uuid4()) + '.json'
        wrapper_path = os.path.join(inner_dir, unique_wrapper_name)
        with open(wrapper_path, 'w') as json_file:
            json.dump(wrapper_list, json_file)

        return True, unique_wrapper_name, None, None, None
        
    except Exception as error:
        error_code = 100
        error_type = type(error).__name__
        error_message = str(error)
        return False, None, error_code, error_type, error_message

def setGeneralWrapper(url, wrapper_name='no_name', repeat='no'):
    try:
        create_directory()
    except PermissionDeniedError as e:
        return False, None, None, None, str(e)
    try:
        service = Service(executable_path=ChromeDriverManager().install())
        options = webdriver.ChromeOptions()
        options.add_argument("start-maximized")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('excludeSwitches', ['enable-logging'])
        options.add_experimental_option('useAutomationExtension', False)
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36")
        driver = webdriver.Chrome(service=service, options=options)
        driver.maximize_window()
        driver.get(url)

        css_file_path = os.path.join(module_dir+'/external_files/css', 'st.action-panel.css')
        with open(css_file_path, 'r') as css_file:
            css_content = css_file.read()
            driver.execute_script(f'''
                var style = document.createElement('style');
                style.type = 'text/css';
                style.innerHTML = `{css_content}`;
                document.head.appendChild(style);
            ''')

        js_file_path = os.path.join(module_dir+'/external_files/js', 'jquery-3.7.1.min.js')
        with open(js_file_path, 'r') as js_file:
            script = js_file.read()
            driver.execute_script(script)

        js_file_path = os.path.join(module_dir+'/external_files/js', 'sweetalert2.all.min.js')
        with open(js_file_path, 'r') as js_file:
            script = js_file.read()
            driver.execute_script(script)

        js_file_path = os.path.join(module_dir+'/external_files/js', 'st.action-panel.js')
        with open(js_file_path, 'r') as js_file:
            script = js_file.read()
            driver.execute_script(script)

        driver.execute_script('$("html").off("click");')

        js_file_path = os.path.join(module_dir, 'general_wrapper.js')
        with open(js_file_path, 'r') as js_file:
            script = js_file.read()
            driver.execute_script(f"window.repeated_pattern = {repr(repeat)};\n{script}")

        while not driver.execute_script("return window.userTasksCompleted"):
            time.sleep(1)

        input_field_values = driver.execute_script("return window.inputFieldValues")

        wrapper_list = []
        for xpath_pair in input_field_values:

            data_fields = xpath_pair['data_fields']
            next_path = xpath_pair['next_path']
            parent_path = xpath_pair['parent_path']
            wrapper_list_inner = []
            for data_field in data_fields:
                data_fields_dics = {}
                data_fields_dics['attribute_name'] = data_field['attribute_name']
                data_fields_dics['attribute_value'] = data_field['attribute_value']
                wrapper_list_inner.append(data_fields_dics)

            dics = {}
            dics['url'] = url
            dics['wrapper_type'] = 'general'
            dics['base_path'] = wrapper_list_inner
            dics['next_path'] = next_path
            dics['parent_path'] = parent_path
            dics['repeat'] = repeat
            wrapper_list.append(dics)

        unique_wrapper_name = wrapper_name + '_general_wrapper_' + str(uuid.uuid4()) + '.json'
        wrapper_path = os.path.join(inner_dir, unique_wrapper_name)
        with open(wrapper_path, 'w') as json_file:
            json.dump(wrapper_list, json_file)

        return True, unique_wrapper_name, None, None, None
        
    except Exception as error:
        error_code = 100
        error_type = type(error).__name__
        error_message = str(error)
        return False, None, error_code, error_type, error_message

def getWrapperData(wrapper_name, maximum_data_count=100, url=''):
    try:
        create_directory()
    except PermissionDeniedError as e:
        return False, str(e)
    file_path = os.path.join(inner_dir, wrapper_name)
    success, wrapper_type, wrapper_url, base_path, next_path, parent_path, repeat = read_json_file(file_path)
    if success:
        if url == '':
            url = wrapper_url
        if wrapper_type == 'table':
            all_tables = getTableWrapperData(url, base_path, maximum_data_count, next_path)
        else:
            all_tables = getGeneralWrapperData(url, base_path, maximum_data_count, next_path, parent_path, repeat)
    else:
        return success, base_path
    return True, all_tables


def getTableWrapperData(url,base_path, maximum_data_count, next_path):
    all_tables = []
    try:
        service = Service(executable_path=ChromeDriverManager().install())
        options = webdriver.ChromeOptions()
        options.add_argument("start-maximized")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('excludeSwitches', ['enable-logging'])
        options.add_experimental_option('useAutomationExtension', False)
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument("--headless")
        
        options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36")
        driver = webdriver.Chrome(service=service, options=options)
        driver.maximize_window()
        driver.get(url)
        
        prev_tables = []
        while(1):
            current_tables = []
            xhtml = driver.find_element(By.XPATH, base_path)
            xhtml = xhtml.get_attribute('outerHTML')
            soup = BeautifulSoup(xhtml, "html.parser")
            top_level_tables = soup.find_all(is_top_level_table)
            for table in top_level_tables:
                all_tables_data = extract_table_data(table)
                current_tables.extend(all_tables_data)
            
            if(prev_tables != current_tables):
                all_tables.extend(current_tables)
                prev_tables = []
                prev_tables = current_tables.copy() 
            else:
                break
            
            if(next_path == ''):
                break

            if len(all_tables) >= maximum_data_count:
                break

            anchor_xpath = next_path
            driver.implicitly_wait(5)
            anchor_element = driver.find_element(By.XPATH,anchor_xpath)
            driver.execute_script("arguments[0].click();", anchor_element)
            time.sleep(5)
        
        driver.close()
        
    except Exception as error:
        pass
        #print(error)
           
    return filter_duplicate_rows(all_tables)

def getGeneralWrapperData(url, base_path, maximum_data_count, next_path, parent_path, repeat):
    all_tables = []
    try:
        service = Service(executable_path=ChromeDriverManager().install())
        options = webdriver.ChromeOptions()
        options.add_argument("start-maximized")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('excludeSwitches', ['enable-logging'])
        options.add_experimental_option('useAutomationExtension', False)
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument("--headless")
        options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36")
        driver = webdriver.Chrome(service=service, options=options)
        driver.maximize_window()
        driver.get(url)
        driver.implicitly_wait(20)
        if(repeat == 'yes'):
            list_header = []
            list_header_try = 0
            while(1):
                data_rows = []
                root_path = '.publication'
                for p in base_path:
                    if list_header_try == 0:
                        list_header.append(p['attribute_name'])
                    xpath_root = parent_path
                    xpath_root = xpath_root.replace('.', ' ')
                    xpath_root = xpath_root.strip()
                    xpath_sub = p['attribute_value']
                    xpath_sub = xpath_sub.replace('.', ' ')
                    xpath_sub = xpath_sub.strip()
                    path = "//*[@class='"+xpath_root+"']//*[@class='"+xpath_sub+"']"
                    elements = driver.find_elements(By.XPATH, path)
                    row_columns = []
                    for element in elements:
                        xhtml = element.get_attribute('outerHTML')
                        soup = BeautifulSoup(xhtml, "html.parser")
                        row_columns.append(soup.get_text(strip=True))
                    data_rows.append(row_columns)
                
                all_tables = all_tables + [list(pair) for pair in zip(*data_rows)]

                list_header_try = list_header_try + 1

                if(next_path == ''):
                    break

                if len(all_tables) >= maximum_data_count:
                    break

                anchor_xpath = next_path
                anchor_element = driver.find_element(By.XPATH,anchor_xpath)
                driver.execute_script("arguments[0].click();", anchor_element)
                time.sleep(3)
            
            all_tables.insert(0, list_header)      
        else:
            list_header_try = 0
            list_header = []
            while(1):
                data_rows = []
                for p in base_path:
                    if list_header_try == 0:
                        list_header.append(p['attribute_name'])
                    app_path = p['attribute_value']
                    xhtml = driver.find_element(By.XPATH, app_path)
                    xhtml = xhtml.get_attribute('outerHTML')
                    soup = BeautifulSoup(xhtml, "html.parser")
                    data_rows.append(soup.get_text(strip=True))
                all_tables.append(data_rows)

                list_header_try = list_header_try + 1

                if(next_path == ''):
                    break
                
                if len(all_tables) >= maximum_data_count:
                    break
                
                anchor_xpath = next_path
                anchor_element = driver.find_element(By.XPATH,anchor_xpath)
                driver.execute_script("arguments[0].click();", anchor_element)
                time.sleep(3)

            all_tables.insert(0, list_header)    
    except Exception as error:
        pass
        #print(error)
           
    return filter_duplicate_rows(all_tables)


def listWrappers():
    try:
        create_directory()
    except PermissionDeniedError as e:
        #print(e)
        return False, str(e)
    directory = inner_dir
    try:
        files = [f for f in os.listdir(directory) if os.path.isfile(os.path.join(directory, f))]
        return True, files
    except Exception as error:
        return False, str(error)

def filter_duplicate_rows(all_tables):
    unique_rows = set()
    filtered_data = [row for row in all_tables if tuple(row) not in unique_rows and not unique_rows.add(tuple(row))]
    return filtered_data

def read_json_file(file_path):
    try:
        with open(file_path, 'r') as json_file:
            data = json.load(json_file)

            if data and isinstance(data, list) and len(data) > 0:
                # Assuming there is only one item in the list
                first_item = data[0]

                wrapper_type = first_item.get('wrapper_type', 'table')
                url = first_item.get('url', '')
                base_path = first_item.get('base_path', '')
                next_path = first_item.get('next_path', '')
                repeat = first_item.get('repeat', 'no')
                parent_path = first_item.get('parent_path', '')

                return True, wrapper_type, url, base_path, next_path, parent_path, repeat
            else:
                return False, None, None, None, None, None, None
    except Exception as error:
        return False, None, None, str(error), None,None, None

def is_top_level_table(tag):
    return tag.name == 'table' and not bool(tag.find_parents('table'))

def extract_cell_data(cell):
    cell_data = extract_text_from_element(cell)
    nested_tables = cell.find_all('table', recursive=False)
    for nested_table in nested_tables:
        cell_data += ' ' + ' '.join(map(str, extract_table_data(nested_table)))
    
    return cell_data

def extract_table_data(table):
    table_data = []
    rows = table.select(':scope > tbody > tr, :scope > thead > tr') or table.find_all('tr', recursive=False)
    for row in rows:
        cell_data = [extract_cell_data(cell) for cell in row.find_all(['td', 'th'], recursive=False)]
        table_data.append(cell_data)
    return table_data

def extract_text_from_element(element):
    text = element.get_text(strip=True)
    nested_elements = element.find_all(['div', 'span', 'td'], recursive=False)
    for nested_element in nested_elements:
        text += ' ' + extract_text_from_element(nested_element)
    return text

class PermissionDeniedError(Exception):
    pass

def check_permissions(directory_path):
    test_file_path = os.path.join(directory_path, '.permission_test')
    try:
        with open(test_file_path, 'w'):
            pass
        os.remove(test_file_path)
    except OSError as e:
        raise PermissionDeniedError(
            f"Permission denied: Unable to write to {directory_path}. {e}"
        )


def create_directory(directory_path=inner_dir):
    try:
        os.makedirs(directory_path, exist_ok=True)
        check_permissions(directory_path)
    except OSError as e:
        raise PermissionDeniedError(f"Error creating directory: {e}")

