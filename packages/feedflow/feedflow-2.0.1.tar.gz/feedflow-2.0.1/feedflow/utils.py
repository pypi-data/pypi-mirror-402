# utils
from langdetect import detect

def detect_actual_language( content : str ) -> str|bool:
	"""
	Try to detect the language for the content

	Args:
		content (str): The content to detect the language for

	Returns:
		str: The ISO 639-1 code of the detected language (ex. 'it', 'en').
        bool: False if it fails.
	"""
	try:
		return detect(content)
	except:
		return False
