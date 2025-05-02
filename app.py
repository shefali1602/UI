from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import pandas as pd
from rapidfuzz import process, fuzz

app = Flask(__name__, template_folder="templates")

global_found=""

def load_excel(file_path, sheet_name=None):
    return pd.read_excel(file_path, sheet_name=sheet_name)

metadata_df = load_excel(r"Knowledge_Area_Artifacts.xlsx", sheet_name='Sheet1')

metadata_df.columns = metadata_df.columns.str.strip()
metadata_df = metadata_df.map(lambda x:x.strip() if isinstance(x,str) else x)

app.secret_key = "GTSBOT"


def get_response(user_input):
    knowledge_area = metadata_df['Knowledge Area'].tolist()
    matches = process.extract(user_input, knowledge_area, scorer=fuzz.WRatio, limit=5)
    if not matches:
        return[]
    closest_match, score, _=matches[0]
    response = metadata_df.loc[metadata_df['Knowledge Area']== closest_match]
    return response, score

def handle_exit():
    return {
        'chat_list': [('Bot', 'Thank you for using Infentora. Have a wonderful day. Goodbye!')],
        'disabled_ui': "disabled='disabled'"
    }

@app.route('/')
def index():
    if 'chat_dic' not in session:
        session['chat_dic'] = {}
    if 'chat_list'not in session['chat_dic']:
        session['chat_dic']['chat_dic'] = [('Bot','Hi there! I am Infentora. I can help you with you KT')]
    if 'links' not in session['chat_dic']:
        session['chat_dic']['links']=[]


    chat_dic ={}

    if 'chat_dic' in session:
        chat_dic = session['chat_dic']

    return render_template('index.html', **chat_dic)  

@app.route('/chat', methods=['POST'])
def chat():
    user_input = request.form['user_input']

    chat_dic = session.get('chat_dic', {})
    chat_list = chat_dic.get('chat_list', [])

    chat_list.append(('User', user_input))
    chat_dic['chat_list'] = chat_list
    session['chat_dic'] = chat_dic

    if user_input.lower() in ['yes', 'yep']:
        if len(chat_list) >= 2 and chat_list[-2][1].startswith('Sorry'):
            last_keyword = chat_list[-2][1].split()[2]
            res, sco = get_response(last_keyword)
            typ = res['Type'].unique()
            chat_list.append(('Bot', '', typ.tolist()))
            session['chat_dic']['chat_list'] = chat_list
            return render_template('index.html', **session['chat_dic'])

    if user_input.lower() == "exit":
        chat_dic = handle_exit()
        session['chat_dic'] = chat_dic
        return render_template('index.html', **chat_dic)


    if user_input.lower() in ["no", "nope"]:
        chat_list.append(('Bot', "Sorry, I couldn't find any matches. Please try again."))
        session['chat_dic']['chat_list'] = chat_list
        return render_template('index.html', **session['chat_dic'])

    if user_input.lower() in ['hi', 'hello', 'hey']:
        chat_list.append(('Bot', 'Hello there! Just tell me what you are looking to learn today?'))
        session['chat_dic']['chat_list'] = chat_list
        return render_template('index.html', **session['chat_dic'])

    responses, score = get_response(user_input)

    if not responses.empty:
        if score < 80:
            chat_list.append(('Bot', f"Sorry, I couldn't find an exact match. Did you mean '{responses.iloc[0]['Knowledge Area']}'?"))
            session['chat_dic']['chat_list'] = chat_list
            return render_template('index.html', **session['chat_dic'])

        types = responses['Type'].unique()
        chat_list.append(('Bot', '', types.tolist()))
        session['chat_dic']['chat_list'] = chat_list
        global global_found
        global_found = responses.iloc[0]['Knowledge Area']
        return render_template('index.html', **session['chat_dic'])

    return jsonify({"message": "Sorry, I could not find any matching terms. Please try again.", "suggestion": False})

@app.route('/reset')
def reset():
    session.clear()  # clear all session data
    return redirect(url_for('index'))  # always go to home page

@app.route('/exit')
def exit_chat():
    chat_dic = handle_exit()
    session['chat_dic'] = chat_dic
    return render_template('index.html', **chat_dic)


def get_formatted_output(duration, sme, links):
    html_data = "Duration: " + duration +"<br>SME: " + sme + "<br>"

    links_arr = links.split("\n")

    links = ""

    for i in links_arr:
        links += f"<a href='{i}' target='_blank'>{i}</a><br>"

    links = " Artifacts Links: <BR>" + links

    html_data = html_data + links
    return html_data

if __name__ == '__main__':
    app.run(debug=True)

    
        
        

      

