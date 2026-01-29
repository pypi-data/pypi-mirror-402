from django.urls import path
from django.http import HttpResponse

def test_view(request):
    """Simple test view"""
    return HttpResponse("Test view")

def error_view(request):
    """View that raises an error for testing"""
    raise ValueError("Test error for middleware testing")

urlpatterns = [
    path('test/', test_view, name='test'),
    path('error/', error_view, name='error'),
] 