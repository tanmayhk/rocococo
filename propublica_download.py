import urllib.request
from zipfile import ZipFile
import os
import shutil
import time

for congress_num in range(94, 115):
    t0 = time.time()
    new_path = "propublica_data\\" + str(congress_num) + "\\"
    if not os.path.exists(new_path):
        os.makedirs(new_path)
    url = "https://s3.amazonaws.com/pp-projects-static/congress/bills/" + str(congress_num) + ".zip"
    file_name = new_path + "downloaded_file.zip"

    # Download the file from the URL
    urllib.request.urlretrieve(url, file_name)

    # Extract the downloaded ZIP file
    with ZipFile(file_name, 'r') as zip_file:
        zip_file.extractall(path=new_path)
        print("Files extracted successfully", congress_num)
        # shutil.move(".\\congress", new_path)
        # Optional: Remove the ZIP file after extraction
        # os.remove(file_name)
    t1 = time.time()
    print(congress_num, ":", t1 - t0, "s")