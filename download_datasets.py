import requests
import os
import time

def search_and_download_github_csv(query, filename_hint, output_name):
    # GitHub Search API for code
    # We will just use a known good raw url for the popular dataset.
    urls = [
        "https://raw.githubusercontent.com/a-m-a-n-m-o-h-a-n/Crime-Data-Analysis/master/01_District_wise_crimes_committed_IPC_2001_2012.csv",
        "https://raw.githubusercontent.com/sachin0201/Analysis-of-Juvenile-Delinquency-in-India/master/01_District_wise_crimes_committed_IPC_2001_2012.csv",
        "https://raw.githubusercontent.com/ilakkiya-v/crime-data-analysis-in-India/master/01_District_wise_crimes_committed_IPC_2001_2012.csv",
        "https://raw.githubusercontent.com/Ramesh-Babu-369/Crime-in-India-Data-Analysis/main/01_District_wise_crimes_committed_IPC_2001_2012.csv",
        "https://raw.githubusercontent.com/Gaurav-Pansari/Crime-Analysis-in-India/master/01_District_wise_crimes_committed_IPC_2001_2012.csv",
        "https://raw.githubusercontent.com/jatin-97/Crime-in-India/master/01_District_wise_crimes_committed_IPC_2001_2012.csv"
    ]
    
    for url in urls:
        print(f"Trying {url} ...")
        response = requests.get(url)
        if response.status_code == 200:
            with open(output_name, 'wb') as f:
                f.write(response.content)
            print(f"Successfully downloaded to {output_name}")
            return True
        time.sleep(1)
        
    print("Failed to find dataset.")
    return False

if __name__ == "__main__":
    search_and_download_github_csv("", "", "crime_india_2001_2012.csv")
