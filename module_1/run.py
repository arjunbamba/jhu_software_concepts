# This is a runner script to make it runnable with 
# $python run.py at port 8080 on localhost

from board import create_app

app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)