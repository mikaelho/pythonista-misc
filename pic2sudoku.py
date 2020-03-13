#language_preference = ['fi'] #,'en','se']

import photos, ui, dialogs, clipboard
import io, ctypes
from functools import partial
from objc_util import *

load_framework('Vision')
VNRecognizeTextRequest = ObjCClass('VNRecognizeTextRequest')
VNDetectRectanglesRequest = ObjCClass('VNDetectRectanglesRequest')
VNImageRequestHandler = ObjCClass('VNImageRequestHandler')

(picker_photos, picker_camera) = (0, 1)

UIImagePNGRepresentation = c.UIImagePNGRepresentation
UIImagePNGRepresentation.argtypes = [ctypes.c_void_p]
UIImagePNGRepresentation.restype = ctypes.c_void_p

def imagePickerController_didFinishPickingMediaWithInfo_(self,cmd,picker,info):
    
    global root

    pick = ObjCInstance(picker)
    pick.setDelegate_(None)
    ObjCInstance(self).release()
    pick.dismissViewControllerAnimated_completion_(True, None)
    
    img = ObjCInstance(info)['UIImagePickerControllerEditedImage']   
    png_data = ObjCInstance(UIImagePNGRepresentation(img.ptr))
    root.process(png_data)

    
SUIViewController = ObjCClass('SUIViewController')

MyPickerDelegate = create_objc_class('MyPickerDelegate',
methods=[imagePickerController_didFinishPickingMediaWithInfo_], protocols=['UIImagePickerControllerDelegate'])

class SudokuProcessor(ui.View):
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.imageview = ui.ImageView(
            frame=self.bounds, flex='WH',
            content_mode=ui.CONTENT_SCALE_ASPECT_FIT)
        self.add_subview(self.imageview)
        
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
      
        self.left_button_items = [
            self.copy_button,
            self.share_button,
        ]
        self.right_button_items = [
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

        vc = SUIViewController.viewControllerForView_(self.objc_instance)
        vc.presentModalViewController_animated_(picker, True)

    def process(self, image_data):
        ui_image = ui.Image.from_data(nsdata_to_bytes(image_data))
        self.imageview.image = ui_image
        
        overlay = ui.View()
        wim, him = ui_image.size
        ws, hs = self.imageview.frame.size
        if (ws/hs) < (wim/him):
            h = ws*him/wim
            overlay.frame = (0,(hs-h)/2,ws,h)
        else:
            w = hs*wim/him
            overlay.frame = ((ws-w)/2,0,w,hs)
        self.imageview.add_subview(overlay)
    
        req = VNDetectRectanglesRequest.alloc().init().autorelease()
        #req.maximumObservations = 100
        handler = VNImageRequestHandler.alloc().initWithData_options_(
            image_data, None
        ).autorelease()
        success = handler.performRequests_error_([req], None)
        if success:
            results = req.results()
            if len(results) == 0:
                dialogs.hud_alert('Failed to find rectangle')
                return
            bbox = self.to_rect(
                req.results()[0].boundingBox())
            bbox = ui.Rect(0,0,1,1)
            recognized_matrix = self.recognize(image_data, bbox)
            ui_bbox = self.to_ui_rect(bbox)
            #imagecontext
            big_box = ui.View(
                frame=(
                    ui_bbox[0]*overlay.width,
                    ui_bbox[1]*overlay.height,
                    ui_bbox[2]*overlay.width,
                    ui_bbox[3]*overlay.height,
                )
            )
            overlay.add_subview(big_box)
            dim_x = big_box.width/9
            dim_y = big_box.height/9
            for col in range(9):
                for row in range(9):
                    small_box = ui.Label(
                        text=str(recognized_matrix[row][col]),
                        text_color='red',
                        border_color='red',
                        border_width=1,
                        frame=(
                            col*dim_x,
                            row*dim_y,
                            dim_x,
                            dim_y
                        )
                    )
                    big_box.add_subview(small_box)

            self.copy_button.enabled = True
            self.share_button.enabled = True
        else:
            self.copy_button.enabled = False
            self.share_button.enabled = False
            dialogs.hud_alert('Failed to recognize anything')
        
    def recognize(self, image_data, bbox):
        dim_x = bbox.width/9
        dim_y = bbox.height/9
        matrix = list()
        for row in range(9):
            r = list()
            matrix.insert(0, r)
            for col in range(9):
                region = CGRect(
                    CGPoint(
                        bbox.x + col*dim_x + dim_x/15,
                        bbox.y + row*dim_y + dim_y/15),
                    CGSize(dim_x/15*13, dim_y/15*13),
                )
                req = VNRecognizeTextRequest.alloc().init().autorelease()
                req.regionOfInterest = region
                req.customWords = ['1','2','3','4','5','6','7','8','9']
                handler = VNImageRequestHandler.alloc().initWithData_options_(
                    image_data, None
                ).autorelease()
                success = handler.performRequests_error_([req], None)
                if success:
                    results = req.results()
                    print('-'*20)
                    print(row, col)
                    for res in results:
                        print('[', res.text(), res.confidence(), ']')
                    if len(results) == 0:
                        result = 0
                    else:
                        try:
                            result = int(str(results[0].text()))
                        except:
                            result = 0
                else:
                    result = 0
                r.append(result)
        print(matrix)
        return matrix
        
    def to_rect(self, objc_bbox):
        orig = objc_bbox.origin
        size = objc_bbox.size
        rect = ui.Rect(orig.x, orig.y, size.width, size.height)
        return rect
        
    def to_ui_rect(self, rect):
        rect = ui.Rect(rect.x, 1.0-(rect.y+rect.height), rect.width, rect.height)
        return rect
        
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
        
UIImage = ObjCClass('UIImage')
UIImageSymbolConfiguration = ObjCClass('UIImageSymbolConfiguration')

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
        
root = SudokuProcessor(
    tint_color='black',
)

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
