import csv
import datetime



def write_to_csv(phone_number, weight, success):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open('data.csv', 'a') as file:
        writer = csv.writer(file, delimiter = ',', lineterminator = '\n')
        writer.writerow([phone_number, weight, success, timestamp])

write_to_csv(83233863, 1600, True)
