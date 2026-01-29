try:
    from vika import Vika
except:
    pass
import pandas as pd
import multitasking
from time import sleep
import threading
import traceback

def get(datasheet_id, token):
    if not datasheet_id:
        return pd.DataFrame()

    records_arr = []
    vika = Vika(token)
    datasheet = vika.datasheet(datasheet_id, field_key='name')
    try:
        records = datasheet.records.all()
        for record in records:
            record_obj = record.json()
            record_obj['_id'] = record._id
            records_arr.append(record_obj)
        return pd.DataFrame(records_arr)
    except:
        return pd.DataFrame()
    
def update(datasheet_id, token, kv):
    records_arr = []
    vika = Vika(token)
    datasheet = vika.datasheet(datasheet_id, field_key='name')
    row = datasheet.records.get(ID=kv['ID'])
    row.update(kv)

class VikaManager():
    def __init__(self, token):
        self.vika = Vika(token)
        self.tasks = []
        self.update_data = {}
        self.UPDATE_LEN_LIMIT = 10
        self.loop = True

    def get(self, datasheet_id):
        records_arr = []
        vika = self.vika
        datasheet = vika.datasheet(datasheet_id, field_key='name')
        try:
            records = datasheet.records.all()
            for record in records:
                records_arr.append(record.json())
            return pd.DataFrame(records_arr)
        except:
            return pd.DataFrame()
        
    def update(self, datasheet_id, records, task=False):
        vika = self.vika
        datasheet = vika.datasheet(datasheet_id, field_key='name')
        record_arr = []
        for record in records:
            record_id = record['_id']
            del(record['_id'])
            record_arr.append({'recordId': record_id, 'fields': record})
            if task:
                if not datasheet_id in self.update_data:
                    self.update_data[datasheet_id] = {}
                if not record_id in self.update_data[datasheet_id]:
                    self.update_data[datasheet_id][record_id] = {}
                for k, v in record.items():
                    self.update_data[datasheet_id][record_id][k] = v

        if not task:
            datasheet.update_records(record_arr)

    def task_run(self):
        vika = self.vika
        for datasheet_id, records in self.update_data.items():
            datasheet = vika.datasheet(datasheet_id, field_key='name')
            record_arr = []
            for record_id, record_fields in records.items():
                record_arr.append({'recordId': record_id, 'fields': record_fields})
            index = 0
            while index < len(record_arr):
                datasheet.update_records(record_arr[index:index+self.UPDATE_LEN_LIMIT])
                index += self.UPDATE_LEN_LIMIT
                sleep(1) # 20230707增加 vika好像限制了1秒一次请求
        
        # 复位数据
        self.update_data = {}
            
    @multitasking.task
    def run_task_interval(self, interval=3):
        self.loop = True
        while self.loop:
            # print(f'run,{threading.current_thread().ident}')
            try:
                self.task_run()
            except:
                traceback.print_exc()
            sleep(interval)

    def stop_task_interval(self):
        self.loop = False


class VikaTask():
    def __init__(self, fn):
        self.fn = fn
        self.runed = False

    def run(self):
        self.runed = True
        self.fn()
    

# get('dstWUZMkiVg81oYhEn')