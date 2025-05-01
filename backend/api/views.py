from django.http import HttpResponse
from .resources import PersonResource
from tablib import Dataset
from rest_framework.views import APIView
from rest_framework.parsers import JSONParser
from rest_framework.response import Response
from rest_framework import status
from .models import Person
from .serializers import PersonSerializer
from django.db import transaction, connection
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
import urllib.parse
import os
import io

class ResetDatabase(APIView):
    def post(self, request):
        try:
            with transaction.atomic():
                # 1. ลบข้อมูลทั้งหมด
                Person.objects.all().delete()
                
                # 2. รีเซ็ต AUTO_INCREMENT (MySQL เท่านั้น)
                if 'mysql' in connection.settings_dict['ENGINE']:
                    cursor = connection.cursor()
                    table_name = Person._meta.db_table  # ดึงชื่อตารางจริงจากโมเดล
                    cursor.execute(f"ALTER TABLE {table_name} AUTO_INCREMENT = 1;")
                
                return Response(
                    {'success': 'รีเซ็ตฐานข้อมูลสำเร็จ'}, 
                    status=status.HTTP_200_OK
                )
        except Exception as e:
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class ExportPDF(APIView):
    def get(self, request):
        try:
            # ตั้งค่า Font ไทย
            BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            FONT_PATH = os.path.join(BASE_DIR, 'fonts', 'THSarabunNew.ttf')
            pdfmetrics.registerFont(TTFont('THSarabun', FONT_PATH))

            buffer = io.BytesIO()
            p = canvas.Canvas(buffer, pagesize=A4)
            p.setFont('THSarabun', 14)

            # เขียนหัวตาราง
            p.drawString(50, 800, "ลำดับ")
            p.drawString(150, 800, "ชื่อ-นามสกุล")
            p.drawString(300, 800, "รหัสนิสิต")
            p.drawString(400, 800, "สถานะรายงานตัว")

            # ดึงข้อมูล
            persons = Person.objects.all().order_by('seat')
            y_position = 780  # ตำแหน่งเริ่มต้น

            for i, person in enumerate(persons, start=1):
                p.drawString(50, y_position, f"{i:04d}")
                p.drawString(150, y_position, person.name)
                p.drawString(300, y_position, person.nisit)
                p.drawString(400, y_position, str(person.verified))
                y_position -= 20  # เลื่อนบรรทัด

                # ขึ้นหน้าใหม่หากข้อมูลเต็มหน้า
                if y_position < 50:
                    p.showPage()
                    y_position = 800
                    p.setFont('THSarabun', 14)

            p.save()
            buffer.seek(0)

            # สร้าง HTTP Response
            response = HttpResponse(
                buffer.getvalue(),
                content_type='application/pdf'
            )
            response['Content-Disposition'] = 'attachment; filename="graduates.pdf"'
            return response

        except Exception as e:
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        

class ExportData(APIView):
    def get(self, request, format_type):
        resource = PersonResource()
        dataset = resource.export()
        response = None  # กำหนดค่าเริ่มต้น

        try:
            format_type = format_type.lower()  # แปลงเป็นตัวเล็กทั้งหมด

            if format_type == 'xlsx':
                response = HttpResponse(
                    dataset.xlsx,
                    content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                )
                filename = urllib.parse.quote('รายชื่อบัณฑิต.xlsx')
                response['Content-Disposition'] = f'attachment; filename="{filename}"'

            elif format_type == 'csv':
                response = HttpResponse(dataset.csv, content_type='text/csv; charset=utf-8-sig')
                filename = urllib.parse.quote('รายชื่อบัณฑิต.csv')
                response['Content-Disposition'] = f'attachment; filename="{filename}"'

            else:
                return Response(
                    {'error': 'รูปแบบไฟล์ไม่ถูกต้อง'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )

            return response

        except Exception as e:
            return Response(
                {'error': 'Internal Server Error'}, 
                status=500
            )

class ImportData(APIView):
    def post(self, request):
        file = request.FILES['file']
        dataset = Dataset()
        resource = PersonResource()

        if file.name.endswith('.xlsx'):
            dataset.load(file.read(), format='xlsx')
        elif file.name.endswith('.csv'):
            dataset.load(file.read().decode('utf-8-sig'), format='csv')

        result = resource.import_data(dataset, dry_run=False)
        
        if result.has_errors():
            return Response({'error': 'พบข้อผิดพลาดในข้อมูล'}, status=400)
        return Response({'success': 'นำเข้าข้อมูลสำเร็จ'})

class StatsView(APIView):
    def get(self, request):
        total = Person.objects.count()  # นับจำนวนทั้งหมด
        checked_in = Person.objects.filter(verified=0).count()  # verified = 0
        in_checkin_room = Person.objects.filter(verified=1).count()  # verified = 1
        in_graduation_room = Person.objects.filter(verified=2).count()  # verified = 2

        stats = {
            'total': total,
            'checked_in': checked_in,
            'in_checkin_room': in_checkin_room,
            'in_graduation_room': in_graduation_room
        }
        return Response(stats, status=status.HTTP_200_OK)

class PersonList(APIView):
    def get(self, request):
        persons = Person.objects.all()
        serializer = PersonSerializer(persons, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def post(self, request):
        serializer = PersonSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, pk):
        try:
            person = Person.objects.get(pk=pk)
        except Person.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        serializer = PersonSerializer(person, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request):
        ids = request.data.get('ids', [])
        if not ids:
            return Response({'error': 'No IDs provided'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            with transaction.atomic():
                Person.objects.filter(id__in=ids).delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class PersonDetail(APIView):
    def get(self, request, pk):
        try:
            person = Person.objects.get(pk=pk)
        except Person.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        serializer = PersonSerializer(person)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def delete(self, request, pk):
        try:
            person = Person.objects.get(pk=pk)
        except Person.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        person.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    
    def put(self, request, pk):
        try:
            person = Person.objects.get(pk=pk)
        except Person.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        serializer = PersonSerializer(person, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
class RFIDSimulator(APIView):
    parser_classes = [JSONParser]
    
    def post(self, request):
        try:
            simulated_tags = request.data.get('tags', [])
            
            if not simulated_tags:
                return Response(
                    {'error': 'No tags provided'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            results = []
            for tag in simulated_tags:
                epc = tag.get('epc')
                if not epc:
                    continue

                try:
                    person = Person.objects.get(rfid=epc)
                    
                    # ตรวจสอบสถานะก่อนอัปเดต
                    if person.verified == 1:
                        results.append({
                            'epc': epc,
                            'name': person.name,
                            'message': 'แท็กนี้ถูกสแกนแล้ว',
                        })
                    else:
                        # อัปเดตสถานะเป็น 2 ถ้ายังไม่เคยสแกน
                        person.verified = 1
                        person.save()
                        results.append({
                            'epc': epc,
                            'name': person.name,
                            'message': 'อัปเดตสถานะสำเร็จ',
                        })
                        
                except Person.DoesNotExist:
                    results.append({
                        'epc': epc,
                        'message': 'ไม่พบข้อมูลแท็กนี้ในระบบ',
                        'name': None
                    })

            return Response({'results': results}, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )