import pandas as pd
import io
import logging
import os
from flask import send_file
import chardet

def merge_files(files, output_format='csv'):
    """
    Merge multiple CSV or Excel files into a single file
    
    Args:
        files: List of file objects from request.files
        output_format: 'csv' or 'excel'
        
    Returns:
        tuple: (file_object, filename, mimetype)
    """
    try:
        merged_data = []
        for file in files:
            # Get file extension
            file_ext = os.path.splitext(file.filename)[1].lower()
            
            # Read data based on file type
            if file_ext == '.csv':
                # 读取文件内容
                file_content = file.read()
                # 检测编码
                result = chardet.detect(file_content)
                encoding = result['encoding']
                
                # 使用检测到的编码读取CSV
                try:
                    df = pd.read_csv(io.BytesIO(file_content), encoding=encoding)
                except:
                    # 如果失败，尝试其他常见编码
                    for enc in ['utf-8', 'gbk', 'gb2312', 'gb18030', 'big5']:
                        try:
                            df = pd.read_csv(io.BytesIO(file_content), encoding=enc)
                            break
                        except:
                            continue
            else:  # Excel files
                df = pd.read_excel(file)
            
            # Add source file column
            df['Source_File'] = file.filename
            # Adjust column order
            cols = ['Source_File'] + [col for col in df.columns if col != 'Source_File']
            df = df[cols]
            merged_data.append(df)
        
        # Merge all data
        if not merged_data:
            raise ValueError("No data to merge")
            
        merged_df = pd.concat(merged_data, ignore_index=True)
        
        # Export based on selected format
        if output_format == 'csv':
            # Export as CSV with UTF-8 BOM to support Excel
            output = io.StringIO()
            merged_df.to_csv(output, index=False, encoding='utf-8-sig')
            mem_file = io.BytesIO()
            mem_file.write(output.getvalue().encode('utf-8-sig'))
            mem_file.seek(0)
            
            return (mem_file, 
                    'merged_files.csv',
                    'text/csv')
        else:
            # Export as Excel
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                merged_df.to_excel(writer, index=False, sheet_name='Merged Data')
            output.seek(0)
            
            return (output,
                    'merged_files.xlsx', 
                    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
                    
    except Exception as e:
        logging.error(f"Error in merge_files: {str(e)}")
        raise 