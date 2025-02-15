## I'm not a developer so will try to add the missing endpoints using assistance
## from Windsurf.

## experimented with adding rules as in training video
## downloaded core-editor-rules.md file from GitHub with example rules.
https://gist.github.com/yifanzz/3cfb8f9065769ffbf94348255f85597d#file-code-editor-rules-md
Asked Windsurf how to add these rules.
Added contents of file to .windsurfrules for the workspace rules.
Asked Windsurf to update it's memory with the file contents and that completed okay.

Asked Windsurf the commands to create the database, returned:
cd /Users/corey/Documents\ -\ Local/Training/GenAI_Bootcamp/local-dev/lang-portal/backend-flask && python3 -c "
from app import create_app
from lib.db import Db

# Create Flask app
app = create_app()

# Initialize the database
db = Db()
db.init(app)
print('Database initialized successfully!')
"

## test db creation with no other setup
Accepted the answer but the environment was not initialized.

##  Created environment with:

cd /Users/corey/Documents\ -\ Local/Training/GenAI_Bootcamp/local-dev/lang-portal/backend-flask && python3 -m venv venv

## Installed the dependencies
cd /Users/corey/Documents\ -\ Local/Training/GenAI_Bootcamp/local-dev/lang-portal/backend-flask && source venv/bin/activate && pip install -r requirements.txt

## Created the database
cd /Users/corey/Documents\ -\ Local/Training/GenAI_Bootcamp/local-dev/lang-portal/backend-flask && source venv/bin/activate && python3 -c "
from app import create_app
from lib.db import Db

# Create Flask app
app = create_app()

# Initialize the database
db = Db()
db.init(app)
print('Database initialized successfully!')
"

## db setup summary
## Windsurf provided a summary of the steps that were performed:
1. Created a virtual environment
2. Installed all required dependencies from requirements.txt
3. Initialized the database, which:
    * Created all necessary tables
    * Imported Core Verbs (60 verbs)
    * Imported Core Adjectives (64 verbs)
    * Imported Study Activities
The database file words.db is now created in the backend-flask directory.

## Connect to database and verify
Next, setup dbeaver to connect to the words.db sqllite3 database and was able to view the tables and data okay.
￼

## Configured terminal session to activate the environment
source /Users/corey/Documents\ -\ Local/Training/GenAI_Bootcamp/local-dev/lang-portal/backend-flask/venv/bin/activate

## Additionally created an alias in .zshrc file
cp -p $HOME/.zshrc $HOME/.zshrc_before_windsurf

echo "alias activate_lang_portal='source /Users/corey/Documents\ -\ Local/Training/GenAI_Bootcamp/local-dev/lang-portal/backend-flask/venv/bin/activate'" >> ~/.zshrc

## Test database access in newly activated environment


## List all tables
.tables
## show example table structure/ddl
.schema words
## query from sample tables.
SELECT * FROM words LIMIT 10;
SELECT * FROM groups;
SELECT * FROM study_activities;
.quit

## try to run the backend-flask application

source /Users/corey/Documents\ -\ Local/Training/GenAI_Bootcamp/local-dev/lang-portal/backend-flask/venv/bin/activate

cd /Users/corey/Documents\ -\ Local/Training/GenAI_Bootcamp/local-dev/lang-portal/backend-flask
python3 app.py

## Open browser to see if it is working
http://127.0.0.1:5000

## this failed with not found error, investigated and checked route information
## Tested various endpoint URLs and data was returned, examples
http://127.0.0.1:5000/api/study-activities
http://127.0.0.1:5000/dashboard/stats
http://127.0.0.1:5000/words

## Asked Windsurf to example these route in more detail.


## Moving onto the backend code as in the videos
## Attempted to add the missing APIs in the back-end code

## Asked Windsurf to find the missing entries:
1. In backend-flask/routes/study_sessions.py:
    * # todo /study_sessions POST: Implement POST endpoint for creating study sessions
    * # todo POST /study_sessions/:id/review: Implement review endpoint for a specific study session
2. In backend-flask/routes/groups.py:
    * # todo GET /groups/:id/words/raw: Implement endpoint to retrieve raw words for a specific group

Recommendations:
1. Implement the missing endpoints in study_sessions.py:
    * Create a POST endpoint for /study_sessions
    * Create a POST endpoint for /study_sessions/:id/review
2. Implement the missing endpoint in groups.py:
    * Create a GET endpoint for /groups/:id/words/raw

## Determine the specs for the request and adjusted prompt to modify the code:
## POST /api/study_activities
Request Params
* group_id integer
* study_activity_id integer
JSON Response
  { "id": 124, "group_id": 123 }

## Used Windsurf to help with adding:
@app.route('/api/study-sessions', methods=['POST'])
  @cross_origin()
  def create_study_session():
    try:
      # Get request data
      data = request.get_json()
      
      # Validate required fields
      required_fields = ['group_id', 'study_activity_id']
      for field in required_fields:
        if field not in data:
          return jsonify({"error": f"Missing required field: {field}"}), 400
      
      # Extract data
      group_id = data['group_id']
      study_activity_id = data['study_activity_id']
      
      # Optional: Add user_id if authentication is implemented
      user_id = g.user.id if hasattr(g, 'user') else None
      
      cursor = app.db.cursor()
      
      # Validate group exists
      cursor.execute('SELECT id FROM groups WHERE id = ?', (group_id,))
      if not cursor.fetchone():
        return jsonify({"error": "Invalid group_id"}), 404
      
      # Validate study activity exists
      cursor.execute('SELECT id FROM study_activities WHERE id = ?', (study_activity_id,))
      if not cursor.fetchone():
        return jsonify({"error": "Invalid study_activity_id"}), 404
      
      # Insert new study session
      cursor.execute('''
        INSERT INTO study_sessions 
        (group_id, study_activity_id, user_id, created_at) 
        VALUES (?, ?, ?, ?)
      ''', (group_id, study_activity_id, user_id, datetime.now()))
      
      # Get the ID of the newly created session
      session_id = cursor.lastrowid
      
      # Commit transaction
      app.db.commit()
      
      return jsonify({
        "group_id": group_id,
        "study_activity_id": study_activity_id
      }), 201
    
    except Exception as e:
      # Rollback transaction in case of error
      app.db.rollback()
      return jsonify({"error": str(e)}), 500

## Used Windsurf to add the next endpoint:
## Create a POST endpoint for /study_sessions/:id/review
## Code added:

# Implement POST endpoint for reviewing a study session
  @app.route('/api/study-sessions/<int:id>/review', methods=['POST'])
  @cross_origin()
  def review_study_session(id):
    try:
      # Get request data
      data = request.get_json() or {}
      
      cursor = app.db.cursor()
      
      # Validate study session exists
      cursor.execute('''
        SELECT 
          ss.id, 
          ss.created_at, 
          g.name as group_name, 
          sa.name as activity_name,
          COUNT(wri.id) as review_items_count
        FROM study_sessions ss
        JOIN groups g ON g.id = ss.group_id
        JOIN study_activities sa ON sa.id = ss.study_activity_id
        LEFT JOIN word_review_items wri ON wri.study_session_id = ss.id
        WHERE ss.id = ?
        GROUP BY ss.id
      ''', (id,))
      
      session = cursor.fetchone()
      if not session:
        return jsonify({"error": "Study session not found"}), 404
      
      # Calculate end time (for this example, we'll add 10 minutes to start time)
      start_time = session['created_at']
      end_time = datetime.fromisoformat(start_time) + timedelta(minutes=10)
      
      # Process review items if provided in the request
      if 'review_items' in data:
        try:
          cursor.executemany('''
            INSERT INTO word_review_items 
            (study_session_id, word_id, correct, review_timestamp) 
            VALUES (?, ?, ?, ?)
          ''', [
            (id, item['word_id'], item.get('correct', False), datetime.now())
            for item in data.get('review_items', [])
          ])
          app.db.commit()
        except Exception as e:
          app.db.rollback()
          return jsonify({"error": "Failed to process review items", "details": str(e)}), 400
      
      return jsonify({
        "id": session['id'],
        "activity_name": session['activity_name'],
        "group_name": session['group_name'],
        "start_time": start_time,
        "end_time": end_time.isoformat(),
        "review_items_count": session['review_items_count']
      }), 200
    
    except Exception as e:
      return jsonify({"error": str(e)}), 500


## Added the last missing endpoint:
## GET /groups/:id/words/raw: Implement endpoint to retrieve raw words for a specific group
## An include for math was added as well as the following code:
# Implement GET endpoint for retrieving raw words for a specific group
  @app.route('/groups/<int:id>/words/raw', methods=['GET'])
  @cross_origin()
  def get_group_raw_words(id):
    try:
      # Get pagination parameters
      page = request.args.get('page', 1, type=int)
      per_page = request.args.get('per_page', 100, type=int)
      offset = (page - 1) * per_page

      cursor = app.db.cursor()
      
      # Validate group exists
      cursor.execute('SELECT id FROM groups WHERE id = ?', (id,))
      if not cursor.fetchone():
        return jsonify({"error": "Group not found"}), 404
      
      # Get total count of words in the group
      cursor.execute('''
        SELECT COUNT(DISTINCT w.id) as total_items
        FROM words w
        JOIN group_words gw ON gw.word_id = w.id
        WHERE gw.group_id = ?
      ''', (id,))
      total_items = cursor.fetchone()['total_items']
      total_pages = math.ceil(total_items / per_page)
      
      # Retrieve words for the group with their review statistics
      cursor.execute('''
        SELECT 
          w.id,
          w.kanji as japanese,
          w.romaji,
          w.english,
          COALESCE(SUM(CASE WHEN wri.correct = 1 THEN 1 ELSE 0 END), 0) as correct_count,
          COALESCE(SUM(CASE WHEN wri.correct = 0 THEN 1 ELSE 0 END), 0) as wrong_count
        FROM words w
        JOIN group_words gw ON gw.word_id = w.id
        LEFT JOIN word_review_items wri ON wri.word_id = w.id
        WHERE gw.group_id = ?
        GROUP BY w.id
        ORDER BY w.kanji
        LIMIT ? OFFSET ?
      ''', (id, per_page, offset))
      
      words = cursor.fetchall()
      
      return jsonify({
        "items": [{
          "japanese": word['japanese'],
          "romaji": word['romaji'],
          "english": word['english'],
          "correct_count": word['correct_count'],
          "wrong_count": word['wrong_count']
        } for word in words],
        "pagination": {
          "current_page": page,
          "total_pages": total_pages,
          "total_items": total_items,
          "items_per_page": per_page
        }
      }), 200
    
    except Exception as e:
      return jsonify({"error": str(e)}), 500


## Generated test request bodies:

## /study_sessions:
{
  "group_id": 1,
  "study_activity_id": 2
}

## /study_sessions/:id/review
{
  "review_items": [
    {
      "word_id": 1,
      "correct": true
    },
    {
      "word_id": 2,
      "correct": false
    }
  ]
}

## /groups/:id/words/raw
## Test get request:
# Basic request
curl http://127.0.0.1:5000/groups/1/words/raw
# With pagination parameters
curl "http://127.0.0.1:5000/groups/1/words/raw?page=1&per_page=50"

## Start the back-end server:
cd /Users/corey/Documents\ -\ Local/Training/GenAI_Bootcamp/local-dev/lang-portal/backend-flask
python3 app.py

## After testing, it was determined that the groups.py code was invalid and using table_name
## group_words instead of word_groups.  Corrected these and was then able to access the
## endpoint successfully.
curl http://127.0.0.1:5000/groups/1/words/raw

## Next test the 2 new post endpoints:
## Test: /study_sessions POST

curl -X POST http://127.0.0.1:5000/api/study-sessions \
     -H "Content-Type: application/json" \
     -d '{"group_id": 1, "study_activity_id": 1}'

## this failed with many errors.
## Windsurf suggested this was due to missing the rollback() method.
## Added:
def rollback(self):
    # Rollback the current transaction
    self.get().rollback()

## Removed non-existant column study_sessions.user_id from the code
## Would look at providing table definitions to Windsurf in the future
## Test curl post now worked okay.
## Ran 3 times and checked data in study_sessions:
￼


## Test endpoint: /study_sessions/:id/review

curl -X POST http://127.0.0.1:5000/api/study-sessions/1/review \
     -H "Content-Type: application/json" \
     -d '{
         "review_items": [
             {"word_id": 1, "correct": true},
             {"word_id": 2, "correct": false}
         ]
     }'

## Received error: "table word_review_items has no column named review_timestamp"
## As above correct the code to match the table definitions.
## This time will try having Windsurf correct it using prompt:

Fix the code based on table word_review_items having the following definition:
CREATE TABLE word_review_items (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  word_id INTEGER NOT NULL,
  study_session_id INTEGER NOT NULL,  -- Link to study session
  correct BOOLEAN NOT NULL,  -- Whether the answer was correct (true) or wrong (false)
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,  -- Timestamp of the review
  FOREIGN KEY (word_id) REFERENCES words(id),
  FOREIGN KEY (study_session_id) REFERENCES study_sessions(id)
);

## Reviewed the changes to the insert statement and accepted them because they were correct.
## Re-tested the post request and the data was returned.

{
  "activity_name": "Typing Tutor",
  "end_time": "2025-02-12T17:56:55.175449",
  "group_name": "Core Verbs",
  "id": 1,
  "review_items_count": 0,
  "start_time": "2025-02-12 17:46:55.175449"
}