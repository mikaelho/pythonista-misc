import console
import editor

import wkwebview


console.clear()

class BrythonRunner(wkwebview.WKWebView):
    
    def _message(self, message):
        level, content = message['level'], message['content']
        
        if level not in ['code', 'raw']:
            if content == 'using indexedDB for stdlib modules cache':
                print('Brython started')
                return
            
            if level.upper() == 'LOG':
                print(content)
                return
        
        super()._message(message)    
          
python_code = editor.get_text()

wv = BrythonRunner()

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
print(f'Running Python {sys.version}')
</script>

<script type="text/python">
'''

html_end = '''

</script>


</body>

</html>
'''

html = html_start + python_code + html_end

wv.load_html(html)

