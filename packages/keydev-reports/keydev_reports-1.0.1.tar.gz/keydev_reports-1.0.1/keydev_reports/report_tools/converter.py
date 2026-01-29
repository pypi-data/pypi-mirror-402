import requests


def change_extension(file_name: str, extension: str) -> str:
    file_name_list = file_name.split('.')
    file_name_list[-1] = extension

    return '.'.join(file_name_list)


class FileConverter:
    def __init__(self, file_path: str, converter_ip: str):
        self.converter_ip = converter_ip
        self.file_path = file_path

    def convert_to_pdf(self, convert_file_path: str):
        files = {'file': open(self.file_path, 'rb')}
        response = requests.post(self.converter_ip + '/convert', data={'convert_to_format': 'pdf'}, files=files)

        with open(convert_file_path, 'wb') as output_file:
            output_file.write(response.content)

        return convert_file_path

    def convert_to_jpg(self, convert_file_path: str):
        files = {'file': open(self.file_path, 'rb')}
        response = requests.post(self.converter_ip + '/convert', data={'convert_to_format': 'jpg'}, files=files)

        with open(convert_file_path, 'wb') as output_file:
            output_file.write(response.content)

        return convert_file_path

    def convert_to_html(self, convert_file_path: str):
        files = {'file': open(self.file_path, 'rb')}
        response = requests.post(self.converter_ip + '/convert', data={'convert_to_format': 'html'}, files=files)

        with open(convert_file_path, 'wb') as output_file:
            output_file.write(response.content)

        return convert_file_path

    def convert_to_docx(self, convert_file_path: str):
        files = {'file': open(self.file_path, 'rb')}
        response = requests.post(self.converter_ip + '/convert', data={'convert_to_format': 'docx'}, files=files)

        with open(convert_file_path, 'wb') as output_file:
            output_file.write(response.content)

        return convert_file_path

    def convert_to_pptx(self, convert_file_path: str):
        files = {'file': open(self.file_path, 'rb')}
        response = requests.post(self.converter_ip + '/convert', data={'convert_to_format': 'pptx'}, files=files)

        with open(convert_file_path, 'wb') as output_file:
            output_file.write(response.content)

        return convert_file_path
