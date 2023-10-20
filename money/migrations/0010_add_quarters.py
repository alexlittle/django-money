import datetime
from django.db import migrations

QUARTERS = {
'2019 Q4': {'start_date': datetime.datetime(2019, 10, 1, 0, 0, 0),
           'end_date': datetime.datetime(2019, 12, 31, 23, 59, 59)},
'2020 Q1': {'start_date': datetime.datetime(2020, 1, 1, 0, 0, 0),
'end_date': datetime.datetime(2020, 3, 31, 23, 59, 59)},
'2020 Q2': {'start_date': datetime.datetime(2020, 4, 1, 0, 0, 0),
'end_date': datetime.datetime(2020, 6, 30, 23, 59, 59)},
'2020 Q3': {'start_date': datetime.datetime(2020, 7, 1, 0, 0, 0),
'end_date': datetime.datetime(2020, 9, 30, 23, 59, 59)},
'2020 Q4': {'start_date': datetime.datetime(2020, 10, 1, 0, 0, 0),
'end_date': datetime.datetime(2020, 12, 31, 23, 59, 59)},
'2021 Q1': {'start_date': datetime.datetime(2021, 1, 1, 0, 0, 0),
'end_date': datetime.datetime(2021, 3, 31, 23, 59, 59)},
'2021 Q2': {'start_date': datetime.datetime(2021, 4, 1, 0, 0, 0),
'end_date': datetime.datetime(2021, 6, 30, 23, 59, 59)},
'2021 Q3': {'start_date': datetime.datetime(2021, 7, 1, 0, 0, 0),
'end_date': datetime.datetime(2021, 9, 30, 23, 59, 59)},
'2021 Q4': {'start_date': datetime.datetime(2021, 10, 1, 0, 0, 0),
'end_date': datetime.datetime(2021, 12, 31, 23, 59, 59)},
'2022 Q1': {'start_date': datetime.datetime(2022, 1, 1, 0, 0, 0),
'end_date': datetime.datetime(2022, 3, 31, 23, 59, 59)},
'2022 Q2': {'start_date': datetime.datetime(2022, 4, 1, 0, 0, 0),
'end_date': datetime.datetime(2022, 6, 30, 23, 59, 59)},
'2022 Q3': {'start_date': datetime.datetime(2022, 7, 1, 0, 0, 0),
'end_date': datetime.datetime(2022, 9, 30, 23, 59, 59)},
'2022 Q4': {'start_date': datetime.datetime(2022, 10, 1, 0, 0, 0),
'end_date': datetime.datetime(2022, 12, 31, 23, 59, 59)},
'2023 Q1': {'start_date': datetime.datetime(2023, 1, 1, 0, 0, 0),
'end_date': datetime.datetime(2023, 3, 31, 23, 59, 59)},
'2023 Q2': {'start_date': datetime.datetime(2023, 4, 1, 0, 0, 0),
'end_date': datetime.datetime(2023, 6, 30, 23, 59, 59)},
'2023 Q3': {'start_date': datetime.datetime(2023, 7, 1, 0, 0, 0),
'end_date': datetime.datetime(2023, 9, 30, 23, 59, 59)},
'2023 Q4': {'start_date': datetime.datetime(2023, 10, 1, 0, 0, 0),
'end_date': datetime.datetime(2023, 12, 31, 23, 59, 59)},
'2024 Q1': {'start_date': datetime.datetime(2024, 1, 1, 0, 0, 0),
'end_date': datetime.datetime(2024, 3, 31, 23, 59, 59)},
'2024 Q2': {'start_date': datetime.datetime(2024, 4, 1, 0, 0, 0),
'end_date': datetime.datetime(2024, 6, 30, 23, 59, 59)},
'2024 Q3': {'start_date': datetime.datetime(2024, 7, 1, 0, 0, 0),
'end_date': datetime.datetime(2024, 9, 30, 23, 59, 59)},
'2024 Q4': {'start_date': datetime.datetime(2024, 10, 1, 0, 0, 0),
'end_date': datetime.datetime(2024, 12, 31, 23, 59, 59)},
}

def add_quarters(apps, schema_editor):
    AccountingPeriod = apps.get_model("money", "AccountingPeriod")
    for k in QUARTERS.keys():
        ap = AccountingPeriod()
        ap.start_date = QUARTERS[k]['start_date']
        ap.end_date = QUARTERS[k]['end_date']
        ap.title = k
        ap.save()

class Migration(migrations.Migration):

    dependencies = [
        ('money', '0009_rename_accountingperiods_accountingperiod'),
    ]

    operations = [
        migrations.RunPython(add_quarters),
    ]
