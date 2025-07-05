import pandas as pd
import os
from db_handling.communicate import *

def export_session_messages_csv(session_id):
    session_doc = get_session_by_id(session_id)

    if not session_doc or 'messages' not in session_doc:
        return {'success' : False, 'error' : 'Session not found or has no messages'}
    
    messages = session_doc['messages']

    #creating dataframe#
    df = pd.DataFrame(messages)
    return df
    


