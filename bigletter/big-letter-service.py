import random

colors = (
    '#ccffcc',
    '#ccffff',
    '#ccccff',
    '#ffcccc',
    '#ffffcc',
)
fonts = (
    'Arial',
    'Arial Black',
    'Verdana',
    'Helvetica',
    'Courier',
)

def letter_handler(event, context=None):
    '@awslambda @html'
    
    try:
        letter = event['queryParams']['letter']
    except KeyError:
        letter = 'Ö'
    
    color = random.choice(colors)
    font = random.choice(fonts)
    font = 'Arial Black'
    
    return f'''
        <!doctype html>
        <html>
            <head>
                <meta charset="utf-8">
                <title></title>
                <style type='text/css'>
                    body {{
                        text-align: center;
                        background-color: {color};
                        font-size: 10vmin;
                        font-family: {font};
                    }}
                </style>
                <script>
                    function init() {{
                        window.addEventListener('resize', onResize, false);
                        window.addEventListener('onrotate', onResize, false);
                        onResize();
                    }}
                    
                    function onResize() {{
                        const canvas = document.getElementsByTagName('canvas')[0];
                        canvas.width = window.innerWidth;
                        canvas.height = window.innerHeight;
                        const ctx = canvas.getContext('2d');
                        const text = '{letter}';
                        ctx.fillStyle = 'black';
                        ctx.font = '10px {font}';
                        msr = ctx.measureText(text);
                        cont_min = Math.min(canvas.clientWidth, canvas.clientHeight);
                        new_size = Math.min(Math.round(10 * cont_min / msr.width), canvas.clientHeight);
                        ctx.font = ''+new_size+'px {font}';
                        //ctx.textBaseline = 'middle';
                        ctx.textAlign = 'center';
                        ctx.fillText(text, canvas.clientWidth/2, canvas.clientHeight-((canvas.clientHeight-new_size)/2)-25);
                        
                    }}
                </script>
            </head>
            
            <body onLoad='init()'>
                <canvas width='100%' height='100%'>
                </canvas>
            </body
        </html>
        '''
    
if __name__ == '__main__':
    import ui
    wv = ui.WebView()
    wv.present(hide_title_bar=True)
    html = letter_handler({})
    wv.load_html(html)
