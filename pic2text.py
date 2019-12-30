#language_preference = ['fi'] #,'en','se']

import photos, ui, dialogs, clipboard, appex
import io, ctypes
from functools import partial
from objc_util import *

load_framework('Vision')
VNRecognizeTextRequest = ObjCClass('VNRecognizeTextRequest')
VNImageRequestHandler = ObjCClass('VNImageRequestHandler')

(picker_photos, picker_camera) = (0, 1)

UIImagePNGRepresentation = c.UIImagePNGRepresentation
UIImagePNGRepresentation.argtypes = [ctypes.c_void_p]
UIImagePNGRepresentation.restype = ctypes.c_void_p

root = ui.View()
  
results_table = ui.TableView(
    frame=root.bounds, flex='WH',
)

def imagePickerController_didFinishPickingMediaWithInfo_(self,cmd,picker,info):
    
    global results_table

    pick = ObjCInstance(picker)
    pick.setDelegate_(None)
    ObjCInstance(self).release()
    pick.dismissViewControllerAnimated_completion_(True, None)
    
    img = ObjCInstance(info)['UIImagePickerControllerEditedImage']   
    png_data = ObjCInstance(UIImagePNGRepresentation(img.ptr))
    results_table.data_source.recognize(png_data)

    
SUIViewController = ObjCClass('SUIViewController')

MyPickerDelegate = create_objc_class('MyPickerDelegate',
methods=[imagePickerController_didFinishPickingMediaWithInfo_], protocols=['UIImagePickerControllerDelegate'])

class RecognizedTextSource:
    
    def __init__(self, root, tableview, **kwargs):
        super().__init__(**kwargs)
        self.tableview = tableview
        self.recognized_text = []
        
        self.camera_button = ui.ButtonItem(
          tint_color='black',
          image=ui.Image('iob:camera_32'),
          action=partial(
              self.get_photo_action,
              picker_camera
          )
        )
        self.photos_button = ui.ButtonItem(
          tint_color='black',
          image=ui.Image('iob:ios7_photos_32'),
          action=partial(
              self.get_photo_action,
              picker_photos
          )
        )
      
        root.left_button_items = [
            self.photos_button
        ]
        root.right_button_items = [
            self.camera_button
        ]
        
    @on_main_thread
    def get_photo_action(self, picker_type, sender):
        picker = ObjCClass('UIImagePickerController').alloc().init()
        
        delegate = MyPickerDelegate.alloc().init()
        picker.setDelegate_(delegate)
        
        picker.allowsEditing = True
        picker.sourceType = picker_type

        vc = SUIViewController.viewControllerForView_(
            self.tableview.superview.objc_instance)
        vc.presentModalViewController_animated_(picker, True)

    def recognize(self, image_data):
        req = VNRecognizeTextRequest.alloc().init().autorelease()
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
  
results_table.data_source = results_table.delegate = RecognizedTextSource(
    root, results_table)

root.add_subview(results_table)

root.present()

'''
OLD LANGUAGE-RELATED CODE
Nothing but English supported...

#revision = VNRecognizeTextRequest.currentRevision()
#supported = VNRecognizeTextRequest.supportedRecognitionLanguagesForTextRecognitionLevel_revision_error_(0, revision, None)
#print(supported)


OLD PHOTO PICKING CODE
Uses Pythonista modules. Easy, readable and very slow.

    def from_camera(self, sender):
        pil_image = None
        pil_image = photos.capture_image()
        self.convert_image(pil_image)
        
    def from_photos(self, sender):
        pil_image = None
        asset = photos.pick_asset()
        if asset is not None:
            pil_image = asset.get_image()
        self.convert_image(pil_image)
        
    @ui.in_background
    def convert_image(self, pil_image):
        if pil_image is None:
            dialogs.hud_alert('Canceled')
            return
        dialogs.hud_alert('Converting image')
        buffer = io.BytesIO()
        pil_image.save(buffer, format='PNG')
        image_data = buffer.getvalue()
        self.recognize(image_data)
'''
