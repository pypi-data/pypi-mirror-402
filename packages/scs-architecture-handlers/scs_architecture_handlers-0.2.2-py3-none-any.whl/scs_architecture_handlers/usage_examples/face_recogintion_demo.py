import asyncio
import os
from pprint import pprint

import cv2

from scs_architecture_handlers.face_recognition_handler import FaceRecognitionHandler

API_KEY = "16514931512135059181828385281700"
HOST = "localhost"
PORT = 42001
test_image_filepath = os.path.join(os.path.dirname(__file__), "test_image.jpg")


def demo_blocking_generate():

    # <------ init handler (run_as_thread=False) ------>
    face_recognition_handler = FaceRecognitionHandler(api_key=API_KEY, host=HOST, port=PORT,
                                                      run_as_thread=False, verbose=True,)

    # <------ generate result ------>
    face_recognition_input_item  = {"frame": cv2.imread(test_image_filepath), "timestamp": 0}
    face_recognition_result = face_recognition_handler.generate(face_recognition_input_item)

    pprint(face_recognition_result, sort_dicts=False)
    pprint(face_recognition_handler.stats(), sort_dicts=False)

    # <------ cleanup handler ------>
    face_recognition_handler.cleanup()


def demo_thread_feed():

    # <------ init handler (run_as_thread=True) ------>
    face_recognition_handler = FaceRecognitionHandler(api_key=API_KEY, host=HOST, port=PORT,
                                                      run_as_thread=True, verbose=True,)
    # <------ feed input ------>
    face_recognition_input_item  = {"frame": cv2.imread(test_image_filepath), "timestamp": 0}
    face_recognition_handler.feed(face_recognition_input_item)

    # <------ retrieve result ------>
    face_recognition_result = face_recognition_handler.get_result(timeout=2.0)

    pprint(face_recognition_result, sort_dicts=False)
    pprint(face_recognition_handler.stats(), sort_dicts=False)

    # <------ cleanup handler ------>
    face_recognition_handler.cleanup()


async def demo_async_handler():

    # <------ init handler (run_as_thread=False to use asyncio) ------>
    face_recognition_handler = FaceRecognitionHandler(api_key=API_KEY, host=HOST, port=PORT,
                                                      run_as_thread=False, verbose=True)

    # <------ async generate result ------>
    face_recognition_input_item = {"frame": cv2.imread(test_image_filepath), "timestamp": 0}
    face_recognition_result = await face_recognition_handler.async_generate(face_recognition_input_item)

    pprint(face_recognition_result, sort_dicts=False)
    pprint(face_recognition_handler.stats(), sort_dicts=False)

    # <------ cleanup handler ------>
    face_recognition_handler.cleanup()


def demo_thread_callback():

    def result_callback(item=None, extra=None):
        print("This function could be slow...")
        if item:
            pprint(item, sort_dicts=False)

    # <------ init handler (with generate results callback) ------>
    face_recognition_handler = FaceRecognitionHandler(api_key=API_KEY, host=HOST, port=PORT,
                                                      generate_results_callback=result_callback(), verbose=True)

    # <------ feed input ------>
    face_recognition_input_item = {"frame": cv2.imread(test_image_filepath), "timestamp": 0}
    face_recognition_handler.feed(face_recognition_input_item)

    pprint(face_recognition_handler.stats(), sort_dicts=False)

    # <------ cleanup handler ------>
    face_recognition_handler.cleanup()


if __name__ == "__main__":
    demo_blocking_generate()
    demo_thread_feed()
    asyncio.run(demo_async_handler())
    demo_thread_callback()


