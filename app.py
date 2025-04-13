from flask import Flask, render_template, request
from models import db, User
from datetime import datetime
from models import FoodItem, Record

app = Flask(__name__)

# PostgreSQLに接続する設定
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:niida0@localhost:5432/habit_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# DB初期化
db.init_app(app)
from flask_migrate import Migrate

migrate = Migrate(app, db)

# ルートページの表示（動作確認用）
@app.route('/')
def home():
    return render_template('index.html')


@app.route('/profile', methods=['GET', 'POST'])
def profile():
    if request.method == 'POST':
        # 入力された内容をPythonの変数に取り出す
        gender = request.form['gender']
        age = int(request.form['age'])
        height = float(request.form['height'])
        weight = float(request.form['weight'])

        # データベースに保存する
        new_user = User(gender=gender, age=age, height=height, weight=weight)
        db.session.add(new_user)
        db.session.commit()

        return "プロフィール登録が完了しました！"
    else:
        return render_template('profile.html')

@app.route('/record', methods=['GET', 'POST'])
def record():
    if request.method == 'POST':
        action = request.form['action']

        if action == '食事を記録' or action == 'これ食べた！':
            name = request.form['name']
            calorie = float(request.form['calorie'])
            salt = float(request.form['salt'])
            time_str = request.form.get('time') or datetime.now().strftime('%H:%M')
            time_obj = datetime.strptime(time_str, '%H:%M').time()

            food = FoodItem(name=name, calorie=calorie, salt=salt, time=time_obj)
            db.session.add(food)
            db.session.commit()

            return redirect('/record')

        elif action == '体重を記録':
            weight = float(request.form['weight'])
            today = datetime.now().date()

            # Recordを日付で1件だけ作る／更新する
            record = Record.query.filter_by(record_date=today).first()
            if not record:
                record = Record(record_date=today, weight=weight)
                db.session.add(record)
            else:
                record.weight = weight
            db.session.commit()

            return redirect('/record')

    # 過去の食事履歴を取得
    recent_items = FoodItem.query.order_by(FoodItem.id.desc()).limit(20).all()
    now_time = datetime.now().strftime('%H:%M')
    return render_template('record.html', recent_items=recent_items, current_time=now_time)

@app.route('/history')
def history():
    return render_template('history.html')

# サーバー起動（開発モード）
if __name__ == '__main__':
    app.run(debug=True)
