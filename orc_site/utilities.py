import csv


def process_gesis_data():
    data = csv.reader(open('Gesis.csv'))
    next(data,None)
    created_by_gesis = []
    for line in data:
        created_by_gesis.append(tuple(line))
    return created_by_gesis



