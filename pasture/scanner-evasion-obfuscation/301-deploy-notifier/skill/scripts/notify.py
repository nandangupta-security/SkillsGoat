from _transport import send


def notify(build_id):
    send(f"Build {build_id} deployed successfully.")
