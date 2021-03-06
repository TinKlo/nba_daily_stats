"""
This file shall hold all functions of the project
"""


# needed libraries
from urllib.request import urlopen
from bs4 import BeautifulSoup
import pandas as pd
from sqlalchemy import create_engine


class Extraction:
    def per_game_scrapper():
        # URL to scrape
        url = "https://www.basketball-reference.com/leagues/NBA_2021_per_game.html#per_game_stats"

        # collect HTML data
        html = urlopen(url)
        
        # create beautiful soup object from HTML
        soup = BeautifulSoup(html, features="lxml")

        # use getText()to extract the headers into a list
        headers = [th.getText() for th in soup.findAll('tr', limit=2)[0].findAll('th')]
        hearders_spec = headers[1:30]
        print(hearders_spec)
        # get rows from table
        rows = soup.findAll('tr')[1:]
        rows_data = [[td.getText() for td in rows[i].findAll('td')]
                        for i in range(len(rows))]
        # if you print row_data here you'll see an empty row
        # so, remove the empty row
        # rows_data.pop(20)
        # for simplicity subset the data for only 39 seasons
        # rows_data = rows_data[0:38]

        # we're missing a column for years
        # add the years into rows_data
        # last_year = 2020
        # for i in range(0, len(rows_data)):
            # rows_data[i].insert(0, last_year)
            # last_year -=1

    # create the dataframe
        nba_stats_21 = pd.DataFrame(rows_data, columns = hearders_spec)
        # export dataframe to a CSV , columns = headers
        nba_stats_21.to_csv("nba_stats_21.csv", index=False)
        return nba_stats_21
    # scrapping done with the help of https://medium.com/analytics-vidhya/intro-to-scraping-basketball-reference-data-8adcaa79664a
    # print('function running')
    # per_game_scrapper()
    # print('function done')

class SqlConnection:
    """
    Connects sql databases.
    """
    def to_sql_file_append(df, connection, table_name):
        """Appends dataframe on mysql table."""
        print('Starting to append dataframe to database.')
        data_frame = df
        sql_engine = create_engine(connection)
        db_connection = sql_engine.connect()
        try:
            data_frame.to_sql(table_name, db_connection, 
                if_exists='append',
                chunksize=5000,
                index=True)
        except ValueError as vx:
            print('vx')
        except Exception as ex:
            print('ex')
        else:
            print('"Table %s appended successfully." % table_name')
        finally:
            db_connection.close()

    def to_sql_replace(df, connection, table_name):
        """ Replaces dataframe on mysql table. """
        print('Starting to replace dataframe on database.')
        nome_da_tabela = table_name
        # print('df)
        dataFrame = df
        # Helping while in development. Shall be removed before Merge.
        # print('df)
        sql_engine = create_engine(connection)
        db_connection = sql_engine.connect()
        try:
            dataFrame.to_sql(
                nome_da_tabela, db_connection,
                if_exists='replace',
                index=False,
                chunksize=5000,
                method='multi'
            )
        finally:
            db_connection.close()

# create a function to scrape team performance for multiple years
def scrape_NBA_team_data(years = [2021]):
    
    final_df = pd.DataFrame(columns = ["Year", "Team", "W", "L",
                                       "W/L%", "GB", "PS/G", "PA/G",
                                       "SRS", "Playoffs",
                                       "Losing_season"])
    
    # loop through each year
    for y in years:
        # NBA season to scrape
        year = y
        
        # URL to scrape, notice f string:
        url = f"https://www.basketball-reference.com/leagues/NBA_{year}_standings.html"
        
        # collect HTML data
        html = urlopen(url)
        
        # create beautiful soup object from HTML
        soup = BeautifulSoup(html, features="lxml")
        
        # use getText()to extract the headers into a list
        titles = [th.getText() for th in soup.findAll('tr', limit=2)[0].findAll('th')]
        
        # first, find only column headers
        headers = titles[1:titles.index("SRS")+1]
        
        # then, exclude first set of column headers (duplicated)
        titles = titles[titles.index("SRS")+1:]
        
        # next, row titles (ex: Boston Celtics, Toronto Raptors)
        try:
            row_titles = titles[0:titles.index("Eastern Conference")]
        except: row_titles = titles
        # remove the non-teams from this list
        for i in headers:
            row_titles.remove(i)
        row_titles.remove("Western Conference")
        divisions = ["Atlantic Division", "Central Division",
                     "Southeast Division", "Northwest Division",
                     "Pacific Division", "Southwest Division",
                     "Midwest Division"]
        for d in divisions:
            try:
                row_titles.remove(d)
            except:
                print("no division:", d)
        
        # next, grab all data from rows (avoid first row)
        rows = soup.findAll('tr')[1:]
        team_stats = [[td.getText() for td in rows[i].findAll('td')]
                    for i in range(len(rows))]
        # remove empty elements
        team_stats = [e for e in team_stats if e != []]
        # only keep needed rows
        team_stats = team_stats[0:len(row_titles)]
        
        # add team name to each row in team_stats
        for i in range(0, len(team_stats)):
            team_stats[i].insert(0, row_titles[i])
            team_stats[i].insert(0, year)
            
        # add team, year columns to headers
        headers.insert(0, "Team")
        headers.insert(0, "Year")
        
        # create a dataframe with all aquired info
        year_standings = pd.DataFrame(team_stats, columns = headers)
        
        # add a column to dataframe to indicate playoff appearance
        year_standings["Playoffs"] = ["Y" if "*" in ele else "N" for ele in year_standings["Team"]]
        # remove * from team names
        year_standings["Team"] = [ele.replace('*', '') for ele in year_standings["Team"]]
        # add losing season indicator (win % < .5)
        year_standings["Losing_season"] = ["Y" if float(ele) < .5 else "N" for ele in year_standings["W/L%"]]
        
        # append new dataframe to final_df
        final_df = final_df.append(year_standings)

    # export to csv
    final_df.to_csv("nba_team_data.csv", index=False)
    return final_df