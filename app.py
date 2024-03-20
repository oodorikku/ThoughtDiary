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

POSITIVE_EMOTION_TEXT = "positive"
NEGATIVE_EMOTION_TEXT = "negative"
positive_emotion = ["joy", "admiration", "amusement", "caring", "excitement", "gratitude", "love", "relief", "surprise", "curiosity"]
negative_emotion = ["anger", "fear", "disgust", "sadness", "nervousness", "pride", "grief", "annoyance", "confusion", "desire", "disappointment"]
emotion = pipeline('sentiment-analysis', model='arpanghoshal/EmoRoBERTa')
#ref https://www.verywellmind.com/how-to-be-more-positive-6499974
positive_methods = ["Make a gratitude journal where you write the things you are thankful of", "Look for an activity you are looking forward to", "Practice smiling to boost your mood", "Positive self-talk"]
#ref https://www.verywellmind.com/how-should-i-deal-with-negative-emotions-3144603
negative_methods = ["Understand your emotions", "Change what you can like your thought patterns", "Find an outlet or a hobby", "Learn to accept yourself"]
user_entries = []
#if user feels a specific emotion for 3 consecutive days, it will be stored here
emotion_patterns = ""
#On user's 7 recent diary entries, we check if user feels more negative or positive emotions, and we put it here.
#weekly_emotion = ""

def check_for_emotion_patterns():
    negative_counter = 0
    positive_counter = 0
    #consecutive_days = 0
    #global weekly_emotion
    global emotion_patterns
    i = 1
    if user_entries:
        previous_emotion = "neutral"
        print('=============')
        print(user_entries)
        for entry in user_entries:
            current_emotion = entry['emotion']
            if current_emotion in positive_emotion:
                positive_counter  += 1
            elif current_emotion in negative_emotion:
                negative_counter += 1
            # Check if the current entry has the same emotion as the previous one
            print("Current" + current_emotion)
            print("Previous" + previous_emotion)
            '''
            if current_emotion == previous_emotion:
                consecutive_days += 1
            else:
                consecutive_days = 1  # Reset consecutive days count if emotions differ
            if consecutive_days == 3:
                emotion_patterns = current_emotion
            '''
            if i == 5:
                if positive_counter >= 3:
                    #weekly_emotion = "positive"
                    emotion_patterns = POSITIVE_EMOTION_TEXT
                elif negative_counter >= 3:
                    #weekly_emotion = "negative"
                    emotion_patterns = NEGATIVE_EMOTION_TEXT
                
                positive_counter = 0
                negative_counter = 0

            previous_emotion = current_emotion
            i += 1


@app.route('/')
def login():
    return render_template('login.html')
    #return render_template('index2.html')

@app.route('/login_to_index', methods=['POST'])
def login_to_index():
    return redirect(url_for('index2'))

@app.route('/main')
def index2():
    '''
        if emotion_patterns == POSITIVE_EMOTION_TEXT:
        return render_template('index.html', user_entries=user_entries, emotion_patterns = emotion_patterns, emotion_methods = positive_methods)
    return render_template('index.html', user_entries=user_entries, emotion_patterns = emotion_patterns, emotion_methods = negative_methods)
    '''
    return render_template('index2.html', user_entries=user_entries, emotion_patterns = emotion_patterns, emotion_methods = positive_methods)

@app.route('/add_entry', methods=['POST'])
def add_entry():
    global user_entries
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

        #To sort the entries by date
        user_entries = sorted(user_entries, key=lambda x: x['date'], reverse = True) 

        check_for_emotion_patterns()

    return redirect(url_for('index2'))

@app.route('/delete_entry/<int:id>', methods=['POST'])
def delete_entry(id):
    global user_entries
    user_entries = [entry for entry in user_entries if entry['id'] != id]
    return redirect(url_for('index2'))

@app.route('/edit_entry/<int:entry_id>')
def edit_entry(entry_id):
    entry_to_edit = next((entry for entry in user_entries if entry['id'] == entry_id), None)
    return render_template('edit_entry.html', entry=entry_to_edit)

#only updates one entry
@app.route('/update_entry/<int:entry_id>', methods=['POST'])
def update_entry(entry_id):
    entry_to_update = next((entry for entry in user_entries if entry['id'] == entry_id), None)
    if entry_to_update:
        entry_to_update['date'] = request.form['date']
        entry_to_update['title'] = request.form['title']
        entry_to_update['content'] = request.form['content']
        entry_to_update['emotion'] = emotion(request.form['content'])[0]['label']

    return redirect(url_for('index2'))

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