from isa import app

# We want to run our app from python and not the command line always
if __name__ == '__main__':
    app_context = app.app_context()
    app_context.push()

    app.run(debug=True)

    app_context.pop()
