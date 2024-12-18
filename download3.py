import asyncio
from playwright.async_api import async_playwright
import os

# Function to read the .txt file for URL, username, and password
def read_credentials(file_path):
    with open(file_path, "r") as f:
        lines = [line.strip() for line in f.readlines()]
        if len(lines) < 3:
            raise ValueError("The input file must have at least 3 lines: URL, username, and password.")
        return lines[0], lines[1], lines[2]

async def download_csv_from_file(input_file):
    download_dir = "./downloads"

    # Ensure the download directory exists
    if not os.path.exists(download_dir):
        os.makedirs(download_dir)

    # Read URL, username, and password from the file
    url, username, password = read_credentials(input_file)
    print(f"Using credentials:\nURL: {url}\nUsername: {username}\nPassword: {password}")

    async with async_playwright() as p:
        # Launch browser (set headless=True if UI not needed)
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(accept_downloads=True)  # Allow file downloads
        page = await context.new_page()

        try:
            # Step 1: Navigate to login page
            print("Navigating to login page...")
            await page.goto(url)
            await page.wait_for_load_state("networkidle")

            # Step 2: Fill in username and password fields
            print("Filling out login form...")
            username_selector = 'input[name="username"], input#username, input[type="text"]'
            password_selector = 'input[name="password"], input#password, input[type="password"]'

            await page.fill(username_selector, username)
            await page.fill(password_selector, password)

            # Step 3: Click the Sign In button
            print("Clicking 'Sign in' button...")
            await page.click("#sign_in_button")  # Use the provided selector for the button

            # Step 4: Wait for login to complete
            await page.wait_for_url("**/admin.pl", timeout=10000)
            print("Login successful!")

            # Step 5: Click the 'Download' button
            print("Clicking 'Download' button...")
            await page.wait_for_selector("#download_data", timeout=5000)
            await page.click("#download_data")

            # Step 6: Click the 'Download Completes Only' button
            print("Clicking 'Download Completes Only' button...")
            await page.wait_for_selector("#download_completes", timeout=5000)
            async with page.expect_download() as download_info:  # Wait for the download to trigger
                await page.click("#download_completes")  # Trigger CSV download
            download = await download_info.value

            # Step 7: Save the downloaded file
            file_path = os.path.join(download_dir, download.suggested_filename)
            await download.save_as(file_path)
            print(f"CSV file downloaded successfully: {file_path}")

        except Exception as e:
            print(f"An error occurred: {e}")

        finally:
            # Close the browser
            await browser.close()
            print("Browser closed.")

if __name__ == "__main__":
    # Prompt the user to input the .txt file path
    input_file = input("Enter the path to the .txt file containing credentials: ").strip()
    try:
        asyncio.run(download_csv_from_file(input_file))
    except Exception as e:
        print(f"Error: {e}")
