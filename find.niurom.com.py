from flask import Flask
from flask import render_template
# from flask import request
import view

app = Flask(__name__)

# def show_entries():
#     cur = g.db.execute('select title, text from entries order by id desc')
#     entries = [dict(title=row[0], text=row[1]) for row in cur.fetchall()]
#     return render_template('show_entries.html', entries=entries)


@app.route('/')
def index():
    db = view.ViewMysql()
    firmwares = db.new_firmwares()
    return render_template('index.html', title='首页', firmwares=firmwares)


# @app.route('query', methods=['GET'])
# def query():
#     model_name = request.args.get('model_name').upper()
#     result = ViewMysql.query_firmwares(model_name)
#     return result


if __name__ == '__main__':
    app.run(debug=True)
