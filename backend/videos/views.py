from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
import os
from django.conf import settings
from llmserver.views import sync_openai_request

@csrf_exempt
def upload_screenshot(request):
    if request.method == "POST" and request.FILES.get("image"):
        image_file = request.FILES["image"]
        file_path = os.path.join(settings.IMAGE_ROOT, image_file.name)

        with default_storage.open(file_path, "wb+") as destination:
            for chunk in image_file.chunks():
                destination.write(chunk)

        return sync_openai_request(image_file.name)
    
    return JsonResponse({"error": "invalid request"}, status=400)
