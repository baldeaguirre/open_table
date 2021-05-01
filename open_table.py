import os
import time
import pyautogui
import mysql.connector
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
from sqlalchemy import create_engine
from matplotlib.dates import DateFormatter,MonthLocator
import warnings
warnings.filterwarnings("ignore")

def data_extraction(data, type_str):

    data = data.loc[data["Type"]==type_str].set_index('Name').T
    data = data.drop("Type")
    data = data.replace({'%':''}, regex=True).astype(float)

    data.index = pd.to_datetime(data.index,format='%Y/%m/%d')
    return data

def plot_opentable(data, areas_list, figname_str):
    
    os.chdir("/home/baldeaguirre/Documents/OpenTable/") # storing figures directory
    
    with plt.style.context('fivethirtyeight'):
        
        fig, ax = plt.subplots(figsize=(16,9))
        for num,area in enumerate(areas_list):
            y = data[area].rolling(7).mean()
            
            ax.plot(y,
                    label=area,linewidth=1,
                    color=plt.rcParams['axes.prop_cycle'].by_key()['color'][num])
            
            ax.fill_between(data.index,0,y.values,alpha=0.2)

            ax.text(s=f"  {y[-1]:.2f}% {area}",
                    y=y[-1],
                    x=data[area].index.values[-1],
                    color = plt.rcParams['axes.prop_cycle'].by_key()['color'][num],
                    fontsize=10)
    
        ax.xaxis.set_major_formatter(DateFormatter('%b %y'))

        plt.title(f"COVID-19 - OpenTable Reservation Data - {data.index[-1].strftime('%d %B %Y')}",
                  fontsize=18.5,
                  fontweight='semibold',
                  color='#414141')
        
        ax.spines['right'].set_visible(False)
        ax.spines['top'].set_visible(False)
        ax.spines['bottom'].set_visible(True)
        ax.spines['left'].set_visible(False)
        
        ax.yaxis.set_major_formatter(mtick.PercentFormatter())
        ax.set_ylim(-101,150)
    
        fmt_month = MonthLocator()
        ax.xaxis.set_minor_locator(fmt_month)    

        ax.set_xlabel("Date",fontsize=12)
        ax.set_ylabel("YoY percentage change vs same date 2019",fontsize=12)

        plt.grid(axis='y',linestyle='--', alpha=0.4,visible=True)
        plt.grid(axis='x',visible=False)
        plt.tick_params(axis = 'both', which = 'major', labelsize = 12)
        # plt.show()
        plt.savefig(figname_str)
        
if __name__ == '__main__':

    os.chdir("/home/baldeaguirre/Downloads/")
    os.remove("2020-2021vs2019_Seated_Diner_Data.csv")
    
    pyautogui.click(37, 64)
    time.sleep(3)
    pyautogui.typewrite('https://www.opentable.com/state-of-industry', interval=0.03)
    pyautogui.press('enter')
    time.sleep(5)

    counter = 0
    while counter <= 13:
        pyautogui.click(1914, 1068)
        counter += 1

    time.sleep(2)
    pyautogui.click(1689, 991)
    time.sleep(3)
    
    os.chdir("/home/baldeaguirre/Downloads/")
    df = pd.read_csv(r"2020-2021vs2019_Seated_Diner_Data.csv")

    countries_list = ["Global","Canada","Germany","United Kingdom","United States", "Mexico"]
    states_list = ["Quintana Roo", "Mexico City", "New York", "Nuevo Leon", "Ontario", "Texas"]
    cities_list = ["Berlin", "Ciudad de México", "London", "New York", "San Antonio", "Toronto"]

    df_countries = data_extraction(df, 'country')
    df_states = data_extraction(df, 'state')
    df_cities = data_extraction(df, 'city')

    # Create MySQL database
    con = mysql.connector.connect(
        user='root',
        password='',
        host='127.0.0.1')

    cursor = con.cursor()
    cursor.execute("CREATE DATABASE IF NOT EXISTS opentable;")
    cursor.execute("ALTER DATABASE opentable CHARACTER SET utf8 COLLATE utf8_general_ci;") # cambiar encoding

    cursor.execute("USE opentable;")
    # cursor.execute("SELECT @@character_set_database, @@collation_database;") # checar encoding

    # result = cursor.fetchall()
    # print(result, '\n')

    cursor.close()
    con.close()

    # create sqlalchemy engine
    engine = create_engine(
        "mysql+pymysql://{user}:{pw}@localhost/{db}".format
        (
            user="root",
            pw="",
            db="opentable"
        )
    )

    # Writing data to MySQL database
    df_countries.to_sql('countries', con=engine, if_exists='replace')
    df_states.to_sql('states', con=engine, if_exists='replace')
    df_cities.to_sql('cities', con=engine, if_exists='replace')

    # Reading data from MySQL database
    df_countries_mysql = pd.read_sql_table('countries', con=engine).set_index('index')
    df_states_mysql = pd.read_sql_table('states', con=engine).set_index('index')
    df_cities_mysql = pd.read_sql_table('cities', con=engine).set_index('index')
    
    plot_opentable(df_countries_mysql, countries_list, 'countries_plot')
    plot_opentable(df_states_mysql, states_list, 'states_plot')
    plot_opentable(df_cities_mysql, cities_list, 'cities_plot')
