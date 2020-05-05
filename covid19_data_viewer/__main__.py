from csv import reader
from matplotlib import pyplot
from matplotlib.ticker import FuncFormatter
import datetime
import urllib.request
import multiprocessing

class Columns:
    COUNTRY_NAME = 0
    COUNTRY_CODE = 1
    DATE = 2
    NEW_CASES = 3
    NEW_DEATHS = 4
    POPULATION = 5
    TOTAL_CASES = 6
    TOTAL_DEATHS = 7
    DEATH_RATE = 8
    INFECTION_RATE = 9
    CASES_DIV_MILLION = 10
    DEATHS_DIV_MILLION = 11
    
    labels_by_columns = {
        TOTAL_CASES: 'Total Cases',
        TOTAL_DEATHS: 'Total Deaths',
        DEATH_RATE: 'Percent of Cases Resulting in Death',
        INFECTION_RATE: 'Percent of Population Infected',
        CASES_DIV_MILLION: 'Number of Cases Per 1 Million Population',
        DEATHS_DIV_MILLION: 'Number of Deaths Per 1 Million Population',
    }

    column_types = {
        '1': TOTAL_CASES,
        '2': TOTAL_DEATHS,
        '3': DEATH_RATE,
        '4': INFECTION_RATE,
        '5': CASES_DIV_MILLION,
        '6': DEATHS_DIV_MILLION,
    }

    column_headers = [
        COUNTRY_NAME,
        COUNTRY_CODE,
        DATE,
        NEW_CASES,
        NEW_DEATHS,
        POPULATION,
        TOTAL_CASES,
        TOTAL_DEATHS,
        DEATH_RATE,
        INFECTION_RATE,
        CASES_DIV_MILLION,
        DEATHS_DIV_MILLION,
    ]

    @staticmethod
    def get_column_num(column_name):
        return Columns.column_headers.index(column_name)

    @staticmethod
    def get_label(column_num):
        return Columns.labels_by_columns[column_num]

class World_Data:
    def __init__(self, data):
        self.columns = Columns()
        self.world_data = {}
        self.comparable_countries = []
        self.country_codes = {}
        self.country_names = {}
        
        for row in data:
            country_name_full = row[6].replace('_',' ').upper()
            country_code = row[8]
            self.country_codes[country_name_full] = country_code
            self.country_names[country_code] = country_name_full

            if country_code not in self.world_data.keys():
                self.world_data[country_code] = []
            self.world_data[country_code].insert(0, get_important_data(row))

        for country in self.world_data:
            rows = self.world_data[country]
            total_cases = rows[0][Columns.get_column_num(Columns.NEW_CASES)]
            total_deaths = rows[0][Columns.get_column_num(Columns.NEW_DEATHS)]
            rows[0].insert(len(rows[0]), total_cases)
            rows[0].insert(len(rows[0]), total_deaths)      
            rows[0].insert(len(rows[0]), divide_safe(total_deaths, total_cases) * 100)
            rows[0].insert(len(rows[0]), divide_safe(total_cases, rows[0][Columns.get_column_num(Columns.POPULATION)]) * 100)
            rows[0].insert(len(rows[0]), divide_safe(total_cases, rows[0][Columns.get_column_num(Columns.POPULATION)] / 1000000))
            rows[0].insert(len(rows[0]), divide_safe(total_deaths, rows[0][Columns.get_column_num(Columns.POPULATION)] / 1000000))
            
            for i in range(1, len(rows)):
                new_cases = rows[i][Columns.get_column_num(Columns.NEW_CASES)]
                new_deaths = rows[i][Columns.get_column_num(Columns.NEW_DEATHS)]
                population = rows[i][Columns.get_column_num(Columns.POPULATION)]
                
                rows[i].insert(len(rows[i]), total_cases + new_cases)
                rows[i].insert(len(rows[i]), total_deaths + new_deaths)
                
                total_cases += new_cases
                total_deaths += new_deaths
                
                rows[i].insert(len(rows[i]), divide_safe(total_deaths, total_cases) * 100)
                rows[i].insert(len(rows[i]), divide_safe(total_cases, population) * 100)
                rows[i].insert(len(rows[i]), divide_safe(total_cases, population / 1000000))
                rows[i].insert(len(rows[i]), divide_safe(total_deaths, population / 1000000))

        # self.comparable_countries = [k for k in self.world_data.keys() if self.world_data[k][0][Columns.DATE] == '31/12/2019' and datetime.date.today() == datetime.datetime.strptime(self.world_data[k][-1][Columns.DATE],'%d/%m/%Y').date()]
        self.comparable_countries = [k for k in self.world_data.keys() if set(self.get_column_data(k, Columns.DATE)) == set(self.get_column_data('USA', Columns.DATE))]
    
    def plot_graph(self, country_code, column_num):
        figure, axes = pyplot.subplots()
        axes.ticklabel_format(style='plain')
        formatter = FuncFormatter(add_commas)
        axes.yaxis.set_major_formatter(formatter)

        xdata = xdata = self.get_column_data(country_code, Columns.DATE)
        ydata = self.get_column_data(country_code, column_num)
        pyplot.plot(xdata, ydata, color='red')
        pyplot.title(f'{Columns.get_label(column_num)}: {self.country_names[country_code]}')
        pyplot.xlabel('Date')
        pyplot.ylabel(Columns.get_label(column_num))
        pyplot.xticks(rotation=-90)
        pyplot.show()

    def plot_two_graphs(self, country_code1, country_code2, column_num):        
        figure, axes = pyplot.subplots()
        axes.ticklabel_format(style='plain')
        formatter = FuncFormatter(add_commas)
        axes.yaxis.set_major_formatter(formatter)

        xdata = self.get_column_data(country_code1, Columns.DATE)
        ydata1 = self.get_column_data(country_code1, column_num)
        ydata2 = self.get_column_data(country_code2, column_num)
        
        pyplot.plot(xdata, ydata1, color='blue', label=country_code1)
        pyplot.plot(xdata, ydata2, color='red', label=country_code2)
        pyplot.legend(loc='upper left')
        pyplot.title(f'{Columns.get_label(column_num)}: {self.country_names[country_code1]} vs {self.country_names[country_code2]}')
        pyplot.xlabel('Date')
        pyplot.ylabel(Columns.get_label(column_num))
        pyplot.xticks(rotation=-90)
        pyplot.show()

    def get_country_code_by_name(self, country_name):
        return self.country_codes[country_name]

    def get_country_name_by_code(self, country_code):
        return self.country_names[country_code]

    def get_column_data(self, country_code, column_num):
        country_data = self.world_data[country_code]
        column_data = [data[column_num] for data in country_data]

        if (column_num == Columns.DATE):
            column_data = [datetime.datetime.strptime(d,'%d/%m/%Y').date() for d in column_data]

        return column_data

    def print_country(self, countryCode):
        countryCode = countryCode.upper()
        print(countryCode)
        for row in self.world_data[countryCode]:
            print(row)

    def print_dict(self):
        for k in self.world_data.keys():
            print(k)
            for v in self.world_data[k]:
                print(v)

    def print_country_names_and_codes(self):
        print('\n\n\tAll Countries:\n')
        for name, code in self.country_codes.items():
            print(f'\t{name}:\t{code}')

    def print_comparable_countries(self):
        print('\n\n\tComparable Countries:\n')
        for country_code in self.comparable_countries:
            print(f'\t{self.country_names[country_code]}:\t{country_code}')

def divide_safe(numerator, denominator):
    return 0 if denominator == 0 else numerator / denominator

def string_to_int(string):
    return 0 if string == '' else int(string)

def get_important_data(row):
    # [country, code, date, new cases, new deaths, population]
    code = row[8] if row[8] != '' else row[7]
    return [row[6], code, row[0], string_to_int(row[4]), string_to_int(row[5]), string_to_int(row[9])]

def add_commas(x, pos):
    return '{:,.0f}'.format(x)

def get_last_index(listy):
    return len(listy)

def get_country_code_input(country_codes):
    country_code = input('\n    Please enter the ABBREVIATION of the desired country (or \'b\' to go back): ').upper()
    while (country_code not in country_codes and country_code.lower() != 'b'):
        country_code = input('\n    Hmmm, was there a typo?\n    Please enter the ABBREVIATION of the desired country (or \'b\' to go back): ').upper()
    print(f'    Selected: {country_code}')
    return country_code

def get_graph_type_input():
    graph_type_prompt = '''
    Graph Types:
    '1': Total Cases
    '2': Total Deaths
    '3': Percent of Cases Resulting in Death
    '4': Percent of Population Infected
    '5': Number of Cases Per 1 Million Population
    '6': Number of Deaths Per 1 Million Population

    Please enter the desired graph type number (or 'b' to go back): '''
    graph_type = input(graph_type_prompt)
    while (graph_type not in Columns.column_types.keys() and graph_type.lower() != 'b'):
        graph_type = input('\n    Hmmm, was there a typo?\n    ' + graph_type_prompt)
    print(f'    Selected: {graph_type}')
    return graph_type

def start_comparison_graph_process(world_data, country_code1, country_code2, column_num):
    if (country_code1 not in world_data.comparable_countries or country_code2 not in world_data.comparable_countries):
        raise(Exception('Cannot compare the selected countries'))

    process = multiprocessing.Process(None, world_data.plot_two_graphs, args=(country_code1, country_code2, column_num), daemon=True)
    process.start()
    return process

def start_graph_process(world_data, country_code1, column_num):
    process = multiprocessing.Process(None, world_data.plot_graph, args=(country_code1, column_num), daemon=True)
    process.start()
    return process




def main():
    url = 'https://opendata.ecdc.europa.eu/covid19/casedistribution/csv'

    print(f'\n    fetching data from {url}...')
    response = urllib.request.urlopen(url)
    
    print('    parsing csv...')
    data = response.read()
    text = data.decode('utf-8')
    data = [line.split(',') for line in text.split('\r\n')][1:]

    print('    organizing data...')
    world_data = World_Data(data)
    
    print('\n    Welcome!\n    All data used is obtained from:\n    https://www.ecdc.europa.eu/en/publications-data/download-todays-data-geographic-distribution-covid-19-cases-worldwide')
    
    initial_prompt = '''
    Command List:
    'n' for list of all country names and abbreviations
    'c' for list of comparable countries

    'g' to plot a graph
    'd' to plot a graph comparing two countries (both countries must be found in the 'Comparable Countries' list)
    't' to print Tasi's favorite 4 graphs

    'q' to quit

    Please type a command: '''

    user_input = ''
    while user_input != 'q':
        user_input = input(initial_prompt).lower()

        if user_input == 'q':
            print('q')

        elif user_input =='n':
            world_data.print_country_names_and_codes()
        
        elif user_input =='c':
            world_data.print_comparable_countries()
        
        elif user_input =='g':
            country_code = get_country_code_input(world_data.world_data.keys())            
            if (country_code.lower() == 'b'):
                continue
            
            graph_type = get_graph_type_input()
            if (graph_type.lower() == 'b'):
                continue
            column_num = Columns.column_types[graph_type]

            # world_data.plot_graph(country_code, column_num)

            try: 
                process = start_graph_process(world_data, country_code, column_num)
            except:
                print("\n\n    ERROR: One of the countries is not in the 'Comparable Countries' list. Please try again.\n")
                continue

        elif user_input =='d':
            print('\n    First country:')
            country_code1 = get_country_code_input(world_data.world_data.keys())
            if (country_code1.lower() == 'b'):
                continue
            print('\n    Second country:')
            country_code2 = get_country_code_input(world_data.world_data.keys())
            if (country_code2.lower() == 'b'):
                continue
            graph_type = get_graph_type_input()
            if (graph_type.lower() == 'b'):
                continue
            column_num = Columns.column_types[graph_type]
            
            try:
                process = start_comparison_graph_process(world_data, country_code1, country_code2, column_num)
            except:
                print("\n\n    ERROR: One of the countries is not in the 'Comparable Countries' list. Please try again.\n")
                continue
        
        elif user_input =='t':
            process = start_comparison_graph_process(world_data, 'USA', 'ITA', Columns.TOTAL_CASES)
            process = start_comparison_graph_process(world_data, 'USA', 'ITA', Columns.DEATH_RATE)
            process = start_comparison_graph_process(world_data, 'USA', 'ITA', Columns.CASES_DIV_MILLION)
            process = start_comparison_graph_process(world_data, 'USA', 'ITA', Columns.DEATHS_DIV_MILLION)
        
if __name__ == '__main__':
    multiprocessing.freeze_support()
    main()


