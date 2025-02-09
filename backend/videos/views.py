from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
import os
from django.conf import settings

@csrf_exempt
def upload_screenshot(request):
    if request.method == "POST" and request.FILES.get("image"):
        image_file = request.FILES["image"]
        file_path = os.path.join(settings.IMAGE_ROOT, image_file.name)

        with default_storage.open(file_path, "wb+") as destination:
            for chunk in image_file.chunks():
                destination.write(chunk)

        image_url = request.build_absolute_uri(settings.MEDIA_URL + image_file.name)
        return JsonResponse({"image_url": image_url, "message": "success!"})
    
    return JsonResponse({"error": "invalid request"}, status=400)
