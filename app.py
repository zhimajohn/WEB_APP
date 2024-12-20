from flask import Flask, render_template, request, send_file, redirect, url_for, session
from functools import wraps
import os
from werkzeug.utils import secure_filename
import pandas as pd
from lxml import etree
import re
import logging
from playwright.async_api import async_playwright
import asyncio
import io
from file_merger import merge_files
import zipfile

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def ensure_download_dir(app):
    """Ensure the download directory exists"""
    download_dir = os.path.join(app.config['UPLOAD_FOLDER'], 'downloads')
    if not os.path.exists(download_dir):
        os.makedirs(download_dir, exist_ok=True)
    return download_dir

# Initialize Flask app
app = Flask(__name__)
app.secret_key = 'your-secret-key-here'  # Change this to a secure random key
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Ensure directories exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
ensure_download_dir(app)

# Add user credentials (in a real application, use a database)
USERS = {
    'admin': 'password123'  # Change this to your desired password
}

# Login decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Add login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        if username == 'admin' and password == 'cathaya':
            session['logged_in'] = True
            return redirect(url_for('home'))
        else:
            return render_template('login.html', error='Invalid credentials')
    
    return render_template('login.html')

# Add logout route
@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('login'))

# Add all your helper functions here
def Select_1(cut_info):
    try:
        re_Select1 = pd.DataFrame(
            columns=['Question ID', 'Type', 'Question Label', 'Value'])
        re_list = []
        # 添加标题
        re_list.append(cut_info[0][15:])
        # 添加题目类型
        re_list.append(cut_info[2][5:])
        # 添加问题
        try:
            re_list.append(cut_info[0][15:] + ' - ' +
                        cut_info[cut_info.index('[Header 2]:') + 1].replace('<b>', '').replace('</b>', '').replace(
                            '<i>Select one.</i>', '').replace('<br>', ''))
        except:
            re_list.append('')
        header_cnt = 2
        while True:
            if '<br />' in re_list[2]:
                re_list[2] = re_list[2].replace(
                    '<br />', '') + ' ' + cut_info[cut_info.index('[Header 2]:') +
                                                header_cnt]
                header_cnt += 1
            else:
                break
        re_list[2] = re_list[2].replace('<b>', '').replace('</b>', '').replace(
            '<i>Select all that apply.</i>',
            '').replace('<br>', '').replace('<br />',
                                            '').replace('<i>',
                                                        '').replace('</i>', '')
        # 添加选项
        if '[Post-Skips]:' in cut_info:
            end = cut_info.index('[Post-Skips]:')
        else:
            end = len(cut_info)

        start = end - int(cut_info[end - 1].split('\t')[0])
        option_tmp = cut_info[start:end]
        option = '\n'.join(option_tmp).replace('\t', '.')
        re_list.append(option)
        re_Select1.loc[0] = re_list

        return re_Select1
    except Exception as e:
        logging.error(f"Error processing single-choice question: {e}, Data: {cut_info}")
        return pd.DataFrame()

def Select_2(cut_info):
    try:
        re_Select2 = pd.DataFrame(
            columns=['Question ID', 'Type', 'Question Label', 'Value'])
        re_list = []
        # 添加标题
        re_list.append(cut_info[0][15:])
        # 添加题目类型
        re_list.append(cut_info[2][5:])
        # 添加问题
        try:
            re_list.append(cut_info[0][15:] + ' - ' +
                        cut_info[cut_info.index('[Header 2]:') + 1].replace('<b>', '').replace('</b>', '').replace(
                            '<i>Select all that apply.</i>', '').replace('<br>', ''))
        except:
            re_list.append('')
        header_cnt = 2
        while True:
            if '<br />' in re_list[2]:
                re_list[2] = re_list[2].replace(
                    '<br />', '') + ' ' + cut_info[cut_info.index('[Header 2]:') +
                                                header_cnt]
                header_cnt += 1
            else:
                break
        re_list[2] = re_list[2].replace('<b>', '').replace('</b>', '').replace(
            '<i>Select all that apply.</i>',
            '').replace('<br>', '').replace('<br />',
                                            '').replace('<i>',
                                                        '').replace('</i>', '')
        # 添加选项
        if '[Post-Skips]:' in cut_info:
            end = cut_info.index('[Post-Skips]:')
        else:
            end = len(cut_info)
        
        if cut_info[end - 1].split('\t')[0] == '</style>':
            end = cut_info.index('[Footer]:')
        start = end - int(cut_info[end - 1].split('\t')[0])
        option = cut_info[start:end]
        for i in range(len(option)):
            re_add = []
            if i == 0:
                re_add.append(re_list[0] + '_' + str(i + 1))
                re_add.append(re_list[1])
                re_add.append(re_list[2] + ' ' + option[0].split('\t')[1])
                re_add.append('0=NO 1=YES')
            else:
                re_add.append(re_list[0] + '_' + str(i + 1))
                re_add.append(re_list[1])
                re_add.append(option[i].split('\t')[1].replace('[Exclusive]', ''))
                re_add.append('0=NO 1=YES')
            re_Select2.loc[i] = re_add
        return re_Select2
    except Exception as e:
        logging.error(f"Error processing multiple-choice question: {e}, Data: {cut_info}")
        return pd.DataFrame()

def Select_3(cut_info):
    pass

def Free_format(cut_info):
    re_free = pd.DataFrame(
        columns=['Question ID', 'Type', 'Question Label', 'Value'])
    re_list = []
    # 添加标题
    re_list.append(cut_info[0][15:])
    # 添加题目类型
    re_list.append(cut_info[2][5:])
    # 添加问题
    try:
        re_list.append(cut_info[0][15:] + ' - ' +
                       cut_info[cut_info.index('[Header 2]:') + 1].replace('<b>', '').replace('</b>', '').replace(
                           '<i>Select all that apply.</i>', '').replace('<br>', ''))
    except:
        re_list.append('')
    header_cnt = 2
    while True:
        if '<br />' in re_list[2]:
            try:
                re_list[2] = re_list[2].replace(
                    '<br />', '') + ' ' + cut_info[cut_info.index('[Header 2]:') +
                                                   header_cnt]
            except:
                print('please Check：', re_list[0])
                break
            header_cnt += 1
        else:
            break
    re_list[2] = re_list[2].replace('<b>', '').replace('</b>', '').replace(
        '<i>Select all that apply.</i>',
        '').replace('<br>', '').replace('<br />',
                                        '').replace('<i>',
                                                    '').replace('</i>', '')
    re_list.append('')
    re_free.loc[0] = re_list
    var = 1
    while True:
        new_list = []
        try:
            question_pos = cut_info.index('[Variable %d]:' % var) + 1
            new_list.append(cut_info[question_pos][5:].strip())
            new_list.append(cut_info[question_pos + 1][5:].strip())
            new_list.append('')
            new_list.append('')
            re_free.loc[new_list[0]] = new_list
        except:
            break
        var += 1
    return re_free

def Grid(cut_info):
    re_Select2 = pd.DataFrame(
        columns=['Question ID', 'Type', 'Question Label', 'Value'])
    re_list = []
    # 添加提目标号
    re_list.append(cut_info[0][15:])
    # 添加题目类型
    re_list.append(cut_info[2][5:])
    # 添加问题
    re_list.append(cut_info[0][15:] + ' - ' +
                   cut_info[cut_info.index('[Header 2]:') + 1])
    header_cnt = 2

    while True:
        if '<br />' in re_list[2]:
            re_list[2] = re_list[2].replace(
                '<br />', '') + ' ' + cut_info[cut_info.index('[Header 2]:') +
                                               header_cnt]
            header_cnt += 1
        else:
            break
    re_list[2] = re_list[2].replace('<b>', '').replace('</b>', '').replace(
        '<i>Select all that apply.</i>',
        '').replace('<br>', '').replace('<br />',
                                        '').replace('<i>',
                                                    '').replace('</i>', '')
    re_list.append(0)

    # 筛选col（顺序在后）
    try:
        col_index = cut_info.index('[Row 1]:') - 1
    except:
        col_index = cut_info.index('[Column 1]:') - 1
    if cut_info[col_index] == 'Total':
        col_index -= 1
    col_start_index = col_index - int(cut_info[col_index].split('\t')[0])
    col_list = cut_info[col_start_index + 1:col_index + 1]
    
    # 筛选row（顺序在前）
    # 定位Grid单/多选
    try:
        grid_type = cut_info.index('[Row 1]:') + 1
    except:
        grid_type = cut_info.index('[Column 1]:') + 1

    # 对于表格-单选题进行操作
    if cut_info[grid_type] == 'Type: Select (Radio Button)':
        # Process radio button grid
        row_index = cut_info.index('[Column List]:') - 1
        while row_index > 0:
            ind = cut_info[row_index].split('\t')
            if ind[0] == cut_info[row_index]:
                row_index -= 1
            else:
                for i in range(row_index - int(ind[0]) + 1, row_index + 1):
                    add_list = []
                    row_list = cut_info[i].split('\t')
                    if '<table class="trow">' in row_list[0]:
                        html = etree.HTML(row_list[0])
                        row_list[0] = html.xpath('//table/tr/td[2]/@title')[0].split('<p>')[0].replace('<i>', '')
                    row_list[1] = row_list[1].replace('<b>', '').replace('</b>', '').replace('<br>', '').replace('<br/>', '').replace('<br />', '').replace('<i>', '').replace('</i>', '')
                    add_list.append(re_list[0] + '_r' + row_list[0])
                    add_list.append(re_list[1])
                    if row_list[0] == '1':
                        if len(row_list) > 1:
                            add_list.append(re_list[2] + row_list[1])
                        else:
                            add_list.append(re_list[2] + row_list[0])
                        add_list.append('\n'.join(col_list).replace('\t', '.'))
                    else:
                        if len(row_list) > 1:
                            add_list.append(row_list[1])
                        else:
                            add_list.append(row_list[0])
                        add_list.append('\n'.join(col_list).replace('\t', '.'))
                    re_Select2.loc[str(row_index) + str(i) + 'test'] = add_list
                break
    else:
        # Process other grid types
        row_end_index = cut_info.index('[Column List]:') - 1
        try:
            row_end = int(cut_info[row_end_index].split('\t')[0])
        except:
            row_end_index -= 1
        if 'Total' in cut_info[row_end_index]:
            row_end_index -= 1
        if 'S9li' in cut_info[row_end_index]:
            row_end_index -= 3
        row_end = int(cut_info[row_end_index].split('\t')[0])
        row_start = row_end_index - row_end

        try:
            col_end_index = cut_info.index('[Row 1]:') - 1
        except:
            col_end_index = cut_info.index('[Column 1]:') - 1

        if cut_info[col_end_index] == 'Total':
            col_end_index -= 1
        col_start_index = col_end_index - int(cut_info[col_end_index].split('\t')[0])
        
        c = 1
        for col in range(col_start_index + 1, col_end_index + 1):
            r = 1
            for row in range(row_start + 1, row_end_index + 1):
                add_list = []
                add_list.append(re_list[0] + '_r' + str(r) + '_c' + str(c))
                add_list.append(re_list[1])

                if '<table class="trow">' in cut_info[row]:
                    html = etree.HTML(cut_info[row])
                    try:
                        cut_info[row] = html.xpath('//table/tr/td[2]/@title')[0].split('<p>')[0].replace('<i>', '')
                    except:
                        cut_info[row] = html.xpath('//span/text()')[0]
                else:
                    try:
                        cut_info[row] = cut_info[row].split('\t')[1]
                    except:
                        pass
                cut_info[row] = cut_info[row].replace('<b>', '').replace('</b>', '').replace('<br>', '').replace('<br/>', '').replace('<br />', '').replace('<i>', '').replace('</i>', '').replace('[Exclusive]', '')

                if '<table class="trow">' in cut_info[col]:
                    html = etree.HTML(cut_info[col])
                    try:
                        cut_info[col] = html.xpath('//table/tr/td[2]/@title')[0].split('<p>')[0].replace('<i>', '')
                    except:
                        cut_info[col] = html.xpath('//span/text()')[0]
                else:
                    try:
                        cut_info[col] = cut_info[col].split('\t')[1]
                    except:
                        pass
                cut_info[col] = cut_info[col].replace('<b>', '').replace('</b>', '').replace('<br>', '').replace('<br/>', '').replace('<br />', '').replace('<i>', '').replace('</i>', '').replace('[Exclusive]', '')

                if c == 1 and r == 1:
                    add_list.append(re_list[2] + ' ' + cut_info[row] + ' - ' + cut_info[col])
                else:
                    add_list.append(cut_info[row] + ' - ' + cut_info[col])
                add_list.append('0=No 1=Yes')
                re_Select2.loc[str(col) + str(row)] = add_list
                r += 1
            c += 1
    return re_Select2

def clean_(x, clean_list):
    for i in clean_list:
        i = i.strip('\n')
        if i in x:
            x = x.replace(i, '')
    S = re.compile(r'\<(.*?)\>', re.S)
    return re.sub(S, '', x).strip()

def type_change(x):
    if x.strip() == 'Select (Radio Button)':
        return 'Single'
    elif x.strip() == 'Select (Check Box)':
        return 'Multi'
    else:
        return x.strip()

def Data_map(path, clean_txt):
    try:
        # 构造结果存储DF
        result = pd.DataFrame(columns=['Question ID', 'Type', 'Question Label', 'Value'])
        
        logging.debug(f"Opening file: {path}")
        # 读取文件
        label_txt = open(path, encoding='utf-8')
        # 按行读取
        txt = label_txt.readlines()
        
        logging.debug(f"Number of lines read: {len(txt)}")
        
        # 获取清洗后的文件内容
        txt_clean = []
        for i in txt:
            res = i.strip('\n\t')
            if res != '':
                txt_clean.append(res)
                
        logging.debug(f"Number of non-empty lines: {len(txt_clean)}")
        
        Q_list_index_a = txt_clean.index('Question List')
        Q_list_index_b = txt_clean.index('Data Field Usage')
        
        logging.debug(f"Question List found at index: {Q_list_index_a}")
        logging.debug(f"Data Field Usage found at index: {Q_list_index_b}")
        
        # 得到题目类型列表
        Q_list = txt_clean[Q_list_index_a + 4: Q_list_index_b - 4]
        Q_list_info = []
        
        # 将文档分块，每个题目一块
        for i in Q_list:
            Q_name = i.split()[0]
            index_a = txt_clean.index('Question Name: ' + Q_name)
            index_b = txt_clean[index_a:].index(
                '----------------------------------<PAGE BREAK>----------------------------------'
            )
            Q_list_info.append(txt_clean[index_a:index_a + index_b])

        # Process each question
        for i in Q_list_info:
            if i[2] == 'Type: Select (Radio Button)' or i[2] == 'Type: Select (Dropdown)':
                r = Select_1(i)
                result = pd.concat([result, r])
            elif i[2] == 'Type: Select (Check Box)':
                r = Select_2(i)
                result = pd.concat([result, r])
            elif i[2] == 'Type: Grid':
                r = Grid(i)
                result = pd.concat([result, r])
            else:
                r = Free_format(i)
                result = pd.concat([result, r])

        result.reindex()
        clean_t = open(clean_txt, encoding='utf-8').readlines()

        result['Question ID'] = result['Question ID'].apply(clean_, clean_list=clean_t)
        result['Question Label'] = result['Question Label'].apply(clean_, clean_list=clean_t)
        result['Type'] = result['Type'].apply(type_change)
        result['Value'] = result['Value'].apply(clean_, clean_list=clean_t)
        
        logging.debug(f"Processed {len(result)} questions")
        return result
        
    except Exception as e:
        logging.error(f"Error in Data_map: {str(e)}")
        return None

def single_trans(original_string):
    modified_string = re.sub(r'(\d+)\.', r'\1"', original_string)
    modified_string = modified_string.replace("\n", '''"\n''')
    modified_string = modified_string + '''".'''
    return modified_string

def group_multi_response(df):
    df["QuestionGroup"] = df["Question ID"].str.extract(r'(^[A-Za-z]+\d+)')
    multi_df = df[df["Type"] == "Multi"]
    grouped = (
        multi_df.groupby("QuestionGroup")["Question ID"]
        .apply(lambda x: sorted(x, key=lambda v: (v.split('_')[0], int(v.split('_')[1]))))
        .reset_index()
    )
    return grouped

def generate_multi_response_syntax(grouped_df, labels_df):
    multi_syntax = []
    multi_syntax.append("*------------------------------------------多重相应语法------------------------------------------.")
    for _, row in grouped_df.iterrows():
        question_group = row["QuestionGroup"]
        variables = row["Question ID"]
        
        set_name = f"${question_group}_SET"
        question_label = labels_df.loc[labels_df["Question ID"] == variables[0], "Question Label"].values[0]
        variables_str = " ".join(variables)
        
        syntax = (
            f"MRSETS\n"
            f"  /MDGROUP NAME={set_name} LABEL='{question_group} - {question_label}'\n"
            f"    CATEGORYLABELS=VARLABELS VARIABLES={variables_str} VALUE=1\n"
            f"  /DISPLAY NAME=[{set_name}].\n"
        )
        multi_syntax.append(syntax)
    return multi_syntax

def process_grid_questions(df):
    spss_syntax = []
    spss_syntax.append("*------------------------------------------表格题语法------------------------------------------.")
    
    for _, row in df.iterrows():
        if row['Type'] != 'Grid':
            continue

        question_id = row['Question ID']
        question_label = row['Question Label']
        question_values = row['Value']

        value_matches = re.findall(r'\d+\.', question_values)
        value_count = len(value_matches)

        if value_count == 0:
            continue

        new_variable = f"{question_id}_b"

        if value_count == 7:
            recode_syntax = f"RECODE {question_id} (6 thru 7=1)(3 thru 5=2)(1 thru 2=3) INTO {new_variable}."
        elif value_count == 6:
            recode_syntax = f"RECODE {question_id} (5 thru 6=1)(3 thru 4=2)(1 thru 2=3) INTO {new_variable}."
        elif value_count == 5:
            recode_syntax = f"RECODE {question_id} (4 thru 5=1)(2 thru 3=2)(1 thru 2=3) INTO {new_variable}."
        else:
            continue

        label_syntax = f"VARIABLE LABELS {new_variable} '{question_label}'."
        value_label_syntax = (
            f"VALUE LABELS {new_variable} "
            f"1 'Top 2' "
            f"2 'Mid {value_count - 4}' "
            f"3 'Bottom 2'."
        )

        spss_syntax.extend([recode_syntax, label_syntax, value_label_syntax, ""])

    spss_syntax.append("EXECUTE.")
    return spss_syntax

def generate_spss_syntax(row):
    syntax = []
    question_id = row["Question ID"]
    question_type = row["Type"]
    question_label = row["Question Label"]
    question_values = row["Value"]

    if question_type == 'Single':
        syntax.extend([
            f'\nVARIABLE LABELS {question_id} "{question_label}".',
            f'VALUE LABELS {question_id}',
            single_trans(question_values) + '\n'
        ])
    elif question_type == 'Multi':
        syntax.append(f'VARIABLE LABELS {question_id} "{question_label}".')
    elif question_type == 'Value':
        syntax.extend([
            f'\nVARIABLE LABELS {question_id} "{question_label}".\n'
        ])
    elif question_type == 'Grid' and question_values == "0=No 1=Yes":
        syntax.append(f'VARIABLE LABELS {question_id} "{question_label}".\n')
    elif question_type == 'Grid':
        syntax.extend([
            f'VARIABLE LABELS {question_id} "{question_label}".',
            f'VALUE LABELS {question_id}',
            single_trans(question_values) + '\n'
        ])
    elif question_type == 'Free Format':
        syntax.append(f'VARIABLE LABELS {question_id} "{question_label}".')
    elif question_type == 'Select (Dropdown)':
        syntax.extend([
            f'\nVARIABLE LABELS {question_id} "{question_label}".',
            f'VALUE LABELS {question_id}',
            single_trans(question_values) + '\n'
        ])

    return '\n'.join(syntax)

def process_txt_file(file_path):
    try:
        # Create a default clean.txt in the uploads folder if it doesn't exist
        clean_txt_path = os.path.join(app.config['UPLOAD_FOLDER'], 'clean.txt')
        if not os.path.exists(clean_txt_path):
            with open(clean_txt_path, 'w', encoding='utf-8') as f:
                f.write('')  # Add default cleaning rules if needed
        
        # Process the file using your existing logic
        result_df = Data_map(file_path, clean_txt_path)
        
        # Add error checking for result_df
        if result_df is None or result_df.empty:
            error_msg = "Failed to process the file: No data was extracted"
            logging.error(error_msg)
            return error_msg
            
        # 生成基本语法
        all_syntax = []
        for _, row in result_df.iterrows():
            syntax = generate_spss_syntax(row)
            if syntax:  # Only add non-empty syntax
                all_syntax.append(syntax)
        
        # 生成多重响应语法
        grouped_multi = group_multi_response(result_df)
        multi_syntax_list = generate_multi_response_syntax(grouped_multi, result_df)
        all_syntax.extend(multi_syntax_list)
        
        # 生成表格题语法
        grid_syntax_list = process_grid_questions(result_df)
        all_syntax.extend(grid_syntax_list)
        
        if not all_syntax:
            return "No SPSS syntax was generated from the file"
            
        return '\n'.join(all_syntax)
        
    except Exception as e:
        error_msg = f"Error processing file: {str(e)}"
        logging.error(error_msg)
        return error_msg

# Add the scraper functions
def read_credentials(file_content):
    lines = [line.strip() for line in file_content.splitlines()]
    if len(lines) < 3:
        raise ValueError("The input file must have at least 3 lines: URL, username, and password.")
    return lines[0], lines[1], lines[2]

async def download_csv_from_credentials(url, username, password, download_dir):
    """Download survey data using provided credentials"""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(accept_downloads=True)
        page = await context.new_page()

        try:
            await page.goto(url)
            await page.wait_for_load_state("networkidle")

            # Fill login form
            username_selector = 'input[name="username"], input#username, input[type="text"]'
            password_selector = 'input[name="password"], input#password, input[type="password"]'
            
            await page.fill(username_selector, username)
            await page.fill(password_selector, password)
            await page.click("#sign_in_button")

            # Wait for login to complete
            await page.wait_for_url("**/admin.pl", timeout=10000)

            # Click download buttons
            await page.wait_for_selector("#download_data", timeout=5000)
            await page.click("#download_data")
            
            await page.wait_for_selector("#download_completes", timeout=5000)
            async with page.expect_download() as download_info:
                await page.click("#download_completes")
            download = await download_info.value
            
            # Save file
            file_path = os.path.join(download_dir, download.suggested_filename)
            await download.save_as(file_path)
            
            return file_path

        finally:
            await browser.close()

# Add new route for the scraper page
@app.route('/scraper', methods=['GET', 'POST'])
@login_required
def scraper():
    if request.method == 'POST':
        if 'file' not in request.files:
            return 'No file uploaded', 400
            
        file = request.files['file']
        if file.filename == '':
            return 'No file selected', 400
            
        if file and file.filename.endswith(('.xlsx', '.xls')):
            try:
                # Read Excel file
                df = pd.read_excel(file)
                if len(df.columns) != 3:
                    return 'Excel file must have exactly 3 columns: URL, Username, Password', 400
                
                # Get download directory
                download_dir = ensure_download_dir(app)
                
                # 清理旧的zip文件
                zip_path = os.path.join(download_dir, 'downloaded_surveys.zip')
                if os.path.exists(zip_path):
                    try:
                        os.remove(zip_path)
                    except Exception as e:
                        logging.error(f"Error removing old zip file: {str(e)}")
                
                # Start download process
                results = []
                successful_files = []
                
                for index, row in df.iterrows():
                    url = str(row[0]).strip()
                    username = str(row[1]).strip()
                    password = str(row[2]).strip()
                    
                    try:
                        file_path = asyncio.run(download_csv_from_credentials(
                            url, username, password, download_dir))
                        if os.path.exists(file_path):  # 验证文件是否成功下载
                            results.append({
                                'url': url,
                                'status': 'success',
                                'message': f'Downloaded to {os.path.basename(file_path)}'
                            })
                            successful_files.append(file_path)
                        else:
                            raise Exception("File download failed")
                    except Exception as e:
                        results.append({
                            'url': url,
                            'status': 'error',
                            'message': str(e)
                        })
                
                # 如果有成功下载的文件，创建zip文件
                if successful_files:
                    try:
                        # 创建内存中的zip文件
                        memory_file = io.BytesIO()
                        with zipfile.ZipFile(memory_file, 'w') as zipf:
                            for file in successful_files:
                                if os.path.exists(file):
                                    zipf.write(file, os.path.basename(file))
                        
                        # 保存zip文件到磁盘
                        memory_file.seek(0)
                        with open(zip_path, 'wb') as f:
                            f.write(memory_file.getvalue())
                        
                        if os.path.exists(zip_path):  # 验证zip文件是否成功创建
                            return render_template('scraper_results.html', 
                                                results=results,
                                                has_downloads=True)
                        else:
                            raise Exception("Failed to create zip file")
                    except Exception as e:
                        logging.error(f"Error creating zip file: {str(e)}")
                        return render_template('scraper_results.html', 
                                            results=results,
                                            has_downloads=False)
                else:
                    return render_template('scraper_results.html', 
                                        results=results,
                                        has_downloads=False)
                    
            except Exception as e:
                logging.error(f"Error in scraper: {str(e)}")
                return f'Error processing request: {str(e)}', 400
            finally:
                # 清理单个下载的文件，保留zip文件
                for file in successful_files:
                    try:
                        if os.path.exists(file):
                            os.remove(file)
                    except Exception as e:
                        logging.error(f"Error removing file {file}: {str(e)}")
                
        return 'Invalid file type. Please upload an Excel file.', 400
        
    return render_template('scraper.html')

# 添加新的路由用于下载ZIP文件
@app.route('/download_surveys')
@login_required
def download_surveys():
    try:
        download_dir = ensure_download_dir(app)
        zip_path = os.path.join(download_dir, 'downloaded_surveys.zip')
        
        if os.path.exists(zip_path):
            try:
                # 读取zip文件到内存
                with open(zip_path, 'rb') as f:
                    memory_file = io.BytesIO(f.read())
                memory_file.seek(0)
                
                # 发送文件
                return send_file(
                    memory_file,
                    mimetype='application/zip',
                    as_attachment=True,
                    download_name='downloaded_surveys.zip'
                )
            except Exception as e:
                logging.error(f"Error sending zip file: {str(e)}")
                return f'Error sending file: {str(e)}', 500
            finally:
                # 清理zip文件
                try:
                    os.remove(zip_path)
                except:
                    pass
        else:
            return 'No downloads available. Please try downloading the files again.', 404
            
    except Exception as e:
        logging.error(f"Error in download_surveys: {str(e)}")
        return f'Error downloading files: {str(e)}', 500

# Modify the main route to show both options
@app.route('/')
@login_required
def home():
    return render_template('home.html')

# Rename existing upload_file route to spss_generator
@app.route('/spss', methods=['GET', 'POST'])
@login_required
def spss_generator():
    if request.method == 'POST':
        if 'file' not in request.files:
            return 'No file uploaded', 400
        
        file = request.files['file']
        if file.filename == '':
            return 'No file selected', 400
        
        if file and file.filename.endswith('.txt'):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            
            # Process the file and generate SPSS syntax
            spss_syntax = process_txt_file(filepath)
            
            # Clean up the uploaded file
            os.remove(filepath)
            
            return render_template('result.html', syntax=spss_syntax)
        
        return 'Invalid file type. Please upload a .txt file.', 400
    
    return render_template('spss.html')

@app.route('/tutorial')
@login_required
def tutorial():
    return render_template('tutorial.html')

# 添加新的路由
@app.route('/merger', methods=['GET', 'POST'])
@login_required
def merger():
    if request.method == 'POST':
        if 'files[]' not in request.files:
            return 'No files uploaded', 400
            
        files = request.files.getlist('files[]')
        if not files or files[0].filename == '':
            return 'No files selected', 400
            
        output_format = request.form.get('output_format', 'csv')
        
        # Check file formats
        allowed_extensions = {'.csv', '.xlsx', '.xls'}
        if not all(any(f.filename.lower().endswith(ext) for ext in allowed_extensions) 
                  for f in files):
            return 'Invalid file format. Only CSV and Excel files are supported.', 400
            
        try:
            file_obj, filename, mimetype = merge_files(files, output_format)
            return send_file(
                file_obj,
                mimetype=mimetype,
                as_attachment=True,
                download_name=filename
            )
                
        except Exception as e:
            logging.error(f"Error in merger route: {str(e)}")
            return f'Error processing files: {str(e)}', 400
            
    return render_template('merger.html')

# 添加新的路由用于下载模板
@app.route('/download_template')
@login_required
def download_template():
    try:
        # 创建一个新的 Excel 文件
        df = pd.DataFrame(columns=['URL', 'Username', 'Password'])
        
        # 将 DataFrame 保存到内存中的 Excel 文件
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='Credentials')
            
            # 获取 worksheet 对象
            worksheet = writer.sheets['Credentials']
            
            # 调整列宽
            worksheet.set_column('A:A', 40)  # URL 列宽
            worksheet.set_column('B:C', 20)  # Username 和 Password 列宽
            
        output.seek(0)
        
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name='survey_credentials_template.xlsx'
        )
        
    except Exception as e:
        logging.error(f"Error creating template: {str(e)}")
        return f'Error creating template: {str(e)}', 400

if __name__ == '__main__':
    app.run(debug=True) 