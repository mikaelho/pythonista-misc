#language_preference = ['fi'] #,'en','se']

import photos, ui, dialogs, clipboard
import io
from objc_util import *

load_framework('Vision')
VNRecognizeTextRequest = ObjCClass('VNRecognizeTextRequest')
VNImageRequestHandler = ObjCClass('VNImageRequestHandler')

#revision = VNRecognizeTextRequest.currentRevision()
#supported = VNRecognizeTextRequest.supportedRecognitionLanguagesForTextRecognitionLevel_revision_error_(0, revision, None)
#print(supported)

#print('Getting picture')

class RecognizedTextSource:
    
    def __init__(self, root, tableview, **kwargs):
        super().__init__(**kwargs)
        self.tableview = tableview
        self.recognized_text = []
        
        self.camera_button = ui.ButtonItem(
          tint_color='black',
          image=ui.Image('iob:camera_32'),
          action=self.from_camera,
        )
        self.photos_button = ui.ButtonItem(
          tint_color='black',
          image=ui.Image('iob:ios7_photos_32'),
          action=self.from_photos,
        )
      
        root.left_button_items = [
            self.photos_button
        ]
        root.right_button_items = [
            self.camera_button
        ]
        
    def from_camera(self, sender):
        pil_image = None
        pil_image = photos.capture_image()
        self.recognize(pil_image)
        
    def from_photos(self, sender):
        pil_image = None
        pil_image = photos.pick_asset().get_image()
        self.recognize(pil_image)
        
    def recognize(self, pil_image):
        if pil_image is None:
            dialogs.hud_alert('Canceled')
            return
        dialogs.hud_alert('Converting image')
        buffer = io.BytesIO()
        pil_image.save(buffer, format='PNG')
        image_data = buffer.getvalue()

        req = VNRecognizeTextRequest.alloc().init().autorelease()
    
        dialogs.hud_alert('Recognizing')
    
        handler = VNImageRequestHandler.alloc().initWithData_options_(
            image_data, None
        ).autorelease()

        success = handler.performRequests_error_([req], None)
        if success:
            self.recognized_text = [
                str(result.text())
                for result
                in req.results()
            ]
            self.tableview.reload()
            dialogs.hud_alert('Done')
        else:
            dialogs.hud_alert('Failed to recognize anything')
        
    def tableview_number_of_rows(self, tableview, section):
        return len(self.recognized_text)
        
    def tableview_cell_for_row(self, tableview, section, row):
        cell = ui.TableViewCell()
        cell.text_label.text = self.recognized_text[row]

        return cell

    def tableview_did_select(self, tableview, section, row):
        clipboard.set(self.recognized_text[row])
        dialogs.hud_alert('Copied')
  
root = ui.View()
  
results_table = ui.TableView(
    frame=root.bounds, flex='WH',
)
results_table.data_source = results_table.delegate = RecognizedTextSource(
    root, results_table)

root.add_subview(results_table)

root.present()
