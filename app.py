from flask import Flask, render_template, request, redirect, url_for, jsonify
from transformers import RobertaTokenizerFast, TFRobertaForSequenceClassification, pipeline
from flask import flash
from datetime import datetime
import speech_recognition as sr
import secrets

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

tokenizer = RobertaTokenizerFast.from_pretrained("arpanghoshal/EmoRoBERTa")
model = TFRobertaForSequenceClassification.from_pretrained("arpanghoshal/EmoRoBERTa")

emotion = pipeline('sentiment-analysis', model='arpanghoshal/EmoRoBERTa')

user_entries = []

@app.route('/')
def index():
    return render_template('index.html', user_entries=user_entries)

@app.route('/add_entry', methods=['POST'])
def add_entry():
    date = request.form['date']
    title = request.form['title']
    content = request.form['content']

    existing_entry = next((entry for entry in user_entries if entry['date'] == date), None)

    if existing_entry:
        flash(f"You have already added a diary entry for {datetime.strptime(date, '%Y-%m-%d').strftime('%B %d, %Y')}.")
    else:
        entry_emotion = emotion(content)[0]['label']
        entry = {
            'id': len(user_entries) + 1,
            'date': date,
            'title': title,
            'content': content,
            'emotion': entry_emotion
        }
        user_entries.append(entry)

    return redirect(url_for('index'))

@app.route('/delete_entry/<int:id>', methods=['POST'])
def delete_entry(id):
    global user_entries
    user_entries = [entry for entry in user_entries if entry['id'] != id]
    return redirect(url_for('index'))

@app.route('/edit_entry/<int:entry_id>')
def edit_entry(entry_id):
    entry_to_edit = next((entry for entry in user_entries if entry['id'] == entry_id), None)
    return render_template('edit_entry.html', entry=entry_to_edit)

@app.route('/update_entry/<int:entry_id>', methods=['POST'])
def update_entry(entry_id):
    entry_to_update = next((entry for entry in user_entries if entry['id'] == entry_id), None)
    if entry_to_update:
        entry_to_update['date'] = request.form['date']
        entry_to_update['title'] = request.form['title']
        entry_to_update['content'] = request.form['content']
        entry_to_update['emotion'] = emotion(request.form['content'])[0]['label']

    return redirect(url_for('index'))

@app.route('/speech_to_text', methods=['POST'])
def speech_to_text():
    recognizer = sr.Recognizer()

    try:
        with sr.Microphone() as source:
            print("Say something...")
            audio = recognizer.listen(source, timeout=5)

        content = recognizer.recognize_google(audio)
        return jsonify({"content": content})
    except sr.UnknownValueError:
        print("Speech recognition could not understand audio")
        return jsonify({"error": "Speech recognition could not understand audio"})
    except sr.WaitTimeoutError:
        return jsonify({"error": "Speech recognition timed out while waiting for phrase to start"})
    except sr.RequestError as e:
        return jsonify({"error": f"Could not request results from Google Speech Recognition service; {e}"})

if __name__ == '__main__':
    app.run(debug=True)
