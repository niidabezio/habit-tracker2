from models import db, User, Record, FoodItem, FavoriteFood
from flask import Flask, render_template, request, redirect
from models import db, User
from datetime import datetime, timedelta
from models import FoodItem, Record
from models import FavoriteFood
from flask import session



app = Flask(__name__)
app.secret_key = '1234'  # セッションに必要（なんでもOK）


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

    if request.method == 'GET' and 'reset' in request.args:
        session.pop('user_id', None)
        return render_template('profile.html')

    if 'user_id' in session and request.method == 'GET':
        user = User.query.get(session['user_id'])

        # 同じ計算ロジック（繰り返しなので後で関数化してもOK）
        if user.gender == "男性":
            bmr = 10 * user.weight + 6.25 * user.height - 5 * user.age + 5
        else:
            bmr = 10 * user.weight + 6.25 * user.height - 5 * user.age - 161

        activity = 1.5
        ideal_calorie = int(bmr * activity)

        # 追加：理想のたんぱく質・塩分
        ideal_protein = round(user.weight * 1.2, 1)  # 体重×1.2g
        ideal_salt = 6.0  # g

        return render_template('profile_result.html',
                       user=user,
                       ideal_calorie=ideal_calorie,
                       bmr=bmr,
                       activity=activity,
                       ideal_protein=ideal_protein,
                       ideal_salt=ideal_salt)
    
    if request.method == 'POST':
        # 入力内容を取得
        gender = request.form['gender']
        age = int(request.form['age'])
        height = float(request.form['height'])
        weight = float(request.form['weight'])

        # ユーザー登録
        new_user = User(gender=gender, age=age, height=height, weight=weight)
        db.session.add(new_user)
        db.session.commit()

        # ✅ ユーザーIDをセッションに保存
        session['user_id'] = new_user.id

        # 計算（ハリス-ベネディクト式）
        if gender == "男性":
            bmr = 10 * weight + 6.25 * height - 5 * age + 5
        else:
            bmr = 10 * weight + 6.25 * height - 5 * age - 161

        activity = 1.5  # 一般的な活動レベル
        ideal_calorie = int(bmr * activity)

        # 追加：理想のたんぱく質・塩分
        ideal_protein = round(weight * 1.2, 1)
        ideal_salt = 6.0

        # 結果ページへ
        return render_template('profile_result.html',
                               user=new_user,
                               ideal_calorie=ideal_calorie,
                               bmr=bmr,
                               activity=activity,
                               ideal_protein=ideal_protein,
                               ideal_salt=ideal_salt
                            )
                               
        return render_template('profile.html')

@app.route('/record', methods=['GET', 'POST'])
def record():
    user_id = session.get('user_id')

    if not user_id:
        return redirect('/profile')  # 未登録ならプロフィールへ

    user = User.query.get(user_id)

    if request.method == 'POST':
        action = request.form.get('action')  # ← これなら「なかったら None」で止まらない！
        
        # 🔥 理想カロリーを再計算（プロフィールと同じ式）
        if user.gender == "男性":
            bmr = 10 * user.weight + 6.25 * user.height - 5 * user.age + 5
        else:
            bmr = 10 * user.weight + 6.25 * user.height - 5 * user.age - 161

        activity = 1.5  # ここも合わせる
        goal_calorie = int(bmr * activity)
        
        if action == '食事を記録' or action == '食':
            name = request.form['name']

            # 👇 ここから追加！
            calorie_str = request.form.get('calorie')
            calorie = float(calorie_str) if calorie_str and calorie_str != 'None' else 0

            salt_str = request.form.get('salt')
            salt = float(salt_str) if salt_str and salt_str != 'None' else 0

            protein_str = request.form.get('protein')
            protein = float(protein_str) if protein_str and protein_str != 'None' else 0
            # 👆 ここまで追加！

            time_str = request.form.get('time') or datetime.now().strftime('%H:%M')
            time_obj = datetime.strptime(time_str, '%H:%M').time()
            
            time_str = request.form.get('time') or datetime.now().strftime('%H:%M')
            time_obj = datetime.strptime(time_str, '%H:%M').time()

            today = datetime.now().date()
            record = Record.query.filter_by(record_date=today, user_id=user_id).first()
            if not record:
                record = Record(record_date=today, user_id=user_id)
                db.session.add(record)
                db.session.commit()

            food = FoodItem(name=name, calorie=calorie, protein=protein, salt=salt, time=time_obj, record_id=record.id)
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
        
        elif action == 'お気に入りに追加':
            print("お気に入り追加処理が呼ばれました")
            name = request.form['name']
            calorie = float(request.form['calorie'])
            salt = float(request.form['salt'])

            favorite = FavoriteFood(name=name, calorie=calorie, salt=salt, user_id=user_id)
            db.session.add(favorite)
            db.session.commit()
            return redirect('/record')

        # 🟡 ここがGET処理（画面を表示）
    today = datetime.now().date()
    record = Record.query.filter_by(record_date=today, user_id=user_id).first()

    # 今日食べたもの（FoodItem）を取り出す
    today_items = []  # ← ここを追加！
    if record:
        today_items = record.food_items

    recent_items = FoodItem.query.order_by(FoodItem.id.desc()).limit(20).all()
        # 🔽 重複を取り除く（名前が同じものは1つにする）
    unique_items = []
    seen_names = set()
    for item in recent_items:
        if item.name not in seen_names:
            unique_items.append(item)
            seen_names.add(item.name)
    favorite_items = FavoriteFood.query.filter_by(user_id=user_id).all()


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

    total_protein = 0
    if record and record.food_items:
        total_protein = sum([f.protein or 0 for f in record.food_items])

    # 🎯 目標カロリー（体重ベースのざっくり計算）
    if user.gender == "男性":
        bmr = 10 * user.weight + 6.25 * user.height - 5 * user.age + 5
    else:
        bmr = 10 * user.weight + 6.25 * user.height - 5 * user.age - 161
    activity = 1.5
    goal_calorie = int(bmr * activity)


    # 📤 HTML に渡す変数
    return render_template(
        'record.html',
        recent_items=unique_items,  # ← 重複なしのリストに！
        favorite_items=favorite_items,
        today_items=today_items,
        current_time=now_time,
        today_date=today_date,
        total_calorie=total_calorie,
        goal_calorie=goal_calorie
    )
@app.route('/delete_food/<int:food_id>', methods=['POST'])
def delete_food(food_id):
    food = FoodItem.query.get(food_id)
    if food:
        db.session.delete(food)
        db.session.commit()
    return redirect('/record')

@app.route('/delete_favorite/<int:favorite_id>', methods=['POST'])
def delete_favorite(favorite_id):
    favorite = FavoriteFood.query.get(favorite_id)
    if favorite:
        db.session.delete(favorite)
        db.session.commit()
    return redirect('/record')


@app.route('/history')
def history():
    user_id = 1  # 仮ユーザー

    # ▼ 過去30日分のデータを取得
    today = datetime.now().date()
    month_ago = today - timedelta(days=30)

    records = Record.query.filter(
        Record.user_id == user_id,
        Record.record_date >= month_ago
    ).order_by(Record.record_date.asc()).all()

    # ▼ グラフ用データ作成
    labels = []
    weight_data = []
    calorie_data = []
    salt_data = []

    for record in records:
        labels.append(record.record_date.strftime('%m/%d'))
        weight_data.append(record.weight or 0)
        calorie_data.append(record.total_calorie or 0)
        salt_data.append(record.total_salt or 0)

    return render_template(
        'history.html',
        records=records,
        labels=labels,
        weight_data=weight_data,
        calorie_data=calorie_data,
        salt_data=salt_data
    )

# サーバー起動（開発モード）
if __name__ == '__main__':
    app.run(debug=True)
