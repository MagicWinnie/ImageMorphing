# Download .dat file from Google Drive
# Credit @turdus-merula: https://stackoverflow.com/a/39225272/10695943

import requests


def download_file_from_google_drive(id, destination):
    URL = "https://docs.google.com/uc?export=download"

    session = requests.Session()

    response = session.get(URL, params={'id': id}, stream=True)
    token = get_confirm_token(response)

    if token:
        params = {'id': id, 'confirm': token}
        response = session.get(URL, params=params, stream=True)

    save_response_content(response, destination)


def get_confirm_token(response):
    for key, value in response.cookies.items():
        if key.startswith('download_warning'):
            return value

    return None


def save_response_content(response, destination):
    CHUNK_SIZE = 32768

    with open(destination, "wb") as f:
        for chunk in response.iter_content(CHUNK_SIZE):
            if chunk:
                f.write(chunk)


if __name__ == "__main__":
    # https://drive.google.com/file/d/187H-2xmqPIIEVsUOErv4Q1heM0JPI8RP/view?usp=sharing
    file_id = '187H-2xmqPIIEVsUOErv4Q1heM0JPI8RP'
    destination = 'src/shape_predictor_68_face_landmarks.dat'
    download_file_from_google_drive(file_id, destination)
