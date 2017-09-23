"""
Your task is to write a python program to do the following:
    1) For each inspection for each facility on a single page of results from the Napa county health
       department website (url given below), scrape the following information:
       - Facility name
       - Address (just street info, not city, state, or zip)
       - City
       - State
       - Zipcode
       - Inspection date
       - Inspection type
       - For each out-of-compliance violation type, scrape the violation type number and corresponding description.
         For example, an inspection might contain violation type numbers 6 and 7, and descriptions
         "Adequate handwashing facilities supplied & accessible" and "Proper hot and cold holding temperatures"
    2) Place this information in a database of some sort. You can use whatever you want; sqlite, postgres, mongodb, etc.
       Organize the data in a fashion which seems the most logical and useful to you. Include in your result the
       necessary instructions to set up this database, such as create table statements.
    3) Fetch this information from the database, and print it to the console in some fashion which clearly
       and easily displays the data you scraped.

We have provided a little bit of code using the lxml and sqlite to get you started,
but feel free to use whatever method you would like.
"""

"""
Modified by: Natasha Petrus (NatashaTPetrus@gmail.com)

Notes:
1. Syntax used: Python3 --> if using Python2, there'll be some syntax errors
    (e.g. 'print()' only works in Python3, whereas 'print' only works in Python2)
2. Required package: texttable --> to display table after fetching data from the database
"""

from lxml import html
from lxml.html import tostring
import sqlite3 as sql
from sqlite3 import Error
from texttable import Texttable # package to display neat table --> "texttable" !! MUST !! be installed


page_url = (
    "http://ca.healthinspections.us/napa/search.cfm?start=1&1=1&sd=01/01/1970&ed=03/01/2017&kw1=&kw2=&kw3="
    "&rel1=N.permitName&rel2=N.permitName&rel3=N.permitName&zc=&dtRng=YES&pre=similar"
)


def setup_db():
    conn = establish_connection()
    c = conn.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS report (facility TEXT, address TEXT, city TEXT, state TEXT, zipcode INTEGER, "
              "inspection_date TEXT, inspection_type TEXT, violation_number INTEGER, violation_description TEXT);")
    # c.close()
    return c


def establish_connection(): # to handle error
    try:
        conn = sql.connect("exercise.db")
        return conn
    except Error as e:
        print(e)


def insert_into_db(cur, data):
    db = ''' INSERT INTO report (facility, address, city, state, zipcode, inspection_date, inspection_type, violation_number, violation_description)
              VALUES(?,?,?,?,?,?,?,?,?) '''
    cur.execute(db, data)


def fetch_db(cur):
    cur.execute("SELECT * FROM report")
    return cur.fetchall()


def display_table(database_content):
    t = Texttable()
    t.set_cols_width([10,10,10,5,7,10,10,11,25]) # set individual column width
    t.add_row(['Facility', 'Address', 'City', 'State', 'Zipcode', 'Inspection Date', 'Inspection Type', 'Violation#', 'Violation Description'])
    for data in database_content:
        t.add_row(list(data[0:9]))
    print(t.draw())


def scrape(cur):
    root = html.parse(page_url)
    search_links = root.xpath(".//a[contains(@href,'_report_full.cfm?domainID=')]/@href") # array of full inspection report links
    for url in search_links:
        parsed = html.parse("http://ca.healthinspections.us/" + url[3:]) # ignore "../", start from "_template/"
        # for facility name
        facility = parsed.xpath(".//span[1]/text()")[0]
        # for address
        full_address = parsed.xpath(".//span[5]/text()") # contains e.g. "['1313 MAIN ST \r\nNAPA, CA 94559 ']"
        full_address = full_address[0].split('\r\n', 1) # contains e.g. "['1313 MAIN ST', 'NAPA, CA 94559 ']"
        address = full_address[0]
        # for city
        city_state_zipcode = full_address[1] # contains e.g. "NAPA, CA 94559"
        city = city_state_zipcode.split(',', 1)[0]
        # for state
        state_zipcode = city_state_zipcode.split(',', 1)[1].lstrip() # contains e.g. "CA 94559" --> lstrip to remove beginning whitespaces
        state = state_zipcode.split(' ', 1)[0]
        # for zipcode
        zipcode = state_zipcode.split(' ',1)[1]
        # for inspection date
        inspection_date = parsed.xpath(".//span[3]/text()")[0] # extract the text only, not list
        # for inspection type
        inspection_type = parsed.xpath(".//span[10]/text()")[0] #extract the text only, not list
        # for each of out-of-compliance violations
        out_of_compliance_checkboxes = parsed.xpath(".//table[contains(@class,'insideTable')]//tr[not(@id) and not(@class)]/td[3]/img/@src")
        out_of_compliance_descriptions = parsed.xpath(".//table[contains(@class,'insideTable')]//tr[not(@id) and not(@class)]/td[1]/text()")
        for index, checkbox in enumerate(out_of_compliance_checkboxes):
            if "unchecked" not in checkbox: # if out-of-compliance box is checked
                violation = out_of_compliance_descriptions[index] # contains e.g. "6. Adequate handwashing facilities supplied & accessible"
                violation_number = violation.split('. ',1)[0]
                violation_description = violation.split('. ',1)[1]
                # insert each into database
                row_data = (facility, address, city, state, zipcode, inspection_date, inspection_type, violation_number, violation_description);
                insert_into_db(cur, row_data)


def main():
    cur = setup_db()
    scrape(cur)
    database_content = fetch_db(cur)
    display_table(database_content)
    cur.close()


if __name__ == '__main__':
    main()
