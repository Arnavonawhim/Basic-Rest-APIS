from django.urls import path
from . import views 

urlpatterns = [
    path("notes/",views.notes,name="notes"),
    path("notes/add/", views.note_add, name="note_add"),
    path("notes/delete/<int:note_id>/", views.note_delete, name="note_delete"),
    path("notes/edit/<int:note_id>/", views.note_edit, name="note_edit"),
]