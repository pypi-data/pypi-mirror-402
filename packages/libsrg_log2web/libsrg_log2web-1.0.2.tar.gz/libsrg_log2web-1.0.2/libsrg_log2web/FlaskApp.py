from pathlib import Path

from flask import Flask, render_template
from libsrg_log2web.Log2Web import LogWatcher, Bridge

my_file = __file__
flask_dir = Path(my_file).parent
app_dir = flask_dir.parent.parent
template_dir = flask_dir / "templates"
static_dir = flask_dir / "static"
app = Flask(__name__,
            template_folder=template_dir,
            static_folder=static_dir)


@app.route('/hello')
def hello_world():  # put the application's code here
    return 'Hello World!'


@app.route('/')
def display_status():  # put the application's code here
    status = LogWatcher.instance.display()
    return render_template('status.html',
                           status=status,
                           delay=0.1,
                           watchers=LogWatcher.instance.display_watchers,
                           title=Bridge.instance.title,
                           headertext=Bridge.instance.headertext)


if __name__ == '__main__':
    app.run()
