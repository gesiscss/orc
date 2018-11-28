import csv
import os


def get_created_by_gesis():
    csv_file = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'created_by_gesis.csv')
    with open(csv_file, 'r') as f:
        reader = csv.reader(f)
        header = next(reader)
        created_by_gesis = list(reader)
    return created_by_gesis



