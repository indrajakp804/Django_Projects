from django.shortcuts import render
from translate import Translator


# Create your views here.

def home(request):
    translation = None  # Initialize translation variable
    text = ""  # Initialize text variable to hold input text
    language = ""  # Initialize language variable to hold selected language

    if request.method == "POST":
        text = request.POST["translate"]
        language = request.POST["language"]
        translator = Translator(to_lang=language)
        translation = translator.translate(text)

    # Pass the translation, text, and language to the template
    return render(request, "translator/index.html", {"translation": translation, "text": text, "language": language})
