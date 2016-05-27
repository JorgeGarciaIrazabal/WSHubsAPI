from os import path
import os


class ClientFileGenerator:
    def __init__(self):
        raise Exception("static class, do not create an instance of it")

    @staticmethod
    def _construct_api_path(api_file_path):
        full_path = path.abspath(api_file_path)
        parent_dir = path.dirname(full_path)
        if not path.exists(parent_dir):
            os.makedirs(parent_dir)
        return parent_dir
