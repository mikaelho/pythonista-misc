import console
from objc_util import on_main_thread, NSURL
import editor
import os.path

import wkwebview


html_start = '''
<!doctype html>
<html>

<head>
    <meta charset="utf-8">
    <script type="text/javascript"
        src="https://cdn.jsdelivr.net/npm/brython@3.8.9/brython.min.js">
    </script>
    <script type="text/javascript" src="https://cdn.jsdelivr.net/npm/brython@3.8.9/brython_stdlib.js"></script>
</head>

<body onload="brython()">

<script type="text/python">
import sys
print(f'Running Python {sys.version}\\n\\n-----------------------------\\n')
</script>

<script type="text/python">
'''

html_end = '''

</script>


</body>

</html>
'''
    

def main():
    console.clear()
    
    class BrythonRunner(wkwebview.WKWebView):
        
        @on_main_thread
        def load_html(self, html):
            # Need to set a base directory to get
            # real js errors
            current_working_directory = os.path.dirname(editor.get_path())
            root_dir = NSURL.fileURLWithPath_(current_working_directory)
            self.webview.loadHTMLString_baseURL_(html, root_dir)
        
        def _message(self, message):
            level, content = message['level'], message['content']
            
            if level not in ['code', 'raw']:
                if content == 'using indexedDB for stdlib modules cache':
                    #print('Brython started')
                    return
                
                if level.upper() == 'LOG':
                    print(content,
                    end=('' if content.endswith('\n') else '\n'))
                    return
            
            super()._message(message)    
              
    python_code = editor.get_text()
    
    wv = BrythonRunner()
    
    html = html_start + python_code + html_end
    
    wv.load_html(html)

if __name__ == '__main__':
    
    main()
