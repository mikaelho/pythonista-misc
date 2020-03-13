import ui

import onedriver
import onedrive_ids

driver = onedriver.OneDriver(
    onedrive_ids.client_id,
    onedrive_ids.client_secret)
    
def select_which_to_delete(one, two):
    one_name = one['name']
    one_path = one['parentReference']['path'][len('/drive/root:'):]
    two_name = two['name']
    two_path = two['parentReference']['path'][len('/drive/root:'):]
    print('1', one_path, one_name)
    print('2', two_path, two_name)
    while True:
        response = input('1 or 2 to delete, s to skip, q to quit')
        if response not in ['1', '2', 's', 'q']: continue
        if response == '1':
            print('Deleting')
            return one
        elif response == '2':
            print('Deleting')
            return two
        elif response == 's':
            print('Skipping')
            return None
        elif response == 'q':
            print('Stopping')
            raise StopIteration()
    
def print_path(folder, full_path):
    print(full_path)
    
driver.deduplicate('Paperit',
    decision_callback=select_which_to_delete,
    info_callback=print_path)
    
