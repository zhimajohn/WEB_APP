import os
import shutil

def zip_application():
    # Source directory
    source_dir = r"C:\Users\23596\Desktop\CURSOR\spss label generator"
    # Output zip file
    output_zip = r"C:\Users\23596\Desktop\CURSOR\spss_label_generator.zip"
    
    try:
        # Create zip file
        shutil.make_archive(
            output_zip.replace('.zip', ''),  # Remove .zip as make_archive adds it
            'zip',
            source_dir
        )
        print(f"Successfully created zip file at: {output_zip}")
    except Exception as e:
        print(f"Error creating zip file: {str(e)}")

if __name__ == "__main__":
    zip_application()
    input("Press Enter to exit...") 