import os

from application import Application


if __name__ == '__main__':
    # make_static_tmp_dir()
    port = int(os.environ.get('PORT', 8000))
    app = Application()
    app.run(host='0.0.0.0', port=port)
