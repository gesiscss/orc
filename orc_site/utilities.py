import csv


def get_created_by_gesis():
    with open('created_by_gesis.csv', 'r') as f:
        reader = csv.reader(f)
        header = next(reader)
        created_by_gesis = list(reader)
    return created_by_gesis



