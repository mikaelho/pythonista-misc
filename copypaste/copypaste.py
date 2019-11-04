clip = None

def handler(event, context):
    '''
    @awslambda
    '''
    global clip
    
    clip_in = event['queryParams'].get('clip', None)
    if clip_in:
        clip = clip_in
        return clip_in
    else:
        clip_out = clip
        clip = None
        return clip_out

'''
Windows:
    
Copy to cloud:
    powershell -sta "add-type -as System.Windows.Forms; $text_to_copy = [uri]::EscapeDataString([windows.forms.clipboard]::GetText()); (Invoke-WebRequest """https://uxyv0k54q5.execute-api.eu-west-1.amazonaws.com/prod/?clip=$text_to_copy""").Content"
    
Copy from cloud:
    powershell -sta "Write-Output (Invoke-WebRequest """https://uxyv0k54q5.execute-api.eu-west-1.amazonaws.com/prod/""").Content | Set-Clipboard"
'''
