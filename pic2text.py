#language_preference = ['fi'] #,'en','se']

import photos, ui, dialogs, clipboard
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

UIImage = ObjCClass('UIImage')
UIImageSymbolConfiguration = ObjCClass('UIImageSymbolConfiguration')

root = ui.View(
    tint_color='black',
)
  
results_table = ui.TableView(
    allows_multiple_selection=True,
    frame=root.bounds, flex='WH',
)

#WEIGHTS
ULTRALIGHT, THIN, LIGHT, REGULAR, MEDIUM, SEMIBOLD, BOLD, HEAVY, BLACK = range(1, 10)
# SCALES
SMALL, MEDIUM, LARGE = 1, 2, 3

def SymbolImage(name, point_size=None, weight=None, scale=None):
    ''' Create a ui.Image from an SFSymbol name. Optional parameters:
        * `point_size` - Integer font size
        * `weight` - Font weight, one of ULTRALIGHT, THIN, LIGHT, REGULAR, MEDIUM, SEMIBOLD, BOLD, HEAVY, BLACK
        * `scale` - Size relative to font size, one of SMALL, MEDIUM, LARGE 
        
    Run the file to see a symbol browser.'''
    objc_image = ObjCClass('UIImage').systemImageNamed_(name)
    conf = UIImageSymbolConfiguration.defaultConfiguration()
    if point_size is not None:
        conf = UIImageSymbolConfiguration.configurationWithConfiguration_and_(
            conf,
            UIImageSymbolConfiguration.configurationWithPointSize_(point_size))
    if weight is not None:
        conf = UIImageSymbolConfiguration.configurationWithConfiguration_and_(
            conf,
            UIImageSymbolConfiguration.configurationWithWeight_(weight))
    if scale is not None:
        conf = UIImageSymbolConfiguration.configurationWithConfiguration_and_(
            conf,
            UIImageSymbolConfiguration.configurationWithScale_(scale))
    objc_image = objc_image.imageByApplyingSymbolConfiguration_(conf)
    
    return ui.Image.from_data(
        nsdata_to_bytes(ObjCInstance(UIImagePNGRepresentation(objc_image)))
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
        self.selected_rows = set()
        
        self.camera_button = ui.ButtonItem(
          tint_color='black',
          image=SymbolImage('camera', 8, weight=THIN),
          action=partial(
              self.get_photo_action,
              picker_camera
          )
        )
        self.photos_button = ui.ButtonItem(
          tint_color='black',
          image=SymbolImage('photo.on.rectangle', 8, weight=THIN),
          action=partial(
              self.get_photo_action,
              picker_photos
          )
        )
        self.copy_button = ui.ButtonItem(
          tint_color='black',
          title='Copy',
          enabled=False,
          action=self.copy_action
        )
        self.share_button = ui.ButtonItem(
          tint_color='black',
          title='Share',
          enabled=False,
          action=self.share_action
        )
      
        root.left_button_items = [
            self.copy_button,
            self.share_button,
        ]
        root.right_button_items = [
            self.camera_button,
            self.photos_button,
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
            self.selected_rows = set()
            self.copy_button.enabled = True
            self.share_button.enabled = True
            self.tableview.reload()
        else:
            self.copy_button.enabled = False
            self.share_button.enabled = False
            dialogs.hud_alert('Failed to recognize anything')
        
    def copy_action(self, sender):
        text = self.get_text()
        if text is None:
            return
        clipboard.set(text)
        dialogs.hud_alert('Copied')
        
    def share_action(self, sender):
        text = self.get_text()
        if text is None:
            return
        dialogs.share_text(text)
        
    def get_text(self):
        if len(self.recognized_text) == 0:
            None
        if len(self.selected_rows) == 0:
            to_combine = self.recognized_text
        else:
            to_combine = [
                self.recognized_text[i]
                for i
                in sorted(self.selected_rows)
            ]
        return '\n'.join(to_combine)
                
        
    def tableview_number_of_rows(self, tableview, section):
        return len(self.recognized_text)
        
    def tableview_cell_for_row(self, tableview, section, row):
        cell = ui.TableViewCell()
        cell.text_label.text = self.recognized_text[row]

        return cell

    def tableview_did_select(self, tableview, section, row):
        self.selected_rows.add(row)
        
    def tableview_did_deselect(self, tableview, section, row):
        self.selected_rows.remove(row)
  
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
