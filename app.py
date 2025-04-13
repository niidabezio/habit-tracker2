from flask import Flask, render_template, request, redirect
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
    user_id = 1  # 仮のユーザーID（ログイン機能がないので固定）

    if request.method == 'POST':
        action = request.form['action']

        if action == '食事を記録' or action == 'これ食べた！':
            name = request.form['name']
            calorie = float(request.form['calorie'])
            salt = float(request.form['salt'])
            time_str = request.form.get('time') or datetime.now().strftime('%H:%M')
            time_obj = datetime.strptime(time_str, '%H:%M').time()

            today = datetime.now().date()
            record = Record.query.filter_by(record_date=today, user_id=user_id).first()
            if not record:
                record = Record(record_date=today, user_id=user_id)
                db.session.add(record)
                db.session.commit()

            food = FoodItem(name=name, calorie=calorie, salt=salt, time=time_obj, record_id=record.id)
            db.session.add(food)
            db.session.commit()

            return redirect('/record')

        elif action == '体重を記録':
            weight = float(request.form['weight'])
            today = datetime.now().date()
            record = Record.query.filter_by(record_date=today, user_id=user_id).first()
            if not record:
                record = Record(record_date=today, weight=weight, user_id=user_id)
                db.session.add(record)
            else:
                record.weight = weight
            db.session.commit()
            return redirect('/record')

        # 🟡 ここがGET処理（画面を表示）
    recent_items = FoodItem.query.order_by(FoodItem.id.desc()).limit(20).all()

    # 🕒 今日の日付と現在時刻
    today_date = datetime.now().strftime('%Y年%m月%d日')
    now_time = datetime.now().strftime('%H:%M')

    # 👤 仮のユーザー（ID=1）を取得
    user = User.query.get(1)

    # 🔥 今日の記録とカロリー合計
    today = datetime.now().date()
    record = Record.query.filter_by(record_date=today, user_id=user.id).first()

    total_calorie = 0
    if record and record.food_items:
        total_calorie = sum([f.calorie for f in record.food_items])

    # 🎯 目標カロリー（体重ベースのざっくり計算）
    goal_calorie = int(22 * user.weight + 200)

    # 📤 HTML に渡す変数
    return render_template(
        'record.html',
        recent_items=recent_items,
        current_time=now_time,
        today_date=today_date,
        total_calorie=total_calorie,
        goal_calorie=goal_calorie
    )

@app.route('/history')
def history():
    return render_template('history.html')
@app.route('/delete_food/<int:food_id>', methods=['POST'])
def delete_food(food_id):
    food = FoodItem.query.get(food_id)
    if food:
        db.session.delete(food)
        db.session.commit()
    return redirect('/record')

# サーバー起動（開発モード）
if __name__ == '__main__':
    app.run(debug=True)
