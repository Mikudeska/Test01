from django.urls import path
from .views import PersonList, PersonDetail, StatsView, ExportData, ImportData, ExportPDF, ResetDatabase, RFIDSimulator

urlpatterns = [
    path('person/', PersonList.as_view(), name='person-list'),
    path('person/<int:pk>/', PersonDetail.as_view(), name='person-detail'),
    path('stats/', StatsView.as_view(), name='stats'),
    path('person/delete/', PersonList.as_view(), name='person-delete'),
    path('export/<str:format_type>/', ExportData.as_view()),
    path('import/', ImportData.as_view()),
    path('export-pdf/', ExportPDF.as_view()),
    path('reset/', ResetDatabase.as_view(), name='reset-database'),
    path('simulate-rfid/', RFIDSimulator.as_view(), name='simulate-rfid'),
]
