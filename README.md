<div align="center">
  <h1>AutoRiaDataParser</h1>

<div align="justify">
The script automatically collects and processes data necessary for analyzing data about cars and sellers posted on the website <a href="https://auto.ria.com/"> AutoRia</a>.

<br>

📌 **Operating principle:**

Page analysis and data collection is performed using *Selenium* and *BeautifulSoup*. Links are collected and checked for uniqueness relative to the current date, after which they are saved to the database, excluding duplicates. Each unique URL is processed to extract information about cars and sellers. The data is saved to the database and updated as needed.

📌 **Advantages of use:**

• *Automation:* Eliminates the need for manual analysis of a large number of pages and ads.  
• *Time saving:* Fast data collection using Selenium and BeautifulSoup.  
• *Flexibility:* The script can be configured to work with any section of the AutoRia website and any search parameters by substituting the appropriate link.  
• *Data relevance:* Information can be updated daily, and old records can be additionally analyzed relative to new ones.  
• *Analytics:* The collected data allows for an in-depth analysis of the car market.  

</div>

<div align="center">

   ## 💡Practical use

</div>

<div align="justify">

• *Market Analysis:* Identifying market prices, popular models, average car specifications.  
• *Marketing:* Helping sellers set competitive prices.  
• *Research:* Using data to study market trends.  
• *App Development:* Integrating data into car comparison apps.  

</div>

<br>

<div align="center">

   # Settings

</div>

<div align="left">

1. Clone this repository:

   ```
      git clone https://github.com/lazycatcoder/AutoRiaDataParser.git
   ```


2. Install dependencies:
   
   ```
      pip install -r requirements.txt
   ```


3. Download *ChromeDriver* for your version of Chrome browser from the <a href="https://developer.chrome.com/docs/chromedriver/downloads"> official website</a>. Specify the path to the driver in the **driver** variable:

   ```
     driver = webdriver.Chrome(executable_path=r"D:\chromedriver.exe", options=options)
   ```


4. Set the parsing link in the **base_url** variable:   

   ```
     base_url = "https://auto.ria.com/search/..."
   ```


5. In the **DB_PATH** variable, specify the path to the location of the database file: 
   ```
      DB_PATH = r"D:\AR_data.db"
   ```

</div>

<br>

### 🔴 Additional Information
<div align="justify">

Also in this repository there is a script *"CSV_Converter.py"* which provides the functionality to convert database data to a CSV file. Before running, make sure that the **DB_PATH** variable is correctly set to the location of your database. Run the script. Upon successful execution, the CSV file will be created in the same directory as the database.

</div>
