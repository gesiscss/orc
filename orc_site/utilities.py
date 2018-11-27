import csv


def get_created_by_gesis():
    with open('Gesis.csv', 'r') as f:
        reader = csv.reader(f)
        created_by_gesis = list(reader)
    return created_by_gesis



